"""Student portal."""
from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from lib import auth, store
from lib.ui import esc, kpi, pill, section
from views.public import _embed_video, _nice_date


def login_panel(site):
    section("Student portal", "Sign in",
            "Use the email or phone number you registered with.")
    col1, col2 = st.columns([2, 3])
    with col1:
        with st.form("student_login"):
            ident = st.text_input("Email or phone")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", width="stretch"):
                stu = auth.student_login(ident, pw)
                if stu:
                    auth.login_as(stu, "student")
                    st.rerun()
                else:
                    st.error("Wrong credentials, or your registration is not approved yet.")
        st.caption("Registered but can't log in? Your account is activated once the "
                   "admin approves your registration.")
    with col2:
        st.markdown(
            """<div class="card"><h4>What's inside</h4>
<p style="line-height:2">• Your batch, timings and level<br>
• Attendance record and percentage<br>
• Fee status and payment history<br>
• Practice videos for your level<br>
• Announcements from the guru</p></div>""",
            unsafe_allow_html=True)


def portal(site):
    stu = auth.current_user()
    # refresh from store so admin changes show up
    latest = store.get("students", stu.get("id")) or stu
    st.session_state["auth_user"] = latest
    stu = latest

    batch = store.get("batches", stu.get("batch_id")) or {}
    att = [a for a in store.load("attendance", []) if a.get("student_id") == stu.get("id")]
    fees = [f for f in store.load("fees", []) if f.get("student_id") == stu.get("id")]

    present = sum(1 for a in att if a.get("status") == "present")
    pct = round(100 * present / len(att)) if att else 0
    due = sum(float(f.get("amount", 0) or 0) for f in fees if f.get("status") != "paid")

    section("Namaskaram", stu.get("name", "Student"),
            f"{batch.get('name','—')} · {batch.get('days','')} {batch.get('time','')}")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi(f"{pct}%", "Attendance")
    with c2: kpi(f"{present}/{len(att)}", "Classes attended")
    with c3: kpi(f"₹{int(due)}", "Fees due")
    with c4: kpi(esc(stu.get("level") or batch.get("level") or "—"), "Level")

    tabs = st.tabs(["Announcements", "My classes", "Attendance", "Fees", "Practice videos", "My profile"])

    # ---- announcements
    with tabs[0]:
        rows = store.load("announcements", [])
        rows = [a for a in rows if a.get("audience") in ("all", "students")
                or a.get("audience") == stu.get("batch_id")]
        rows.sort(key=lambda a: (not a.get("pinned"), str(a.get("created_at", ""))), reverse=False)
        if not rows:
            st.info("No announcements right now.")
        for a in rows:
            st.markdown(
                f"""<div class="card" style="margin-bottom:.8rem">
<h4>{'📌 ' if a.get('pinned') else ''}{esc(a.get('title'))}</h4>
<p>{esc(a.get('body'))}</p>
<p style="margin-top:.6rem;font-size:.78rem;color:#a4979b">{esc(str(a.get('created_at',''))[:10])}</p></div>""",
                unsafe_allow_html=True)

    # ---- classes
    with tabs[1]:
        if batch:
            st.markdown(
                f"""<div class="batch"><span class="lvl">{esc(batch.get('level'))}</span>
<h4 style="margin-top:.45rem">{esc(batch.get('name'))}</h4>
<p style="color:#6d5f63;margin:.3rem 0 0">{esc(batch.get('description'))}</p>
<div class="meta"><span>🗓 {esc(batch.get('days'))}</span><span>⏰ {esc(batch.get('time'))}</span>
<span>📍 {esc(batch.get('mode'))}</span><span>💰 ₹{esc(batch.get('fee_monthly'))}/month</span></div></div>""",
                unsafe_allow_html=True)
        else:
            st.info("You have not been assigned to a batch yet.")
        if stu.get("notes_for_student"):
            st.markdown(f'<div class="note">{esc(stu["notes_for_student"])}</div>', unsafe_allow_html=True)

    # ---- attendance
    with tabs[2]:
        if not att:
            st.info("No attendance recorded yet.")
        else:
            att_sorted = sorted(att, key=lambda a: str(a.get("date", "")), reverse=True)
            st.dataframe(
                [{"Date": a.get("date"), "Status": str(a.get("status", "")).title(),
                  "Note": a.get("note", "")} for a in att_sorted],
                width="stretch", hide_index=True)
            st.progress(min(pct, 100) / 100, text=f"Attendance {pct}%")

    # ---- fees
    with tabs[3]:
        if not fees:
            st.info("No fee records yet.")
        else:
            rows = sorted(fees, key=lambda f: str(f.get("period", "")), reverse=True)
            st.dataframe(
                [{"Period": f.get("period"), "Amount (₹)": f.get("amount"),
                  "Status": str(f.get("status", "")).title(),
                  "Paid on": f.get("paid_on", ""), "Method": f.get("method", ""),
                  "Note": f.get("note", "")} for f in rows],
                width="stretch", hide_index=True)
            if due > 0:
                st.markdown(f'<div class="note">Outstanding balance: <b>₹{int(due)}</b>. '
                            'Please settle it with the office or over UPI.</div>',
                            unsafe_allow_html=True)
            else:
                st.success("All fees are up to date. Thank you!")

    # ---- videos
    with tabs[4]:
        vids = store.load("videos", [])
        mine = [v for v in vids
                if v.get("public")
                or (v.get("batch_id") and v.get("batch_id") == stu.get("batch_id"))
                or (v.get("level") and v.get("level") == (stu.get("level") or batch.get("level")))
                or (not v.get("batch_id") and not v.get("level"))]
        if not mine:
            st.info("No practice videos for your batch yet.")
        for v in mine:
            st.markdown(f"**{esc(v.get('title'))}**  \n{esc(v.get('description'))}")
            _embed_video(v.get("url"))
            st.markdown("---")

    # ---- profile
    with tabs[5]:
        st.markdown(
            f"""<div class="card"><h4>{esc(stu.get('name'))}</h4>
<p style="line-height:2">Student code: <b>{esc(stu.get('student_code'))}</b><br>
Email: {esc(stu.get('email'))}<br>Phone: {esc(stu.get('phone'))}<br>
Guardian: {esc(stu.get('guardian') or '—')}<br>
Joined: {esc(str(stu.get('joined_on') or stu.get('created_at',''))[:10])}</p></div>""",
            unsafe_allow_html=True)
        with st.expander("Change my password"):
            with st.form("stu_pw"):
                old = st.text_input("Current password", type="password")
                n1 = st.text_input("New password", type="password")
                n2 = st.text_input("Confirm new password", type="password")
                if st.form_submit_button("Update password"):
                    if not auth.verify_password(old, stu.get("password", "")):
                        st.error("Current password is wrong.")
                    elif len(n1) < 6:
                        st.error("New password must be at least 6 characters.")
                    elif n1 != n2:
                        st.error("Passwords do not match.")
                    else:
                        store.update("students", stu["id"],
                                     {"password": auth.hash_password(n1)},
                                     "student password change")
                        st.success("Password updated.")
