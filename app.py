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


def _sidebar(user: str | None) -> str:
    with st.sidebar:
        st.markdown("### 🎯 Bingo")
        if user:
            st.success(f"Logged in as **{user}**")
            if st.button("Logout", use_container_width=True):
                auth.logout_user()
                st.rerun()
        if auth.is_admin():
            st.info("Admin mode")
            if st.button("Admin logout", use_container_width=True):
                auth.logout_admin()
                st.rerun()

        options = ["Board", "Leaderboard"]
        if auth.is_admin():
            options.append("Admin")
        page = st.radio("Navigate", options, label_visibility="collapsed")
        st.markdown(
            f"<div class='round-pill'>🎀 <b>{fb.get_round_name()}</b></div>",
            unsafe_allow_html=True,
        )
    return page


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
