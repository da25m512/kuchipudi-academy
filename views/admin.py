"""Admin portal — full control over the site and the school."""
from __future__ import annotations

import io
import json
import csv
from datetime import date, datetime

import streamlit as st

from lib import auth, seed, store
from lib.ui import esc, kpi, pill, section
from views.public import _embed_video


# --------------------------------------------------------------------------- #
def login_panel(site):
    section("Admin", "Sign in to the admin portal")
    col1, col2 = st.columns([2, 3])
    with col1:
        with st.form("admin_login"):
            u = st.text_input("Username", value="")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", width="stretch"):
                user = auth.admin_login(u, p)
                if user:
                    auth.login_as(user, "admin")
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
    with col2:
        users = store.load("users", [])
        if any(x.get("must_change") for x in users) or not users:
            st.markdown(
                f'<div class="note">First run: sign in with <b>{auth.DEFAULT_ADMIN["username"]}</b> / '
                f'<b>{auth.DEFAULT_ADMIN["password"]}</b> and change the password immediately '
                'under Settings.</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
def _csv_bytes(rows, fields=None):
    if not rows:
        return b""
    fields = fields or sorted({k for r in rows for k in r.keys()})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


def _next_student_code():
    rows = store.load("students", [])
    n = len(rows) + 1
    while any(s.get("student_code") == f"KP{n:04d}" for s in rows):
        n += 1
    return f"KP{n:04d}"


def _batch_options():
    return {b.get("name", b.get("id")): b.get("id") for b in store.load("batches", [])}


def _student_label(s):
    return f"{s.get('student_code','')} · {s.get('name','')}"


# --------------------------------------------------------------------------- #
def portal(site):
    user = auth.current_user()
    section("Admin portal", f"Welcome, {user.get('name') or user.get('username')}",
            f"Storage: {store.storage_mode()} · everything you change here is saved "
            f"{'into the private GitHub repo' if store.storage_mode()=='github' else 'to local JSON files'}.")

    if user.get("must_change"):
        st.markdown('<div class="note">⚠️ You are still on the default password. '
                    'Change it under <b>Settings</b>.</div>', unsafe_allow_html=True)

    errs = st.session_state.get("_store_errors")
    if errs:
        with st.expander(f"⚠️ {len(errs)} storage warning(s)"):
            for e in errs[-5:]:
                st.code(e)

    tabs = st.tabs([
        "📊 Dashboard", "📝 Registrations", "👩‍🎓 Students", "🎓 Batches",
        "✅ Attendance", "💰 Fees", "🎬 Videos", "🖼 Gallery", "📅 Events",
        "💬 Testimonials", "📣 Announcements", "📨 Enquiries",
        "🎨 Site content", "⚙️ Settings",
    ])

    with tabs[0]: _dashboard(site)
    with tabs[1]: _registrations()
    with tabs[2]: _students()
    with tabs[3]: _batches()
    with tabs[4]: _attendance()
    with tabs[5]: _fees()
    with tabs[6]: _videos()
    with tabs[7]: _gallery()
    with tabs[8]: _events()
    with tabs[9]: _testimonials()
    with tabs[10]: _announcements()
    with tabs[11]: _enquiries()
    with tabs[12]: _site_content(site)
    with tabs[13]: _settings(user)


# --------------------------------------------------------------------------- #
def _dashboard(site):
    students = store.load("students", [])
    active = [s for s in students if s.get("status") == "active"]
    pending = [r for r in store.load("registrations", []) if r.get("status") == "pending"]
    fees = store.load("fees", [])
    due = sum(float(f.get("amount", 0) or 0) for f in fees if f.get("status") != "paid")
    collected = sum(float(f.get("amount", 0) or 0) for f in fees if f.get("status") == "paid")
    enq = [e for e in store.load("enquiries", []) if e.get("status") == "new"]

    c = st.columns(5)
    with c[0]: kpi(len(active), "Active students")
    with c[1]: kpi(len(pending), "Pending registrations")
    with c[2]: kpi(f"₹{int(collected)}", "Fees collected")
    with c[3]: kpi(f"₹{int(due)}", "Fees outstanding")
    with c[4]: kpi(len(enq), "New enquiries")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Students per batch")
        batches = store.load("batches", [])
        rows = [{"Batch": b.get("name"),
                 "Students": sum(1 for s in active if s.get("batch_id") == b.get("id")),
                 "Seats": b.get("seats")} for b in batches]
        if rows:
            st.dataframe(rows, width="stretch", hide_index=True)
        else:
            st.info("No batches yet.")
    with c2:
        st.markdown("#### Needs your attention")
        if pending:
            st.warning(f"{len(pending)} registration(s) waiting for approval.")
        if enq:
            st.warning(f"{len(enq)} unanswered enquiry(ies).")
        unpaid = [f for f in fees if f.get("status") != "paid"]
        if unpaid:
            st.warning(f"{len(unpaid)} unpaid fee record(s).")
        if not (pending or enq or unpaid):
            st.success("Everything is clear. Nice.")

    st.markdown("---")
    st.markdown("#### Recent activity")
    recent = []
    for r in store.load("registrations", [])[-5:]:
        recent.append({"When": str(r.get("created_at", ""))[:16], "Type": "Registration",
                       "Detail": f"{r.get('name')} — {r.get('status')}"})
    for e in store.load("enquiries", [])[-5:]:
        recent.append({"When": str(e.get("created_at", ""))[:16], "Type": "Enquiry",
                       "Detail": f"{e.get('name')} — {e.get('interest')}"})
    recent.sort(key=lambda r: r["When"], reverse=True)
    if recent:
        st.dataframe(recent[:10], width="stretch", hide_index=True)
    else:
        st.caption("Nothing yet.")


# --------------------------------------------------------------------------- #
def _registrations():
    st.markdown("### Registrations")
    rows = store.load("registrations", [])
    status_filter = st.radio("Show", ["pending", "approved", "rejected", "all"],
                             horizontal=True, key="regfilter")
    shown = [r for r in rows if status_filter == "all" or r.get("status") == status_filter]
    if not shown:
        st.info("Nothing here.")
        return
    batch_opts = _batch_options()

    for r in reversed(shown):
        with st.expander(f"{r.get('name')} — {r.get('batch_label','')} "
                         f"[{r.get('status')}] · {str(r.get('created_at',''))[:10]}"):
            st.markdown(
                f"**Phone:** {esc(r.get('phone'))} &nbsp;·&nbsp; **Email:** {esc(r.get('email'))}  \n"
                f"**DOB:** {esc(r.get('dob'))} &nbsp;·&nbsp; **City:** {esc(r.get('city'))}  \n"
                f"**Guardian:** {esc(r.get('guardian') or '—')}  \n"
                f"**Experience:** {esc(r.get('experience'))}  \n"
                f"**Notes:** {esc(r.get('notes') or '—')}")
            if r.get("status") == "pending":
                names = list(batch_opts.keys())
                default_idx = 0
                for i, n in enumerate(names):
                    if batch_opts[n] == r.get("batch_id"):
                        default_idx = i
                c1, c2, c3 = st.columns([2, 1, 1])
                chosen = c1.selectbox("Assign to batch", names or ["—"],
                                      index=default_idx if names else 0,
                                      key=f"regb_{r['id']}")
                if c2.button("Approve", key=f"appr_{r['id']}"):
                    bid = batch_opts.get(chosen, "")
                    batch = store.get("batches", bid) or {}
                    store.insert("students", {
                        "student_code": _next_student_code(),
                        "name": r.get("name"), "email": r.get("email"),
                        "phone": r.get("phone"), "dob": r.get("dob"),
                        "guardian": r.get("guardian"), "city": r.get("city"),
                        "batch_id": bid, "level": batch.get("level", ""),
                        "password": r.get("password"), "status": "active",
                        "joined_on": date.today().isoformat(),
                        "monthly_fee": batch.get("fee_monthly", 0),
                        "notes_for_student": "",
                    }, prefix="stu", message=f"approve registration: {r.get('name')}")
                    store.update("registrations", r["id"],
                                 {"status": "approved", "batch_id": bid},
                                 "registration approved")
                    st.success(f"{r.get('name')} is now an active student.")
                    st.rerun()
                if c3.button("Reject", key=f"rej_{r['id']}"):
                    store.update("registrations", r["id"], {"status": "rejected"},
                                 "registration rejected")
                    st.rerun()
            else:
                if st.button("Delete record", key=f"regdel_{r['id']}"):
                    store.delete("registrations", r["id"], "delete registration")
                    st.rerun()


# --------------------------------------------------------------------------- #
def _students():
    st.markdown("### Students")
    students = store.load("students", [])
    batch_opts = _batch_options()
    id_to_batch = {v: k for k, v in batch_opts.items()}

    c1, c2, c3 = st.columns([2, 2, 1])
    q = c1.text_input("Search by name, code, phone or email", key="stu_q")
    bfilter = c2.selectbox("Batch", ["All"] + list(batch_opts.keys()), key="stu_bf")
    sfilter = c3.selectbox("Status", ["All", "active", "inactive"], key="stu_sf")

    shown = students
    if q:
        ql = q.lower()
        shown = [s for s in shown if ql in json.dumps(
            {k: v for k, v in s.items() if k != "password"}).lower()]
    if bfilter != "All":
        shown = [s for s in shown if s.get("batch_id") == batch_opts[bfilter]]
    if sfilter != "All":
        shown = [s for s in shown if s.get("status") == sfilter]

    if shown:
        st.dataframe([{
            "Code": s.get("student_code"), "Name": s.get("name"),
            "Batch": id_to_batch.get(s.get("batch_id"), "—"),
            "Level": s.get("level"), "Phone": s.get("phone"),
            "Email": s.get("email"), "Status": s.get("status"),
            "Fee/month": s.get("monthly_fee"), "Joined": s.get("joined_on"),
        } for s in shown], width="stretch", hide_index=True)
        st.download_button("⬇ Export students CSV",
                           _csv_bytes([{k: v for k, v in s.items() if k != "password"} for s in shown]),
                           "students.csv", "text/csv")
    else:
        st.info("No students match.")

    st.markdown("---")
    with st.expander("➕ Add a student manually"):
        with st.form("add_student", clear_on_submit=True):
            c = st.columns(2)
            name = c[0].text_input("Name *")
            phone = c[1].text_input("Phone *")
            c = st.columns(2)
            email = c[0].text_input("Email *")
            city = c[1].text_input("City")
            c = st.columns(3)
            bname = c[0].selectbox("Batch", list(batch_opts.keys()) or ["—"])
            level = c[1].text_input("Level", value="Beginner")
            fee = c[2].number_input("Monthly fee ₹", min_value=0, value=1500, step=100)
            guardian = st.text_input("Guardian")
            pw = st.text_input("Portal password *", type="password")
            if st.form_submit_button("Add student"):
                if not (name and phone and email and len(pw) >= 6):
                    st.error("Name, phone, email and a 6+ character password are required.")
                else:
                    store.insert("students", {
                        "student_code": _next_student_code(), "name": name.strip(),
                        "email": email.strip().lower(), "phone": phone.strip(),
                        "city": city.strip(), "guardian": guardian.strip(),
                        "batch_id": batch_opts.get(bname, ""), "level": level,
                        "monthly_fee": fee, "password": auth.hash_password(pw),
                        "status": "active", "joined_on": date.today().isoformat(),
                        "notes_for_student": "",
                    }, prefix="stu", message=f"add student {name}")
                    st.success("Student added.")
                    st.rerun()

    if shown:
        st.markdown("---")
        st.markdown("#### Edit a student")
        pick = st.selectbox("Choose", [_student_label(s) for s in shown], key="stu_edit_pick")
        target = next((s for s in shown if _student_label(s) == pick), None)
        if target:
            with st.form(f"edit_{target['id']}"):
                c = st.columns(2)
                name = c[0].text_input("Name", target.get("name", ""))
                phone = c[1].text_input("Phone", target.get("phone", ""))
                c = st.columns(2)
                email = c[0].text_input("Email", target.get("email", ""))
                city = c[1].text_input("City", target.get("city", ""))
                c = st.columns(3)
                bnames = list(batch_opts.keys())
                bidx = bnames.index(id_to_batch[target["batch_id"]]) \
                    if target.get("batch_id") in id_to_batch else 0
                bname = c[0].selectbox("Batch", bnames or ["—"], index=bidx if bnames else 0)
                level = c[1].text_input("Level", target.get("level", ""))
                fee = c[2].number_input("Monthly fee ₹", min_value=0,
                                        value=int(target.get("monthly_fee") or 0), step=100)
                status = st.selectbox("Status", ["active", "inactive"],
                                      index=0 if target.get("status") == "active" else 1)
                note = st.text_area("Private note shown to this student",
                                    target.get("notes_for_student", ""), height=80)
                newpw = st.text_input("Reset password (leave blank to keep)", type="password")
                c = st.columns(2)
                save = c[0].form_submit_button("Save changes")
                remove = c[1].form_submit_button("Delete student")
            if save:
                changes = {"name": name, "phone": phone, "email": email.lower(),
                           "city": city, "batch_id": batch_opts.get(bname, ""),
                           "level": level, "monthly_fee": fee, "status": status,
                           "notes_for_student": note}
                if newpw:
                    if len(newpw) < 6:
                        st.error("Password must be 6+ characters.")
                        changes = None
                    else:
                        changes["password"] = auth.hash_password(newpw)
                if changes:
                    store.update("students", target["id"], changes, f"update student {name}")
                    st.success("Saved.")
                    st.rerun()
            if remove:
                store.delete("students", target["id"], f"delete student {target.get('name')}")
                st.rerun()


# --------------------------------------------------------------------------- #
def _batches():
    st.markdown("### Batches")
    rows = store.load("batches", [])
    for b in rows:
        with st.expander(f"{b.get('name')} — {b.get('days')} {b.get('time')}"):
            with st.form(f"b_{b['id']}"):
                c = st.columns(2)
                name = c[0].text_input("Name", b.get("name", ""))
                level = c[1].text_input("Level", b.get("level", ""))
                c = st.columns(3)
                days = c[0].text_input("Days", b.get("days", ""))
                time_ = c[1].text_input("Time", b.get("time", ""))
                mode = c[2].text_input("Mode", b.get("mode", ""))
                c = st.columns(4)
                age = c[0].text_input("Age group", b.get("age_group", ""))
                seats = c[1].number_input("Seats", 0, 200, int(b.get("seats") or 0))
                fm = c[2].number_input("Fee / month ₹", 0, 100000, int(b.get("fee_monthly") or 0), 100)
                fq = c[3].number_input("Fee / quarter ₹", 0, 300000, int(b.get("fee_quarterly") or 0), 100)
                desc = st.text_area("Description", b.get("description", ""), height=80)
                c = st.columns(2)
                save = c[0].form_submit_button("Save")
                rm = c[1].form_submit_button("Delete batch")
            if save:
                store.update("batches", b["id"], {
                    "name": name, "level": level, "days": days, "time": time_,
                    "mode": mode, "age_group": age, "seats": seats,
                    "fee_monthly": fm, "fee_quarterly": fq, "description": desc},
                    f"update batch {name}")
                st.success("Saved."); st.rerun()
            if rm:
                store.delete("batches", b["id"], "delete batch"); st.rerun()

    with st.expander("➕ New batch"):
        with st.form("new_batch", clear_on_submit=True):
            c = st.columns(2)
            name = c[0].text_input("Name *")
            level = c[1].text_input("Level", "Beginner")
            c = st.columns(3)
            days = c[0].text_input("Days", "Sat & Sun")
            time_ = c[1].text_input("Time", "10:00 AM – 11:30 AM")
            mode = c[2].text_input("Mode", "In-studio")
            c = st.columns(4)
            age = c[0].text_input("Age group", "5 years and above")
            seats = c[1].number_input("Seats", 0, 200, 15)
            fm = c[2].number_input("Fee / month ₹", 0, 100000, 1500, 100)
            fq = c[3].number_input("Fee / quarter ₹", 0, 300000, 4200, 100)
            desc = st.text_area("Description", height=80)
            if st.form_submit_button("Create batch"):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    store.insert("batches", {
                        "name": name, "level": level, "days": days, "time": time_,
                        "mode": mode, "age_group": age, "seats": seats,
                        "fee_monthly": fm, "fee_quarterly": fq, "description": desc},
                        prefix="batch", message=f"create batch {name}")
                    st.success("Created."); st.rerun()


# --------------------------------------------------------------------------- #
def _attendance():
    st.markdown("### Attendance")
    batch_opts = _batch_options()
    if not batch_opts:
        st.info("Create a batch first.")
        return
    c1, c2 = st.columns([2, 1])
    bname = c1.selectbox("Batch", list(batch_opts.keys()), key="att_b")
    on = c2.date_input("Class date", value=date.today(), format="DD/MM/YYYY", key="att_d")
    bid = batch_opts[bname]
    students = [s for s in store.load("students", [])
                if s.get("batch_id") == bid and s.get("status") == "active"]
    if not students:
        st.info("No active students in this batch.")
        return

    existing = {a.get("student_id"): a for a in store.load("attendance", [])
                if a.get("batch_id") == bid and str(a.get("date")) == on.isoformat()}

    with st.form("att_form"):
        marks = {}
        for s in students:
            c = st.columns([3, 2, 3])
            c[0].markdown(f"**{esc(s.get('name'))}** · {esc(s.get('student_code'))}")
            prev = existing.get(s["id"], {})
            idx = ["present", "absent", "late", "excused"].index(prev.get("status", "present")) \
                if prev.get("status") in ("present", "absent", "late", "excused") else 0
            status = c[1].selectbox("Status", ["present", "absent", "late", "excused"],
                                    index=idx, key=f"att_{s['id']}", label_visibility="collapsed")
            note = c[2].text_input("Note", prev.get("note", ""), key=f"attn_{s['id']}",
                                   label_visibility="collapsed", placeholder="note (optional)")
            marks[s["id"]] = (status, note)
        if st.form_submit_button("Save attendance for this date"):
            rows = [a for a in store.load("attendance", [])
                    if not (a.get("batch_id") == bid and str(a.get("date")) == on.isoformat())]
            for sid, (status, note) in marks.items():
                rows.append({"id": store.new_id("att"), "student_id": sid, "batch_id": bid,
                             "date": on.isoformat(), "status": status, "note": note,
                             "created_at": store.now_iso()})
            store.save("attendance", rows, f"attendance {bname} {on.isoformat()}")
            st.success("Attendance saved.")

    st.markdown("---")
    st.markdown("#### Attendance summary for this batch")
    att = [a for a in store.load("attendance", []) if a.get("batch_id") == bid]
    summary = []
    for s in students:
        mine = [a for a in att if a.get("student_id") == s["id"]]
        pres = sum(1 for a in mine if a.get("status") == "present")
        summary.append({"Code": s.get("student_code"), "Name": s.get("name"),
                        "Classes": len(mine), "Present": pres,
                        "%": round(100 * pres / len(mine)) if mine else 0})
    st.dataframe(summary, width="stretch", hide_index=True)
    if att:
        st.download_button("⬇ Export attendance CSV", _csv_bytes(att), "attendance.csv", "text/csv")


# --------------------------------------------------------------------------- #
def _fees():
    st.markdown("### Fees")
    students = [s for s in store.load("students", []) if s.get("status") == "active"]
    sid_to_name = {s["id"]: _student_label(s) for s in students}
    batch_opts = _batch_options()
    fees = store.load("fees", [])

    with st.expander("🧾 Generate fee records for a month"):
        c = st.columns([2, 2, 1])
        bname = c[0].selectbox("Batch", ["All batches"] + list(batch_opts.keys()), key="fee_gb")
        period = c[1].text_input("Period label", value=date.today().strftime("%b %Y"), key="fee_gp")
        if c[2].button("Generate"):
            targets = students if bname == "All batches" else \
                [s for s in students if s.get("batch_id") == batch_opts[bname]]
            rows = list(fees)
            added = 0
            for s in targets:
                if any(f.get("student_id") == s["id"] and f.get("period") == period for f in rows):
                    continue
                rows.append({"id": store.new_id("fee"), "student_id": s["id"],
                             "batch_id": s.get("batch_id"), "period": period,
                             "amount": s.get("monthly_fee") or 0, "status": "unpaid",
                             "paid_on": "", "method": "", "note": "",
                             "created_at": store.now_iso()})
                added += 1
            store.save("fees", rows, f"generate fees for {period}")
            st.success(f"{added} fee record(s) created for {period}.")
            st.rerun()

    c = st.columns([2, 2, 2])
    fstatus = c[0].selectbox("Status", ["All", "unpaid", "paid", "waived"], key="fee_fs")
    fperiod = c[1].selectbox("Period", ["All"] + sorted({f.get("period", "") for f in fees}), key="fee_fp")
    fbatch = c[2].selectbox("Batch", ["All"] + list(batch_opts.keys()), key="fee_fb")

    shown = fees
    if fstatus != "All": shown = [f for f in shown if f.get("status") == fstatus]
    if fperiod != "All": shown = [f for f in shown if f.get("period") == fperiod]
    if fbatch != "All": shown = [f for f in shown if f.get("batch_id") == batch_opts[fbatch]]

    if not shown:
        st.info("No fee records match.")
    else:
        total = sum(float(f.get("amount", 0) or 0) for f in shown)
        paid = sum(float(f.get("amount", 0) or 0) for f in shown if f.get("status") == "paid")
        c = st.columns(3)
        with c[0]: kpi(f"₹{int(total)}", "Total billed")
        with c[1]: kpi(f"₹{int(paid)}", "Collected")
        with c[2]: kpi(f"₹{int(total-paid)}", "Outstanding")

        st.dataframe([{
            "Student": sid_to_name.get(f.get("student_id"), f.get("student_id")),
            "Period": f.get("period"), "Amount": f.get("amount"),
            "Status": f.get("status"), "Paid on": f.get("paid_on"),
            "Method": f.get("method"), "Note": f.get("note")} for f in shown],
            width="stretch", hide_index=True)
        st.download_button("⬇ Export fees CSV", _csv_bytes(shown), "fees.csv", "text/csv")

        st.markdown("#### Mark a record")
        labels = {f"{sid_to_name.get(f.get('student_id'),'?')} — {f.get('period')} "
                  f"(₹{f.get('amount')}, {f.get('status')})": f["id"] for f in shown}
        pick = st.selectbox("Fee record", list(labels.keys()), key="fee_pick")
        with st.form("fee_edit"):
            c = st.columns(4)
            status = c[0].selectbox("Status", ["unpaid", "paid", "waived"])
            paid_on = c[1].date_input("Paid on", value=date.today(), format="DD/MM/YYYY")
            method = c[2].selectbox("Method", ["", "UPI", "Cash", "Bank transfer", "Card"])
            amount = c[3].number_input("Amount ₹", 0, 1000000,
                                       int(next((f.get("amount") or 0) for f in shown
                                                if f["id"] == labels[pick])), 100)
            note = st.text_input("Note")
            c = st.columns(2)
            save = c[0].form_submit_button("Update record")
            rm = c[1].form_submit_button("Delete record")
        if save:
            store.update("fees", labels[pick], {
                "status": status, "amount": amount, "method": method, "note": note,
                "paid_on": paid_on.isoformat() if status == "paid" else ""},
                "update fee record")
            st.success("Updated."); st.rerun()
        if rm:
            store.delete("fees", labels[pick], "delete fee record"); st.rerun()

    with st.expander("➕ Add a one-off charge"):
        with st.form("fee_add", clear_on_submit=True):
            c = st.columns(3)
            sname = c[0].selectbox("Student", [sid_to_name[k] for k in sid_to_name] or ["—"])
            period = c[1].text_input("Period / label", "Costume")
            amount = c[2].number_input("Amount ₹", 0, 1000000, 500, 100)
            note = st.text_input("Note")
            if st.form_submit_button("Add charge"):
                sid = next((k for k, v in sid_to_name.items() if v == sname), None)
                if sid:
                    stu = store.get("students", sid) or {}
                    store.insert("fees", {"student_id": sid, "batch_id": stu.get("batch_id"),
                                          "period": period, "amount": amount, "status": "unpaid",
                                          "paid_on": "", "method": "", "note": note},
                                 prefix="fee", message="add one-off charge")
                    st.success("Added."); st.rerun()


# --------------------------------------------------------------------------- #
def _videos():
    st.markdown("### Videos")
    st.caption("Paste a YouTube link, an unlisted Google Drive link, an Instagram reel URL, "
               "or a direct .mp4 URL. Public videos show on the website; the rest only "
               "appear in the student portal for the chosen batch or level.")
    batch_opts = _batch_options()
    rows = store.load("videos", [])

    with st.expander("➕ Add a video", expanded=not rows):
        with st.form("vid_add", clear_on_submit=True):
            title = st.text_input("Title *")
            url = st.text_input("Video URL *", placeholder="https://www.youtube.com/watch?v=… or Instagram reel URL")
            desc = st.text_area("Description", height=70)
            c = st.columns(3)
            bname = c[0].selectbox("Batch (optional)", ["— any —"] + list(batch_opts.keys()))
            level = c[1].text_input("Level (optional)")
            public = c[2].checkbox("Show publicly", value=False)
            if st.form_submit_button("Add video"):
                if not title.strip() or not url.strip():
                    st.error("Title and URL are required.")
                else:
                    store.insert("videos", {
                        "title": title, "url": url.strip(), "description": desc,
                        "batch_id": batch_opts.get(bname, ""), "level": level,
                        "public": public, "kind": "link"},
                        prefix="vid", message=f"add video {title}")
                    st.success("Added."); st.rerun()

    for v in rows:
        with st.expander(f"{'🌐 ' if v.get('public') else '🔒 '}{v.get('title')}"):
            _embed_video(v.get("url"), height=260)
            with st.form(f"v_{v['id']}"):
                title = st.text_input("Title", v.get("title", ""))
                url = st.text_input("URL", v.get("url", ""))
                desc = st.text_area("Description", v.get("description", ""), height=70)
                c = st.columns(3)
                names = ["— any —"] + list(batch_opts.keys())
                cur = next((n for n, i in batch_opts.items() if i == v.get("batch_id")), "— any —")
                bname = c[0].selectbox("Batch", names, index=names.index(cur) if cur in names else 0)
                level = c[1].text_input("Level", v.get("level", ""))
                public = c[2].checkbox("Public", value=bool(v.get("public")))
                c = st.columns(2)
                save = c[0].form_submit_button("Save")
                rm = c[1].form_submit_button("Delete")
            if save:
                store.update("videos", v["id"], {
                    "title": title, "url": url, "description": desc,
                    "batch_id": batch_opts.get(bname, ""), "level": level,
                    "public": public}, "update video")
                st.success("Saved."); st.rerun()
            if rm:
                store.delete("videos", v["id"], "delete video"); st.rerun()


# --------------------------------------------------------------------------- #
def _simple_crud(table, title, fields, prefix, label_key, help_text=""):
    """Generic editor for gallery / events / testimonials / announcements."""
    st.markdown(f"### {title}")
    if help_text:
        st.caption(help_text)
    rows = store.load(table, [])

    with st.expander(f"➕ New {title.rstrip('s').lower()}", expanded=not rows):
        with st.form(f"{table}_add", clear_on_submit=True):
            values = {}
            for key, spec in fields.items():
                values[key] = _field(spec, key, None, f"{table}_new_{key}")
            if st.form_submit_button("Add"):
                if not str(values.get(label_key, "")).strip():
                    st.error(f"{fields[label_key]['label']} is required.")
                else:
                    store.insert(table, values, prefix=prefix, message=f"add {table} entry")
                    st.success("Added."); st.rerun()

    for r in rows:
        with st.expander(str(r.get(label_key, r.get("id")))[:80]):
            with st.form(f"{table}_{r['id']}"):
                values = {}
                for key, spec in fields.items():
                    values[key] = _field(spec, key, r.get(key), f"{table}_{r['id']}_{key}")
                c = st.columns(2)
                save = c[0].form_submit_button("Save")
                rm = c[1].form_submit_button("Delete")
            if save:
                store.update(table, r["id"], values, f"update {table} entry"); st.success("Saved."); st.rerun()
            if rm:
                store.delete(table, r["id"], f"delete {table} entry"); st.rerun()


def _field(spec, key, current, widget_key):
    kind = spec.get("type", "text")
    label = spec.get("label", key)
    if kind == "text":
        return st.text_input(label, value=str(current or spec.get("default", "")), key=widget_key)
    if kind == "area":
        return st.text_area(label, value=str(current or spec.get("default", "")),
                            height=spec.get("height", 90), key=widget_key)
    if kind == "bool":
        return st.checkbox(label, value=bool(current if current is not None else spec.get("default", True)),
                           key=widget_key)
    if kind == "date":
        try:
            val = datetime.strptime(str(current)[:10], "%Y-%m-%d").date()
        except Exception:
            val = date.today()
        return st.date_input(label, value=val, format="DD/MM/YYYY", key=widget_key).isoformat()
    if kind == "select":
        opts = spec.get("options", [])
        idx = opts.index(current) if current in opts else 0
        return st.selectbox(label, opts, index=idx, key=widget_key)
    return st.text_input(label, value=str(current or ""), key=widget_key)


def _gallery():
    _simple_crud("gallery", "Gallery", {
        "caption": {"type": "text", "label": "Caption"},
        "url": {"type": "text", "label": "Image URL"},
        "published": {"type": "bool", "label": "Show on website", "default": True},
    }, "img", "caption",
        "Paste a direct image URL (Instagram post images, Google Drive direct links, "
        "Imgur, or any https image link).")


def _events():
    _simple_crud("events", "Events", {
        "title": {"type": "text", "label": "Title"},
        "date": {"type": "date", "label": "Date"},
        "venue": {"type": "text", "label": "Venue"},
        "description": {"type": "area", "label": "Description"},
        "image": {"type": "text", "label": "Image URL (optional)"},
        "published": {"type": "bool", "label": "Show on website", "default": True},
    }, "evt", "title")


def _testimonials():
    _simple_crud("testimonials", "Testimonials", {
        "name": {"type": "text", "label": "Name"},
        "relation": {"type": "text", "label": "Relation (e.g. Parent, Advanced batch)"},
        "quote": {"type": "area", "label": "Quote"},
        "published": {"type": "bool", "label": "Show on website", "default": True},
    }, "tst", "name")


def _announcements():
    batch_opts = _batch_options()
    _simple_crud("announcements", "Announcements", {
        "title": {"type": "text", "label": "Title"},
        "body": {"type": "area", "label": "Message"},
        "audience": {"type": "select", "label": "Audience",
                     "options": ["all", "students"] + list(batch_opts.values())},
        "pinned": {"type": "bool", "label": "Pin to top", "default": False},
    }, "ann", "title",
        "Announcements appear in the student portal. Set the banner on the home page "
        "under Site content.")


# --------------------------------------------------------------------------- #
def _enquiries():
    st.markdown("### Enquiries from the website")
    rows = store.load("enquiries", [])
    if not rows:
        st.info("No enquiries yet.")
        return
    f = st.radio("Show", ["new", "handled", "all"], horizontal=True, key="enq_f")
    shown = [e for e in rows if f == "all" or e.get("status") == f]
    st.download_button("⬇ Export enquiries CSV", _csv_bytes(rows), "enquiries.csv", "text/csv")
    for e in reversed(shown):
        with st.expander(f"{e.get('name')} — {e.get('interest')} · {str(e.get('created_at',''))[:10]}"):
            st.markdown(f"**Phone:** {esc(e.get('phone'))} · **Email:** {esc(e.get('email'))}  \n"
                        f"**Message:** {esc(e.get('message') or '—')}")
            c = st.columns(2)
            if c[0].button("Mark handled", key=f"enqh_{e['id']}"):
                store.update("enquiries", e["id"], {"status": "handled"}, "enquiry handled"); st.rerun()
            if c[1].button("Delete", key=f"enqd_{e['id']}"):
                store.delete("enquiries", e["id"], "delete enquiry"); st.rerun()


# --------------------------------------------------------------------------- #
def _site_content(site):
    st.markdown("### Site content")
    st.caption("Everything the public website shows, editable here.")

    with st.form("site_form"):
        st.markdown("#### Identity")
        c = st.columns(2)
        academy_name = c[0].text_input("Academy name", site.get("academy_name", ""))
        tagline = c[1].text_input("Tagline", site.get("tagline", ""))
        c = st.columns(2)
        primary = c[0].color_picker("Primary colour", site.get("primary_color", "#7B1E3C"))
        accent = c[1].color_picker("Accent colour", site.get("accent_color", "#C9A227"))

        st.markdown("#### Home page")
        hero_heading = st.text_input("Hero heading", site.get("hero_heading", ""))
        hero_sub = st.text_area("Hero subtitle", site.get("hero_sub", ""), height=80)
        banner = st.text_input("Announcement banner (blank to hide)",
                               site.get("announcement_banner", ""))

        st.markdown("#### Guru")
        c = st.columns(2)
        guru_name = c[0].text_input("Guru name", site.get("guru_name", ""))
        guru_title = c[1].text_input("Guru title", site.get("guru_title", ""))
        guru_bio = st.text_area("Guru bio (blank line separates paragraphs)",
                                site.get("guru_bio", ""), height=170)
        about_story = st.text_area("About / story text", site.get("about_story", ""), height=150)

        st.markdown("#### Why-us cards")
        why = list(site.get("why_us", []))
        while len(why) < 4:
            why.append({"icon": "✧", "title": "", "text": ""})
        new_why = []
        for i in range(4):
            c = st.columns([1, 3, 6])
            icon = c[0].text_input(f"Icon {i+1}", why[i].get("icon", ""), key=f"wi{i}")
            title = c[1].text_input(f"Title {i+1}", why[i].get("title", ""), key=f"wt{i}")
            text = c[2].text_input(f"Text {i+1}", why[i].get("text", ""), key=f"wx{i}")
            if title.strip():
                new_why.append({"icon": icon, "title": title, "text": text})

        st.markdown("#### Contact & links")
        c = st.columns(3)
        phone = c[0].text_input("Phone", site.get("phone", ""))
        email = c[1].text_input("Email", site.get("email", ""))
        whatsapp = c[2].text_input("WhatsApp link", site.get("whatsapp", ""))
        address = st.text_input("Address", site.get("address", ""))
        c = st.columns(2)
        maps_url = c[0].text_input("Google Maps link", site.get("maps_url", ""))
        insta = c[1].text_input("Instagram URL", site.get("guru_instagram", ""))
        c = st.columns(2)
        youtube = c[0].text_input("YouTube URL", site.get("youtube", ""))
        facebook = c[1].text_input("Facebook URL", site.get("facebook", ""))
        insta_note = st.text_input("Instagram section note", site.get("instagram_embed_note", ""))
        footer_note = st.text_input("Footer note", site.get("footer_note", ""))

        st.markdown("#### Switches")
        c = st.columns(2)
        show_fees = c[0].checkbox("Show fees publicly", bool(site.get("show_fees_publicly", True)))
        reg_open = c[1].checkbox("Registrations open", bool(site.get("registration_open", True)))

        if st.form_submit_button("Save site content"):
            payload = dict(site)
            payload.update({
                "academy_name": academy_name, "tagline": tagline,
                "primary_color": primary, "accent_color": accent,
                "hero_heading": hero_heading, "hero_sub": hero_sub,
                "announcement_banner": banner, "guru_name": guru_name,
                "guru_title": guru_title, "guru_bio": guru_bio,
                "about_story": about_story, "why_us": new_why,
                "phone": phone, "email": email, "whatsapp": whatsapp,
                "address": address, "maps_url": maps_url, "guru_instagram": insta,
                "youtube": youtube, "facebook": facebook,
                "instagram_embed_note": insta_note, "footer_note": footer_note,
                "show_fees_publicly": show_fees, "registration_open": reg_open,
            })
            store.save("site", payload, "update site content")
            st.success("Site updated.")
            st.rerun()


# --------------------------------------------------------------------------- #
def _settings(user):
    st.markdown("### Settings")

    st.markdown("#### Change admin password")
    with st.form("adm_pw"):
        n1 = st.text_input("New password", type="password")
        n2 = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Update password"):
            if len(n1) < 8:
                st.error("Use at least 8 characters.")
            elif n1 != n2:
                st.error("Passwords do not match.")
            else:
                auth.set_admin_password(user.get("id", "user_admin"), n1)
                st.success("Password changed. Use it next time you sign in.")

    st.markdown("---")
    st.markdown("#### Storage")
    mode = store.storage_mode()
    st.markdown(f"Current mode: **{mode}**")
    if mode == "github":
        cfg = store.gh_config()
        st.markdown(f"Repository: `{cfg['repo']}` · branch `{cfg['branch']}` · folder `data/`")
        st.caption("Every save above writes a commit to that private repository.")
    else:
        st.markdown('<div class="note">Running on local JSON files. On Streamlit Cloud, add a '
                    '<code>[github]</code> section with <code>token</code> and <code>repo</code> '
                    'to the app secrets so data is committed to your private repo and survives '
                    'restarts.</div>', unsafe_allow_html=True)
    if st.button("🔄 Reload data from storage"):
        store.refresh(); st.rerun()

    st.markdown("---")
    st.markdown("#### Backup")
    bundle = {t: store.load(t, [] if t != "site" else {}) for t in store.TABLES}
    for row in bundle.get("students", []) or []:
        row = row
    st.download_button("⬇ Download full data backup (JSON)",
                       json.dumps(bundle, indent=2, ensure_ascii=False).encode("utf-8"),
                       f"backup-{date.today().isoformat()}.json", "application/json")

    with st.expander("⚠️ Restore from a backup file"):
        up = st.file_uploader("Backup JSON", type=["json"])
        confirm = st.checkbox("I understand this overwrites all current data.")
        if up and confirm and st.button("Restore now"):
            data = json.load(up)
            for table, payload in data.items():
                if table in store.TABLES:
                    store.save(table, payload, f"restore {table} from backup")
            st.success("Restored."); store.refresh(); st.rerun()
