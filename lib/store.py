"""GitHub-backed JSON data store.

Every table is a JSON file inside the repo's data/ directory. In production the
app reads and writes those files through the GitHub Contents API using a token
kept in Streamlit secrets, so all data lives in the private repo and survives
restarts. Locally (no token configured) it falls back to the files on disk.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

import requests
import streamlit as st

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DIR = os.path.join(ROOT, "data")
_LOCK = threading.Lock()

TABLES = [
    "site", "students", "batches", "attendance", "fees", "videos",
    "gallery", "events", "testimonials", "enquiries", "announcements",
    "registrations", "users",
]


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
def _secret(section: str, key: str, default=None):
    try:
        blob = st.secrets.get(section, {})
        if isinstance(blob, dict) or hasattr(blob, "get"):
            val = blob.get(key)
            if val:
                return val
    except Exception:
        pass
    return os.environ.get(f"{section.upper()}_{key.upper()}", default)


def gh_config():
    """Return dict(token, repo, branch) when GitHub storage is configured."""
    token = _secret("github", "token")
    repo = _secret("github", "repo")
    branch = _secret("github", "branch", "main") or "main"
    if token and repo:
        return {"token": token, "repo": repo.strip("/"), "branch": branch}
    return None


def storage_mode() -> str:
    return "github" if gh_config() else "local"


def _headers(cfg):
    return {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# --------------------------------------------------------------------------- #
# low level read / write
# --------------------------------------------------------------------------- #
def _gh_read(cfg, table):
    url = f"{API}/repos/{cfg['repo']}/contents/data/{table}.json"
    r = requests.get(url, headers=_headers(cfg),
                     params={"ref": cfg["branch"]}, timeout=20)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    body = r.json()
    raw = base64.b64decode(body["content"]).decode("utf-8")
    return json.loads(raw or "null"), body["sha"]


def _gh_write(cfg, table, payload, sha, message):
    url = f"{API}/repos/{cfg['repo']}/contents/data/{table}.json"
    content = base64.b64encode(
        json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    data = {"message": message, "content": content, "branch": cfg["branch"]}
    if sha:
        data["sha"] = sha
    r = requests.put(url, headers=_headers(cfg), json=data, timeout=25)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub write failed ({r.status_code}): {r.text[:300]}")
    return r.json()["content"]["sha"]


def _local_read(table):
    path = os.path.join(LOCAL_DIR, f"{table}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        txt = fh.read().strip()
    return json.loads(txt) if txt else None


def _local_write(table, payload):
    os.makedirs(LOCAL_DIR, exist_ok=True)
    path = os.path.join(LOCAL_DIR, f"{table}.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# cached public API
# --------------------------------------------------------------------------- #
def _cache():
    if "_store_cache" not in st.session_state:
        st.session_state["_store_cache"] = {}
    return st.session_state["_store_cache"]


def _shas():
    if "_store_shas" not in st.session_state:
        st.session_state["_store_shas"] = {}
    return st.session_state["_store_shas"]


def load(table, default=None):
    """Read a table, using the per-session cache when available."""
    cache = _cache()
    if table in cache:
        return cache[table]

    cfg = gh_config()
    data = None
    if cfg:
        try:
            data, sha = _gh_read(cfg, table)
            _shas()[table] = sha
        except Exception as exc:  # network / auth problem -> fall back to disk
            st.session_state.setdefault("_store_errors", []).append(str(exc))
            data = _local_read(table)
    else:
        data = _local_read(table)

    if data is None:
        data = default if default is not None else []
        # seed the table so it exists from here on
        try:
            save(table, data, f"seed {table}.json")
            return _cache()[table]
        except Exception:
            pass
    cache[table] = data
    return data


def save(table, payload, message=None):
    """Persist a table and refresh the cache."""
    message = message or f"update {table}.json"
    cfg = gh_config()
    with _LOCK:
        if cfg:
            sha = _shas().get(table)
            if sha is None:
                try:
                    _, sha = _gh_read(cfg, table)
                except Exception:
                    sha = None
            try:
                new_sha = _gh_write(cfg, table, payload, sha, message)
            except RuntimeError:
                # stale sha (someone else wrote) -> re-read and retry once
                _, sha = _gh_read(cfg, table)
                new_sha = _gh_write(cfg, table, payload, sha, message)
            _shas()[table] = new_sha
        else:
            _local_write(table, payload)
        _cache()[table] = payload
    return payload


def refresh(table=None):
    """Drop cached copies so the next read hits GitHub again."""
    if table:
        _cache().pop(table, None)
        _shas().pop(table, None)
    else:
        st.session_state["_store_cache"] = {}
        st.session_state["_store_shas"] = {}


# --------------------------------------------------------------------------- #
# record helpers
# --------------------------------------------------------------------------- #
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix="id"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def insert(table, record, prefix="rec", message=None):
    rows = list(load(table, []))
    record = dict(record)
    record.setdefault("id", new_id(prefix))
    record.setdefault("created_at", now_iso())
    rows.append(record)
    save(table, rows, message or f"add record to {table}")
    return record


def update(table, rec_id, changes, message=None):
    rows = list(load(table, []))
    hit = None
    for row in rows:
        if row.get("id") == rec_id:
            row.update(changes)
            row["updated_at"] = now_iso()
            hit = row
            break
    if hit:
        save(table, rows, message or f"update record in {table}")
    return hit


def delete(table, rec_id, message=None):
    rows = [r for r in load(table, []) if r.get("id") != rec_id]
    save(table, rows, message or f"delete record from {table}")


def get(table, rec_id):
    for row in load(table, []):
        if row.get("id") == rec_id:
            return row
    return None
