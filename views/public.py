"""Public-facing pages."""
from __future__ import annotations

from datetime import date, datetime

import streamlit as st
import streamlit.components.v1 as components

from lib import auth, seed, store
from lib.ui import card, esc, kpi, pill, section

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _nice_date(value):
    try:
        d = datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        return d.day, MONTHS[d.month - 1], d.strftime("%d %b %Y")
    except Exception:
        return "–", "", str(value or "")


def _embed_video(url, height=330):
    """Render a YouTube / Drive / Instagram / direct video link."""
    url = (url or "").strip()
    if not url:
        st.info("No video link set yet.")
        return
    low = url.lower()
    if "youtu" in low:
        vid = ""
        if "watch?v=" in url:
            vid = url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            vid = url.split("youtu.be/")[1].split("?")[0]
        elif "/embed/" in url:
            vid = url.split("/embed/")[1].split("?")[0]
        elif "/shorts/" in url:
            vid = url.split("/shorts/")[1].split("?")[0]
        if vid:
            components.html(
                f'<iframe width="100%" height="{height}" src="https://www.youtube.com/embed/{vid}" '
                'frameborder="0" style="border-radius:14px" allowfullscreen></iframe>',
                height=height + 10)
            return
    if "instagram.com" in low:
        permalink = url.split("?")[0].rstrip("/") + "/"
        components.html(
            f"""<blockquote class="instagram-media" data-instgrm-permalink="{permalink}"
 data-instgrm-version="14" style="width:100%;margin:0;border:0"></blockquote>
<script async src="//www.instagram.com/embed.js"></script>""",
            height=height + 260)
        return
    if "drive.google.com" in low:
        fid = ""
        if "/d/" in url:
            fid = url.split("/d/")[1].split("/")[0]
        elif "id=" in url:
            fid = url.split("id=")[1].split("&")[0]
        if fid:
            components.html(
                f'<iframe src="https://drive.google.com/file/d/{fid}/preview" width="100%" '
                f'height="{height}" style="border-radius:14px" allow="autoplay"></iframe>',
                height=height + 10)
            return
    if low.endswith((".mp4", ".webm", ".mov", ".m4v")):
        st.video(url)
        return
    st.markdown(f"[Open video ↗]({url})")


# --------------------------------------------------------------------------- #
def home(site):
    st.html(
        f"""<div class="hero">
  <div class="hero-eyebrow">{esc(site.get('hero_eyebrow') or 'Classical Kuchipudi')}</div>
  <h1>{esc(site.get('hero_heading'))}</h1>
  <p>{esc(site.get('hero_sub'))}</p>
</div>""")

    if site.get("announcement_banner"):
        st.markdown(f'<div class="note" style="margin-top:1.2rem">📣 {esc(site["announcement_banner"])}</div>',
                    unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Register for classes", width="stretch"):
            st.session_state["page"] = "Register"; st.rerun()
    with col2:
        if st.button("See class timings", width="stretch"):
            st.session_state["page"] = "Classes"; st.rerun()

    section("Why learn here", site.get("why_us_heading") or "An old form, taught carefully",
            site.get("why_us_lead") or "")
    cols = st.columns(4)
    for col, item in zip(cols, site.get("why_us", [])[:4]):
        with col:
            card(item.get("icon", "✧"), item.get("title", ""), item.get("text", ""))

    # guru
    section("The guru", site.get("guru_name", ""), site.get("guru_title", ""))
    gcol1, gcol2 = st.columns([2, 1])
    with gcol1:
        for para in str(site.get("guru_bio", "")).split("\n\n"):
            if para.strip():
                st.markdown(f"<p style='color:#6d5f63;line-height:1.75'>{esc(para)}</p>",
                            unsafe_allow_html=True)
    with gcol2:
        if site.get("guru_instagram"):
            st.markdown(
                f"""<div class="card"><div class="glyph">◈</div>
<h4>Follow the journey</h4>
<p>Reels, rehearsals and performance clips.</p>
<p style="margin-top:.7rem"><a href="{esc(site['guru_instagram'])}" target="_blank">Instagram ↗</a></p></div>""",
                unsafe_allow_html=True)

    # upcoming
    events = [e for e in store.load("events", []) if e.get("published", True)]
    events.sort(key=lambda e: str(e.get("date", "")))
    upcoming = [e for e in events if str(e.get("date", "")) >= date.today().isoformat()][:3]
    if upcoming:
        section("What's next", "Upcoming performances")
        for ev in upcoming:
            d, m, _ = _nice_date(ev.get("date"))
            st.markdown(
                f"""<div class="eventrow"><div class="evdate"><div class="d">{d}</div><div class="m">{m}</div></div>
<div><h4>{esc(ev.get('title'))}</h4><p>{esc(ev.get('venue'))} — {esc(ev.get('description'))}</p></div></div>""",
                unsafe_allow_html=True)

    # testimonials
    quotes = [t for t in store.load("testimonials", []) if t.get("published", True)][:3]
    if quotes:
        section("In their words", "What families say")
        for col, q in zip(st.columns(len(quotes)), quotes):
            with col:
                st.markdown(
                    f"""<div class="quote"><p>“{esc(q.get('quote'))}”</p>
<div class="who">{esc(q.get('name'))}</div><div class="rel">{esc(q.get('relation'))}</div></div>""",
                    unsafe_allow_html=True)

    section("Ready when you are", site.get("cta_heading") or "Come and watch a class first",
            site.get("cta_lead") or "")
    if st.button("Start registration →"):
        st.session_state["page"] = "Register"; st.rerun()


# --------------------------------------------------------------------------- #
def about(site):
    section("About", "Kuchipudi, and this school")
    col1, col2 = st.columns([3, 2])
    with col1:
        for para in str(site.get("about_story", "")).split("\n\n"):
            if para.strip():
                st.markdown(f"<p style='color:#6d5f63;line-height:1.8;font-size:1.02rem'>{esc(para)}</p>",
                            unsafe_allow_html=True)
    with col2:
        items = site.get("syllabus") or []
        if items:
            st.html('<div class="card"><h4>'
                    + esc(site.get("syllabus_heading") or "The first year, roughly")
                    + "</h4>"
                    + "".join(
                        f"<p style='margin:.55rem 0'><b style='color:var(--primary)'>"
                        f"{esc(i.get('name'))}</b><br>{esc(i.get('note'))}</p>"
                        for i in items)
                    + "</div>")

    section("The guru", site.get("guru_name", ""), site.get("guru_title", ""))
    for para in str(site.get("guru_bio", "")).split("\n\n"):
        if para.strip():
            st.markdown(f"<p style='color:#6d5f63;line-height:1.8'>{esc(para)}</p>",
                        unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
def classes(site):
    section("Classes", "Batches, levels and timings",
            "Every batch is capped so corrections actually reach each student.")
    batches = store.load("batches", [])
    if not batches:
        st.info("Class details are being updated. Please check back soon.")
        return
    show_fee = site.get("show_fees_publicly", True)
    for b in batches:
        fee_html = ""
        if show_fee:
            fee_html = (f'<div style="text-align:right"><div class="price">₹{esc(b.get("fee_monthly"))}</div>'
                        f'<div style="font-size:.76rem;color:#6d5f63">per month</div></div>')
        st.markdown(
            f"""<div class="batch">
  <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap">
    <div><span class="lvl">{esc(b.get('level'))}</span>
      <h4 style="margin-top:.45rem">{esc(b.get('name'))}</h4>
      <p style="color:#6d5f63;font-size:.94rem;margin:.3rem 0 0;max-width:46rem">{esc(b.get('description'))}</p>
    </div>{fee_html}
  </div>
  <div class="meta">
    <span>🗓 {esc(b.get('days'))}</span><span>⏰ {esc(b.get('time'))}</span>
    <span>👣 {esc(b.get('age_group'))}</span><span>📍 {esc(b.get('mode'))}</span>
    <span>🎟 {esc(b.get('seats'))} seats</span>
  </div>
</div>""",
            unsafe_allow_html=True)

    if show_fee:
        section("Fees", "Simple and transparent")
        rows = [{"Batch": b.get("name"), "Monthly (₹)": b.get("fee_monthly"),
                 "Quarterly (₹)": b.get("fee_quarterly"), "Mode": b.get("mode")}
                for b in batches]
        st.dataframe(rows, width="stretch", hide_index=True)
        if site.get("fees_note"):
            st.html(f'<div class="note">{esc(site["fees_note"])}</div>')

    if st.button("Register for a batch →"):
        st.session_state["page"] = "Register"; st.rerun()


# --------------------------------------------------------------------------- #
def gallery(site):
    section("Gallery", "Moments from the studio and the stage")
    items = [g for g in store.load("gallery", []) if g.get("published", True)]
    if not items:
        st.info("Photographs will appear here soon.")
    else:
        cols = st.columns(3)
        for i, g in enumerate(items):
            with cols[i % 3]:
                if g.get("url"):
                    st.image(g["url"], width="stretch",
                             caption=g.get("caption", ""))
                else:
                    st.markdown(f'<div class="card"><h4>{esc(g.get("caption"))}</h4></div>',
                                unsafe_allow_html=True)

    if site.get("guru_instagram"):
        section("Instagram", site.get("instagram_embed_note", "From our Instagram"))
        st.markdown(f"[Open @{esc(site['guru_instagram'].rstrip('/').split('/')[-1])} on Instagram ↗]"
                    f"({esc(site['guru_instagram'])})")
    reels = [v for v in store.load("videos", [])
             if v.get("public") and "instagram.com" in str(v.get("url", ""))]
    for r in reels[:4]:
        _embed_video(r.get("url"))


# --------------------------------------------------------------------------- #
def events(site):
    section("Events", "Performances, festivals and the annual production")
    rows = [e for e in store.load("events", []) if e.get("published", True)]
    rows.sort(key=lambda e: str(e.get("date", "")), reverse=True)
    if not rows:
        st.info("No events listed yet.")
        return
    today = date.today().isoformat()
    up = [e for e in rows if str(e.get("date", "")) >= today]
    past = [e for e in rows if str(e.get("date", "")) < today]
    if up:
        st.markdown("#### Upcoming")
        for ev in sorted(up, key=lambda e: str(e.get("date"))):
            _event_row(ev)
    if past:
        st.markdown("#### Past")
        for ev in past:
            _event_row(ev)


def _event_row(ev):
    d, m, _ = _nice_date(ev.get("date"))
    st.markdown(
        f"""<div class="eventrow"><div class="evdate"><div class="d">{d}</div><div class="m">{m}</div></div>
<div><h4>{esc(ev.get('title'))}</h4>
<p><b>{esc(ev.get('venue'))}</b> — {esc(ev.get('description'))}</p></div></div>""",
        unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
def videos_public(site):
    section("Watch", "Open practice videos",
            "A few clips anyone can watch. Enrolled students get the full practice library in their portal.")
    rows = [v for v in store.load("videos", []) if v.get("public")]
    if not rows:
        st.info("Public videos will be posted soon.")
        return
    for v in rows:
        st.markdown(f"**{esc(v.get('title'))}** — {esc(v.get('description'))}")
        _embed_video(v.get("url"))
        st.markdown("---")


# --------------------------------------------------------------------------- #
def contact(site):
    section("Contact", "Come say hello")
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown(
            f"""<div class="card">
<h4>Reach us</h4>
<p style="line-height:2">📞 {esc(site.get('phone'))}<br>✉️ {esc(site.get('email'))}<br>
📍 {esc(site.get('address'))}</p>
{f'<p style="margin-top:.6rem"><a href="{esc(site["maps_url"])}" target="_blank">Open in Maps ↗</a></p>' if site.get('maps_url') else ''}
{f'<p><a href="{esc(site["guru_instagram"])}" target="_blank">Instagram ↗</a></p>' if site.get('guru_instagram') else ''}
</div>""",
            unsafe_allow_html=True)
    with col2:
        st.markdown("#### Send an enquiry")
        with st.form("enquiry_form", clear_on_submit=True):
            name = st.text_input("Your name *")
            c1, c2 = st.columns(2)
            phone = c1.text_input("Phone *")
            email = c2.text_input("Email")
            interest = st.selectbox("Interested in",
                                    ["Beginner classes", "Intermediate", "Advanced",
                                     "Online classes", "Workshop / event", "Something else"])
            msg = st.text_area("Message", height=110)
            if st.form_submit_button("Send enquiry"):
                if not name.strip() or not phone.strip():
                    st.error("Name and phone are required.")
                else:
                    store.insert("enquiries", {
                        "name": name.strip(), "phone": phone.strip(),
                        "email": email.strip(), "interest": interest,
                        "message": msg.strip(), "status": "new",
                    }, prefix="enq", message="new enquiry from website")
                    st.success("Thank you — we'll get back to you shortly.")


# --------------------------------------------------------------------------- #
def register(site):
    section("Register", "Join a batch",
            "Fill this in and we'll confirm your seat. You'll be able to log in to the "
            "student portal once your registration is approved.")
    if not site.get("registration_open", True):
        st.warning("Registrations are closed at the moment. Please use the contact form to be added to the waitlist.")
        return

    batches = store.load("batches", [])
    options = {f"{b.get('name')} — {b.get('days')} {b.get('time')}": b.get("id") for b in batches}

    with st.form("register_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Student's full name *")
        dob = c2.date_input("Date of birth", value=None, min_value=date(1940, 1, 1),
                            max_value=date.today(), format="DD/MM/YYYY")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone (WhatsApp) *")
        email = c4.text_input("Email *")
        c5, c6 = st.columns(2)
        guardian = c5.text_input("Parent / guardian name (if under 18)")
        city = c6.text_input("City")
        batch_label = st.selectbox("Preferred batch *", list(options.keys()) if options else ["—"])
        experience = st.selectbox("Previous dance experience",
                                  ["Complete beginner", "Some Kuchipudi", "Other classical form", "Advanced"])
        notes = st.text_area("Anything we should know?", height=90)
        st.markdown("**Choose a password for your student portal**")
        c7, c8 = st.columns(2)
        pw1 = c7.text_input("Password *", type="password")
        pw2 = c8.text_input("Confirm password *", type="password")
        submitted = st.form_submit_button("Submit registration")

    if submitted:
        errs = []
        if not name.strip(): errs.append("Name is required.")
        if not phone.strip(): errs.append("Phone is required.")
        if not email.strip() or "@" not in email: errs.append("A valid email is required.")
        if len(pw1) < 6: errs.append("Password must be at least 6 characters.")
        if pw1 != pw2: errs.append("Passwords do not match.")
        existing = {str(s.get("email", "")).lower() for s in store.load("students", [])}
        if email.strip().lower() in existing:
            errs.append("This email is already registered — try logging in instead.")
        if errs:
            for e in errs:
                st.error(e)
            return

        store.insert("registrations", {
            "name": name.strip(), "dob": dob.isoformat() if dob else "",
            "phone": phone.strip(), "email": email.strip().lower(),
            "guardian": guardian.strip(), "city": city.strip(),
            "batch_id": options.get(batch_label, ""), "batch_label": batch_label,
            "experience": experience, "notes": notes.strip(),
            "password": auth.hash_password(pw1), "status": "pending",
        }, prefix="reg", message="new student registration")
        st.success("Registration received. We'll confirm your seat by phone or email, "
                   "and your portal login will work as soon as it's approved.")
        st.balloons()
