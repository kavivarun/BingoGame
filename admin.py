"""Admin panel: verify bingo claims, edit tiles, reset game."""
from __future__ import annotations

import json

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import firebase_client as fb

_ADMIN_POLL_MS = 30_000


def render_admin_panel() -> None:
    st_autorefresh(interval=_ADMIN_POLL_MS, key="admin_poll")
    st.title("🔧 Admin Panel")
    st.caption(f"Current round: **{fb.get_round_name()}** (`{fb.get_round_id()}`)")

    tab_claims, tab_subs, tab_tiles, tab_reset = st.tabs(
        ["Pending claims", "All submissions", "Edit tiles", "Reset game"]
    )

    with tab_claims:
        _render_pending_claims()
    with tab_subs:
        _render_all_submissions()
    with tab_tiles:
        _render_edit_tiles()
    with tab_reset:
        _render_reset()


def _render_pending_claims() -> None:
    pending = fb.list_claims("pending")
    if not pending:
        st.success("Nothing pending. 🎉")
        return

    pending.sort(key=lambda c: c.get("claimed_at"))
    submissions = {(s["user"], s["tile_index"]): s for s in fb.list_all_submissions()}
    tiles = fb.get_tiles()

    for claim in pending:
        with st.container(border=True):
            st.markdown(
                f"**{claim['user']}** claimed a **{claim['type']}** bingo "
                f"(`{claim['line_id']}`) at "
                f"{claim['claimed_at'].strftime('%Y-%m-%d %H:%M')}"
            )
            cols = st.columns(len(claim["line_indices"]))
            for col, idx in zip(cols, claim["line_indices"]):
                sub = submissions.get((claim["user"], idx))
                with col:
                    st.markdown(f"**#{idx} · {tiles[idx]['title']}**")
                    if sub:
                        st.image(fb.signed_url(sub["image_path"]), use_container_width=True)
                    else:
                        st.warning("No image found.")

            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("✅ Approve", key=f"appr_{claim['_id']}", type="primary"):
                fb.verify_claim(claim["_id"], approve=True)
                st.rerun()
            if c2.button("❌ Reject", key=f"rej_{claim['_id']}"):
                fb.verify_claim(claim["_id"], approve=False)
                st.rerun()


def _render_all_submissions() -> None:
    subs = fb.list_all_submissions()
    if not subs:
        st.write("_No submissions yet._")
        return

    users = sorted({s["user"] for s in subs})
    selected = st.selectbox("Filter by user", ["(all)"] + users)
    filtered = subs if selected == "(all)" else [s for s in subs if s["user"] == selected]
    filtered.sort(key=lambda s: (s["user"], s["tile_index"]))

    tiles = fb.get_tiles()
    cols_per_row = 4
    for i in range(0, len(filtered), cols_per_row):
        row = filtered[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, sub in zip(cols, row):
            with col:
                idx = sub["tile_index"]
                st.markdown(f"**{sub['user']}** · #{idx} {tiles[idx]['title']}")
                st.image(fb.signed_url(sub["image_path"]), use_container_width=True)
                st.caption(sub["uploaded_at"].strftime("%Y-%m-%d %H:%M"))


def _render_edit_tiles() -> None:
    current = {"round_id": fb.get_round_id(), "tasks": fb.get_tiles()}
    text = st.text_area(
        "Tile JSON (16 tasks, indices 0-15)",
        value=json.dumps(current, indent=2),
        height=500,
        key="tiles_editor",
    )
    if st.button("Save tiles", type="primary"):
        try:
            parsed = json.loads(text)
            tasks = parsed["tasks"]
            if len(tasks) != 16:
                raise ValueError(f"Expected 16 tasks, got {len(tasks)}")
            indices = sorted(t["index"] for t in tasks)
            if indices != list(range(16)):
                raise ValueError("Tile indices must be exactly 0..15")
            for t in tasks:
                if "title" not in t or "description" not in t:
                    raise ValueError("Each tile needs title and description")
            fb.save_tiles(tasks)
            st.success("Saved.")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")


def _render_reset() -> None:
    st.subheader("Rename current round")
    current_name = fb.get_round_name()
    new_name = st.text_input(
        "Round name",
        value=current_name,
        max_chars=60,
        help="Shown to players at the top of the board and on the leaderboard.",
    )
    if st.button("Save name", key="save_round_name"):
        fb.rename_current_round(new_name)
        st.success("Round renamed.")
        st.rerun()

    st.divider()
    st.subheader("Start a new round")
    st.warning(
        "Starting a new round archives the current round and clears all submissions and claims. "
        "Players will see fresh empty boards."
    )
    next_name = st.text_input(
        "Name for the next round",
        placeholder="e.g. Summer Adventure, Birthday Bingo, Week 2…",
        max_chars=60,
        key="next_round_name",
    )
    confirm = st.text_input('Type "RESET" to confirm')
    if st.button("Start new round", type="primary", disabled=confirm != "RESET"):
        new_round, name = fb.reset_game(next_name)
        st.success(f"New round started: **{name}** (`{new_round}`)")
        st.rerun()
