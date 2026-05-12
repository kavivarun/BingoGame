"""Bingo game — Streamlit entry point."""
from __future__ import annotations

import streamlit as st

import admin as admin_mod
import auth
import bingo_board
import firebase_client as fb
import leaderboard

st.set_page_config(page_title="Bingo", page_icon="🎯", layout="wide")
st.markdown(bingo_board.GRID_CSS, unsafe_allow_html=True)


_NAV_PAGES = ["Board", "Leaderboard"]


def _sidebar(user: str | None) -> str:
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Board"

    pages = list(_NAV_PAGES)
    if auth.is_admin():
        pages.append("Admin")
    if st.session_state.nav_page not in pages:
        st.session_state.nav_page = pages[0]

    with st.sidebar:
        st.markdown("### 🎯 Bingo")
        if user:
            st.success(f"Logged in as **{user}**")
        if auth.is_admin():
            st.info("Admin mode")

        st.markdown(
            f"<div class='round-pill'>🎀 <b>{fb.get_round_name()}</b></div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        for name in pages:
            is_current = st.session_state.nav_page == name
            if st.button(
                name,
                key=f"nav_{name}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state.nav_page = name
                st.rerun()

        with st.container(key="sidebar_logout"):
            st.divider()
            if user and st.button("Logout", key="logout_user", use_container_width=True):
                auth.logout_user()
                st.rerun()
            if auth.is_admin() and st.button(
                "Admin logout", key="logout_admin", use_container_width=True
            ):
                auth.logout_admin()
                st.rerun()

    return st.session_state.nav_page


def main() -> None:
    fb.bootstrap_tiles()
    user = auth.current_user()
    admin = auth.is_admin()

    if not user and not admin:
        auth.render_login_screen()
        return

    page = _sidebar(user)

    if page == "Board":
        if user:
            bingo_board.render_board(user)
        else:
            st.info("Login as a player to see the board.")
    elif page == "Leaderboard":
        leaderboard.render_leaderboard()
    elif page == "Admin":
        admin_mod.render_admin_panel()


if __name__ == "__main__":
    main()
