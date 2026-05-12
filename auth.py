"""Login, cookie session, and admin gating."""
from __future__ import annotations

import streamlit as st
from streamlit_cookies_controller import CookieController

import firebase_client as fb

SESSION_COOKIE = "bingo_session"
ADMIN_COOKIE = "bingo_admin"
COOKIE_MAX_AGE_DAYS = 30


def _cookies() -> CookieController:
    if "cookie_controller" not in st.session_state:
        st.session_state.cookie_controller = CookieController()
    return st.session_state.cookie_controller


def current_user() -> str | None:
    """Resolve the logged-in player from cookie + session state."""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    token = _cookies().get(SESSION_COOKIE)
    if not token:
        return None
    name = fb.user_by_session(token)
    if name:
        st.session_state.user = name
    return name


def is_admin() -> bool:
    if st.session_state.get("is_admin"):
        return True
    flag = _cookies().get(ADMIN_COOKIE)
    if flag == "1":
        st.session_state.is_admin = True
        return True
    return False


def login_user(name: str) -> None:
    token = fb.login_or_create_user(name)
    st.session_state.user = name
    _cookies().set(SESSION_COOKIE, token, max_age=COOKIE_MAX_AGE_DAYS * 24 * 3600)


def logout_user() -> None:
    name = st.session_state.get("user")
    if name:
        fb.clear_session(name)
    st.session_state.pop("user", None)
    _cookies().remove(SESSION_COOKIE)


def login_admin(password: str) -> bool:
    expected = st.secrets["admin"]["password"]
    if password == expected:
        st.session_state.is_admin = True
        _cookies().set(ADMIN_COOKIE, "1", max_age=COOKIE_MAX_AGE_DAYS * 24 * 3600)
        return True
    return False


def logout_admin() -> None:
    st.session_state.pop("is_admin", None)
    _cookies().remove(ADMIN_COOKIE)


def render_login_screen() -> None:
    st.markdown(
        "<h1 class='gold-header' style='font-size:3rem; text-align:center;'>🎀 Bingo Game 🏆</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#6b3b51; margin-top:-8px;'>"
        "Enter your name to start playing. Your login is remembered in this browser."
        "</p>",
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        name = st.text_input("Your name", max_chars=40)
        submitted = st.form_submit_button("Start playing", type="primary")
    if submitted:
        clean = (name or "").strip()
        if not clean:
            st.error("Please enter a name.")
        else:
            login_user(clean)
            st.rerun()

    with st.expander("Admin login"):
        with st.form("admin_login"):
            pwd = st.text_input("Admin password", type="password")
            ok = st.form_submit_button("Login as admin")
        if ok:
            if login_admin(pwd):
                st.success("Admin logged in.")
                st.rerun()
            else:
                st.error("Wrong password.")
