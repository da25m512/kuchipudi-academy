"""Password hashing and session handling for admin and student logins."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

import streamlit as st

from . import store

ITERATIONS = 120_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
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
DEFAULT_ADMIN = {"username": "admin", "password": "kuchipudi@2026"}


def admin_users():
    users = store.load("users", [])
    if not users:
        users = [{
            "id": "user_admin",
            "username": DEFAULT_ADMIN["username"],
            "name": "Administrator",
            "role": "admin",
            "password": hash_password(DEFAULT_ADMIN["password"]),
            "must_change": True,
            "created_at": store.now_iso(),
        }]
        store.save("users", users, "seed admin user")
    return users


def admin_login(username: str, password: str):
    # An ADMIN_PASSWORD env var / secret always works as a break-glass login.
    override = store._secret("admin", "password")
    if override and username.strip().lower() == "admin" and password == override:
        return {"id": "user_admin", "username": "admin", "name": "Administrator",
                "role": "admin", "must_change": False}
    for user in admin_users():
        if user.get("username", "").lower() == username.strip().lower():
            if verify_password(password, user.get("password", "")):
                return user
    return None


def set_admin_password(user_id: str, new_password: str):
    users = list(admin_users())
    for user in users:
        if user.get("id") == user_id:
            user["password"] = hash_password(new_password)
            user["must_change"] = False
            user["updated_at"] = store.now_iso()
    store.save("users", users, "change admin password")


# --------------------------------------------------------------------------- #
# students
# --------------------------------------------------------------------------- #
def student_login(identifier: str, password: str):
    ident = (identifier or "").strip().lower()
    for stu in store.load("students", []):
        if stu.get("status") != "active":
            continue
        candidates = {
            str(stu.get("email", "")).lower(),
            str(stu.get("phone", "")).lower(),
            str(stu.get("student_code", "")).lower(),
        }
        if ident in candidates and ident:
            if verify_password(password, stu.get("password", "")):
                return stu
    return None


# --------------------------------------------------------------------------- #
# session
# --------------------------------------------------------------------------- #
def current_user():
    return st.session_state.get("auth_user")


def login_as(user, role):
    st.session_state["auth_user"] = user
    st.session_state["auth_role"] = role


def logout():
    for key in ("auth_user", "auth_role"):
        st.session_state.pop(key, None)
    store.refresh()


def role():
    return st.session_state.get("auth_role")


def is_admin():
    return role() == "admin"


def is_student():
    return role() == "student"
