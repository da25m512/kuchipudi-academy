"""Authentication.

The admin password lives only in Streamlit secrets — it is never stored in the
repository and there is no default. Student passwords are PBKDF2-SHA256 hashes
kept with the student record on the content branch.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets as pysecrets
import time

import streamlit as st

from . import store

ITERATIONS = 120_000
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
SESSION_SECONDS = 8 * 60 * 60


# --------------------------------------------------------------------------- #
# password hashing (students)
# --------------------------------------------------------------------------- #
def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or pysecrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"pbkdf2${ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        scheme, iters, salt, digest = stored.split("$")
        if scheme != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), digest)
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# admin
# --------------------------------------------------------------------------- #
def admin_password_configured() -> bool:
    return bool(_admin_password())


def _admin_password():
    return store._secret("admin_password") or store._secret("admin", "password")


def lockout_remaining() -> int:
    until = st.session_state.get("_admin_lock_until", 0)
    return max(0, int(until - time.time()))


def admin_login(password: str):
    """Return True on success. Constant-time compare, with lockout on repeats."""
    if lockout_remaining() > 0:
        return False
    expected = _admin_password()
    if not expected:
        return False
    ok = hmac.compare_digest(str(password), str(expected))
    if ok:
        st.session_state["_admin_attempts"] = 0
        return True
    tries = st.session_state.get("_admin_attempts", 0) + 1
    st.session_state["_admin_attempts"] = tries
    if tries >= MAX_ATTEMPTS:
        st.session_state["_admin_lock_until"] = time.time() + LOCKOUT_SECONDS
        st.session_state["_admin_attempts"] = 0
    return False


# --------------------------------------------------------------------------- #
# students
# --------------------------------------------------------------------------- #
def student_login(identifier: str, password: str):
    ident = (identifier or "").strip().lower()
    if not ident:
        return None
    for stu in store.load("students", []):
        if stu.get("status") != "active":
            continue
        candidates = {
            str(stu.get("email", "")).lower(),
            str(stu.get("phone", "")).lower(),
            str(stu.get("student_code", "")).lower(),
        }
        if ident in candidates and verify_password(password, stu.get("password", "")):
            return stu
    return None


# --------------------------------------------------------------------------- #
# session
# --------------------------------------------------------------------------- #
def login_as(user, role):
    st.session_state["auth_user"] = user
    st.session_state["auth_role"] = role
    st.session_state["auth_started"] = time.time()


def _expired() -> bool:
    started = st.session_state.get("auth_started")
    return bool(started) and (time.time() - started) > SESSION_SECONDS


def current_user():
    if _expired():
        logout()
        return None
    return st.session_state.get("auth_user")


def logout():
    for key in ("auth_user", "auth_role", "auth_started"):
        st.session_state.pop(key, None)
    store.refresh()


def role():
    if _expired():
        logout()
        return None
    return st.session_state.get("auth_role")


def is_admin():
    return role() == "admin"


def is_student():
    return role() == "student"
