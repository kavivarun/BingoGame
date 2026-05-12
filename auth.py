"""Login, cookie session, and admin gating."""
from __future__ import annotations

import time

import streamlit as st
from streamlit_cookies_controller import CookieController

import firebase_client as fb

USER_COOKIE = "bingo_user"
ADMIN_COOKIE = "bingo_admin"
COOKIE_MAX_AGE_DAYS = 30
_COOKIE_SYNC_DELAY = 0.25


def _cookies() -> CookieController:
    # Re-instantiate every script run with a stable key so the component
    # actually re-renders and keeps pushing cookies from the browser.
    controller = CookieController(key="bingo_cookies")
    # Library bug: __cookies stays None until the frontend round-trip completes,
    # which makes .set()/.remove() crash with TypeError. Initialize to an empty
    # dict so writes succeed even on a cold render. Real cookies from the
    # frontend overwrite this on the next script run.
    if getattr(controller, "_CookieController__cookies", None) is None:
        controller._CookieController__cookies = {}
    return controller


def _wait_for_cookies(controller: CookieController) -> dict:
    """Force one wait cycle on cold load so cookies sync from the browser."""
    cookies = controller.getAll() or {}
    if cookies or st.session_state.get("_cookie_sync_done"):
        st.session_state._cookie_sync_done = True
        return cookies
    time.sleep(_COOKIE_SYNC_DELAY)
    st.session_state._cookie_sync_done = True
    st.rerun()


def current_user() -> str | None:
    """Resolve the logged-in player from cookie + session state."""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    cookies = _wait_for_cookies(_cookies())
    name = (cookies.get(USER_COOKIE) or "").strip()
    if not name:
        return None
    st.session_state.user = name
    return name


def is_admin() -> bool:
    if st.session_state.get("is_admin"):
        return True
    cookies = _wait_for_cookies(_cookies())
    if cookies.get(ADMIN_COOKIE) == "1":
        st.session_state.is_admin = True
        return True
    return False


def _set_cookie(name: str, value: str, max_age: int) -> None:
    """Write a cookie that survives Streamlit Cloud's cross-origin iframe.

    Streamlit Cloud serves the app inside a cross-origin frame, so cookies
    need ``SameSite=None; Secure`` to be allowed by browsers. Localhost is
    same-origin, but modern browsers still accept ``Secure`` there.
    """
    _cookies().set(
        name,
        value,
        max_age=max_age,
        same_site="none",
        secure=True,
    )
    # Let the cookie-set component message reach the browser before the
    # caller's st.rerun() tears down the component.
    time.sleep(0.3)


def login_user(name: str) -> None:
    fb.login_or_create_user(name)
    st.session_state.user = name
    _set_cookie(USER_COOKIE, name, COOKIE_MAX_AGE_DAYS * 24 * 3600)


def _clear_cookie(name: str) -> None:
    """Expire a cookie using the same SameSite/Secure attributes used to set it,
    otherwise the browser may not treat the new Set-Cookie as a replacement."""
    _set_cookie(name, "", max_age=0)


def logout_user() -> None:
    st.session_state.pop("user", None)
    _clear_cookie(USER_COOKIE)


def login_admin(password: str) -> bool:
    expected = st.secrets["admin"]["password"]
    if password == expected:
        st.session_state.is_admin = True
        _set_cookie(ADMIN_COOKIE, "1", COOKIE_MAX_AGE_DAYS * 24 * 3600)
        return True
    return False


def logout_admin() -> None:
    st.session_state.pop("is_admin", None)
    _clear_cookie(ADMIN_COOKIE)


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
