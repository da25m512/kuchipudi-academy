"""Kuchipudi dance academy — public website, student portal and admin portal.

Run locally:   streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from lib import auth, seed, store, ui
from views import admin, public
from views import student as student_view

st.set_page_config(
    page_title="Kuchipudi Academy",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PUBLIC_PAGES = ["Home", "About", "Classes", "Videos", "Gallery",
                "Events", "Contact", "Register"]


def bootstrap():
    """Make sure every table exists with sensible defaults."""
    if st.session_state.get("_bootstrapped"):
        return store.load("site", seed.SITE)
    site = store.load("site", seed.SITE)
    if isinstance(site, dict):
        merged = dict(seed.SITE)
        merged.update(site)
        if merged != site:
            store.save("site", merged, "merge new site fields")
        site = merged
    store.load("batches", seed.BATCHES)
    store.load("testimonials", seed.TESTIMONIALS)
    store.load("events", seed.EVENTS)
    store.load("videos", seed.VIDEOS)
    store.load("announcements", seed.ANNOUNCEMENTS)
    for table in ("students", "attendance", "fees", "gallery",
                  "enquiries", "registrations"):
        store.load(table, [])
    auth.admin_users()
    st.session_state["_bootstrapped"] = True
    return site


def navbar(site):
    page = st.session_state.get("page", "Home")
    cols = st.columns(len(PUBLIC_PAGES) + 2, gap="small")
    for col, name in zip(cols, PUBLIC_PAGES):
        with col:
            if st.button(name, key=f"nav_{name}", width="stretch",
                         type="primary" if page == name else "secondary"):
                st.session_state["page"] = name
                st.rerun()
    with cols[-2]:
        label = "My portal" if auth.is_student() else "Student"
        if st.button(label, key="nav_student", width="stretch",
                     type="primary" if page == "Student" else "secondary"):
            st.session_state["page"] = "Student"
            st.rerun()
    with cols[-1]:
        if st.button("Admin", key="nav_admin", width="stretch",
                     type="primary" if page == "Admin" else "secondary"):
            st.session_state["page"] = "Admin"
            st.rerun()


def sidebar(site):
    with st.sidebar:
        st.markdown(f"### {site.get('academy_name','')}")
        st.caption(site.get("tagline", ""))
        st.markdown("---")
        user = auth.current_user()
        if user:
            st.markdown(f"Signed in as **{user.get('name') or user.get('username')}**  \n"
                        f"_{auth.role()}_")
            if st.button("Sign out", width="stretch"):
                auth.logout()
                st.session_state["page"] = "Home"
                st.rerun()
        else:
            st.caption("Not signed in.")
        st.markdown("---")
        st.caption(f"Data store: {store.storage_mode()}")
        if st.button("Reload data", width="stretch"):
            store.refresh()
            st.rerun()


def main():
    site = bootstrap()
    ui.inject_css(site.get("primary_color", "#7B1E3C"),
                  site.get("accent_color", "#C9A227"))
    ui.brandbar(site)
    navbar(site)
    sidebar(site)
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    page = st.session_state.get("page", "Home")

    if page == "Home":
        public.home(site)
    elif page == "About":
        public.about(site)
    elif page == "Classes":
        public.classes(site)
    elif page == "Videos":
        public.videos_public(site)
    elif page == "Gallery":
        public.gallery(site)
    elif page == "Events":
        public.events(site)
    elif page == "Contact":
        public.contact(site)
    elif page == "Register":
        public.register(site)
    elif page == "Student":
        if auth.is_student():
            student_view.portal(site)
        else:
            student_view.login_panel(site)
    elif page == "Admin":
        if auth.is_admin():
            admin.portal(site)
        else:
            admin.login_panel(site)
    else:
        public.home(site)

    ui.footer(site)


if __name__ == "__main__":
    main()
