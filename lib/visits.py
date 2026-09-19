"""Visitor counting.

Each browser session is counted once. Counts are buffered in the Streamlit
process and flushed to the content branch in batches, so a busy day produces a
handful of commits rather than one per visitor.
"""
from __future__ import annotations

import threading
from datetime import date, timedelta

import streamlit as st

from . import store

FLUSH_EVERY = 3          # pending visits before writing
FLUSH_SECONDS = 600      # or after this long


@st.cache_resource(show_spinner=False)
def _buffer():
    return {"pending": 0, "last_flush": 0.0, "lock": threading.Lock()}


def _blank():
    return {"total": 0, "daily": {}}


def record_visit():
    """Count this browser session once, flushing to storage now and then."""
    if st.session_state.get("_visit_counted"):
        return
    st.session_state["_visit_counted"] = True

    import time
    buf = _buffer()
    with buf["lock"]:
        buf["pending"] += 1
        due = (buf["pending"] >= FLUSH_EVERY
               or (time.time() - buf["last_flush"]) > FLUSH_SECONDS)
        if not due:
            return
        pending = buf["pending"]
        buf["pending"] = 0
        buf["last_flush"] = time.time()
    _flush(pending)


def _flush(count):
    if count <= 0:
        return
    try:
        store.refresh("visits")
        data = store.load("visits", _blank())
        if not isinstance(data, dict):
            data = _blank()
        today = date.today().isoformat()
        data["total"] = int(data.get("total", 0)) + count
        daily = data.setdefault("daily", {})
        daily[today] = int(daily.get(today, 0)) + count
        # keep a rolling year
        cutoff = (date.today() - timedelta(days=365)).isoformat()
        data["daily"] = {k: v for k, v in daily.items() if k >= cutoff}
        store.save("visits", data, f"record {count} visit(s)")
    except Exception as exc:
        store.note_error(exc)


def flush_now():
    """Write out anything buffered — called when the admin opens the dashboard."""
    buf = _buffer()
    with buf["lock"]:
        pending = buf["pending"]
        buf["pending"] = 0
    if pending:
        _flush(pending)


def stats():
    flush_now()
    data = store.load("visits", _blank())
    if not isinstance(data, dict):
        data = _blank()
    daily = data.get("daily", {}) or {}
    today = date.today()
    last7 = sum(int(daily.get((today - timedelta(days=i)).isoformat(), 0)) for i in range(7))
    last30 = sum(int(daily.get((today - timedelta(days=i)).isoformat(), 0)) for i in range(30))
    series = [
        {"Date": (today - timedelta(days=i)).isoformat(),
         "Visits": int(daily.get((today - timedelta(days=i)).isoformat(), 0))}
        for i in range(29, -1, -1)
    ]
    return {
        "total": int(data.get("total", 0)),
        "today": int(daily.get(today.isoformat(), 0)),
        "last7": last7,
        "last30": last30,
        "series": series,
    }
