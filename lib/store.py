"""JSON data store backed by a separate GitHub branch.

Content lives on its own branch (default ``content``) inside the same private
repository. Two reasons that matters:

* Streamlit Community Cloud watches the branch it deployed from (``main``), so
  writing data to a different branch never reboots the live app.
* Deleting that one branch removes every student record, fee, photo and setting
  in a single action, leaving the code untouched.

Without GitHub secrets configured the app falls back to a local ``local_content``
folder so it can be run offline. That folder is temporary; only the GitHub
backend stores anything permanently.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import uuid
from datetime import datetime, timezone

import requests
import streamlit as st

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DIR = os.path.join(ROOT, "local_content", "data")
_LOCK = threading.Lock()

TABLES = [
    "site", "students", "batches", "attendance", "fees", "videos",
    "gallery", "events", "testimonials", "enquiries", "announcements",
    "registrations", "visits",
]


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
def _secret(*path, default=None):
    """Read a secret by path, e.g. _secret('github','token') or _secret('admin_password')."""
    try:
        node = st.secrets
        for key in path:
            node = node[key]
        if node not in (None, ""):
            return node
    except Exception:
        pass
    env = "_".join(p.upper() for p in path)
    return os.environ.get(env, default)


def gh_config():
    """Return dict(token, owner, repo, branch) when GitHub storage is configured."""
    token = _secret("github", "token")
    owner = _secret("github", "owner")
    repo = _secret("github", "repo")
    branch = _secret("github", "branch", default="content") or "content"
    if not token or not repo:
        return None
    repo = str(repo).strip("/")
    if "/" in repo:                      # accept "owner/name" in the repo field
        owner, repo = repo.split("/", 1)
    if not owner:
        return None
    return {"token": token, "owner": owner, "repo": repo, "branch": branch}


def storage_mode() -> str:
    return "github" if gh_config() else "local"


def storage_label() -> str:
    cfg = gh_config()
    if not cfg:
        return "local files (temporary — set GitHub secrets to store permanently)"
    return f"{cfg['owner']}/{cfg['repo']} · branch `{cfg['branch']}`"


def _headers(cfg):
    return {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# --------------------------------------------------------------------------- #
# branch bootstrap
# --------------------------------------------------------------------------- #
def _ensure_branch(cfg):
    """Create the content branch off the repo's default branch if it is missing."""
    if st.session_state.get("_branch_ready"):
        return True
    base = f"{API}/repos/{cfg['owner']}/{cfg['repo']}"
    r = requests.get(f"{base}/branches/{cfg['branch']}", headers=_headers(cfg), timeout=20)
    if r.status_code == 200:
        st.session_state["_branch_ready"] = True
        return True
    if r.status_code != 404:
        r.raise_for_status()

    repo_info = requests.get(base, headers=_headers(cfg), timeout=20)
    repo_info.raise_for_status()
    default_branch = repo_info.json().get("default_branch", "main")
    head = requests.get(f"{base}/git/ref/heads/{default_branch}",
                        headers=_headers(cfg), timeout=20)
    head.raise_for_status()
    sha = head.json()["object"]["sha"]
    made = requests.post(f"{base}/git/refs", headers=_headers(cfg), timeout=25,
                         json={"ref": f"refs/heads/{cfg['branch']}", "sha": sha})
    if made.status_code not in (200, 201) and "already exists" not in made.text:
        raise RuntimeError(f"could not create branch '{cfg['branch']}': {made.text[:200]}")
    st.session_state["_branch_ready"] = True
    return True


# --------------------------------------------------------------------------- #
# low level read / write
# --------------------------------------------------------------------------- #
def _gh_read(cfg, table):
    url = f"{API}/repos/{cfg['owner']}/{cfg['repo']}/contents/data/{table}.json"
    r = requests.get(url, headers=_headers(cfg), params={"ref": cfg["branch"]}, timeout=20)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    body = r.json()
    raw = base64.b64decode(body["content"]).decode("utf-8")
    return json.loads(raw or "null"), body["sha"]


def _gh_write(cfg, table, payload, sha, message):
    url = f"{API}/repos/{cfg['owner']}/{cfg['repo']}/contents/data/{table}.json"
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
    return st.session_state.setdefault("_store_cache", {})


def _shas():
    return st.session_state.setdefault("_store_shas", {})


def note_error(exc):
    st.session_state.setdefault("_store_errors", []).append(str(exc)[:400])


def load(table, default=None):
    cache = _cache()
    if table in cache:
        return cache[table]

    cfg = gh_config()
    data = None
    if cfg:
        try:
            _ensure_branch(cfg)
            data, sha = _gh_read(cfg, table)
            _shas()[table] = sha
        except Exception as exc:
            note_error(exc)
            data = _local_read(table)
    else:
        data = _local_read(table)

    if data is None:
        data = default if default is not None else []
        try:
            save(table, data, f"seed {table}.json")
            return _cache()[table]
        except Exception as exc:
            note_error(exc)
    cache[table] = data
    return data


def save(table, payload, message=None):
    message = message or f"update {table}.json"
    cfg = gh_config()
    with _LOCK:
        if cfg:
            _ensure_branch(cfg)
            sha = _shas().get(table)
            if sha is None:
                try:
                    _, sha = _gh_read(cfg, table)
                except Exception:
                    sha = None
            try:
                new_sha = _gh_write(cfg, table, payload, sha, message)
            except RuntimeError:
                _, sha = _gh_read(cfg, table)          # stale sha -> refetch once
                new_sha = _gh_write(cfg, table, payload, sha, message)
            _shas()[table] = new_sha
        else:
            _local_write(table, payload)
        _cache()[table] = payload
    return payload


def refresh(table=None):
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
