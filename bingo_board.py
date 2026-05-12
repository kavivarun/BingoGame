"""4x4 grid renderer + upload dialog for the logged-in player."""
from __future__ import annotations

import streamlit as st

import bingo_logic
import firebase_client as fb

GRID_CSS = """
<style>
:root {
    --pink:        #EC4899;
    --pink-deep:   #BE185D;
    --pink-soft:   #FFE4F0;
    --pink-bg:     #FFF8FB;
    --gold:        #D4AF37;
    --gold-bright: #F5C842;
    --gold-soft:   #FFF3C4;
    --plum:        #3D0F26;
}

/* Headers + accents */
h1.gold-header {
    background: linear-gradient(90deg, var(--gold) 0%, var(--pink) 60%, var(--pink-deep) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-weight: 800;
    letter-spacing: 0.5px;
}

.round-pill {
    margin-top: 12px;
    padding: 10px 14px;
    border-radius: 14px;
    text-align: center;
    background: linear-gradient(135deg, var(--pink-soft) 0%, var(--gold-soft) 100%);
    border: 1.5px solid var(--gold);
    color: var(--plum);
    font-size: 0.95rem;
}

.board-title {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin: 4px 0 18px 0;
}
.board-title h2 {
    background: linear-gradient(90deg, var(--pink-deep), var(--gold));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin: 0;
    font-weight: 800;
}
.board-title .round-name {
    color: var(--plum);
    font-weight: 600;
    opacity: 0.75;
}

.progress-strip {
    background: var(--pink-soft);
    border-radius: 999px;
    height: 10px;
    overflow: hidden;
    margin: 4px 0 18px 0;
}
.progress-strip > div {
    height: 100%;
    background: linear-gradient(90deg, var(--pink), var(--gold-bright));
    border-radius: 999px;
}

/* Tile card */
.tile-card {
    position: relative;
    aspect-ratio: 1 / 1;
    border-radius: 18px;
    overflow: hidden;
    border: 2px solid var(--pink-soft);
    background: white;
    box-shadow: 0 2px 8px rgba(236, 72, 153, 0.08);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    margin-bottom: 6px;
}
.tile-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(236, 72, 153, 0.20);
}

.tile-card.empty {
    background: linear-gradient(135deg, #FFFFFF 0%, var(--pink-soft) 100%);
    border-style: dashed;
    border-color: var(--pink);
}

.tile-card.uploaded { border-color: var(--gold); }
.tile-card.pending  { border-color: var(--gold-bright); box-shadow: 0 0 0 3px rgba(245, 200, 66, 0.25); }
.tile-card.verified {
    border-color: var(--gold);
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.35), 0 6px 18px rgba(236, 72, 153, 0.25);
}

.tile-card img.tile-photo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* Empty-state body */
.tile-empty-body {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 14px;
    color: var(--plum);
}
.tile-empty-body .num {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--pink-deep);
    letter-spacing: 1px;
}
.tile-empty-body .title {
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.25;
    margin-top: 6px;
}
.tile-empty-body .desc {
    font-size: 0.82rem;
    color: #6b3b51;
    line-height: 1.35;
    margin-top: 6px;
    flex-grow: 1;
}
.tile-empty-body .cam {
    font-size: 0.82rem;
    color: var(--pink);
    font-weight: 600;
    text-align: right;
}

/* Image overlays */
.tile-overlay-top {
    position: absolute;
    top: 8px;
    left: 8px;
    right: 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 6px;
}
.tile-badge {
    background: rgba(61, 15, 38, 0.72);
    color: white;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    backdrop-filter: blur(6px);
    letter-spacing: 0.4px;
}
.tile-state {
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--plum);
}
.tile-state.uploaded { background: var(--gold-soft); color: var(--pink-deep); }
.tile-state.pending  { background: var(--gold-bright); color: var(--plum); }
.tile-state.verified { background: var(--gold); color: white; box-shadow: 0 2px 6px rgba(212,175,55,0.5); }

.tile-overlay-bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 18px 12px 10px 12px;
    background: linear-gradient(0deg, rgba(61, 15, 38, 0.85) 0%, rgba(61, 15, 38, 0) 100%);
    color: white;
    font-weight: 600;
    font-size: 0.85rem;
    line-height: 1.2;
}

/* Buttons under tiles */
div[data-testid="stButton"] > button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
"""


def _tile_state(idx: int, submissions: dict[int, dict], claims: list[dict]) -> str:
    in_verified = any(c["status"] == "verified" and idx in c["line_indices"] for c in claims)
    if in_verified:
        return "verified"
    in_pending = any(c["status"] == "pending" and idx in c["line_indices"] for c in claims)
    if in_pending:
        return "pending"
    if idx in submissions:
        return "uploaded"
    return "empty"


def render_board(user: str) -> None:
    tiles = fb.get_tiles()
    submissions = fb.get_user_submissions(user)
    claims = fb.get_user_claims(user)

    completed = set(submissions.keys())
    if completed:
        existing = fb.line_ids_already_claimed(user)
        new_lines = bingo_logic.detect_new_lines(completed, existing)
        for line in new_lines:
            fb.create_claim(user, line.type, list(line.indices), line.line_id)
        if new_lines:
            claims = fb.get_user_claims(user)
            for line in new_lines:
                st.toast(f"🎉 New {line.type} bingo submitted for verification!", icon="🎯")

    st.markdown(
        f"""
        <div class="board-title">
            <h2>{user}'s Bingo Board</h2>
            <span class="round-name">· {fb.get_round_name()}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pct = int(round(len(completed) / 16 * 100))
    st.markdown(
        f"""
        <div class="progress-strip"><div style="width:{pct}%"></div></div>
        <div style="text-align:right; font-size:0.82rem; color:#6b3b51; margin-bottom:14px;">
            {len(completed)} / 16 tiles uploaded · {pct}%
        </div>
        """,
        unsafe_allow_html=True,
    )

    for row in range(4):
        cols = st.columns(4, gap="small")
        for col in range(4):
            idx = row * 4 + col
            tile = tiles[idx]
            state = _tile_state(idx, submissions, claims)
            with cols[col]:
                _render_tile(user, tile, state, submissions.get(idx))


_STATE_LABELS = {
    "uploaded": "✓ Uploaded",
    "pending":  "⏳ Pending",
    "verified": "🏆 Verified",
}


def _render_tile(user: str, tile: dict, state: str, submission: dict | None) -> None:
    idx = tile["index"]

    if submission:
        url = fb.signed_url(submission["image_path"])
        state_class = state if state in _STATE_LABELS else "uploaded"
        state_label = _STATE_LABELS[state_class]
        html = (
            f'<div class="tile-card {state}">'
            f'  <img class="tile-photo" src="{url}" alt="tile {idx}" />'
            f'  <div class="tile-overlay-top">'
            f'    <span class="tile-badge">#{idx + 1}</span>'
            f'    <span class="tile-state {state_class}">{state_label}</span>'
            f'  </div>'
            f'  <div class="tile-overlay-bottom">{tile["title"]}</div>'
            f'</div>'
        )
    else:
        html = (
            f'<div class="tile-card empty">'
            f'  <div class="tile-empty-body">'
            f'    <div>'
            f'      <div class="num">TILE #{idx + 1}</div>'
            f'      <div class="title">{tile["title"]}</div>'
            f'      <div class="desc">{tile["description"]}</div>'
            f'    </div>'
            f'    <div class="cam">📷 Tap below to upload</div>'
            f'  </div>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)

    label = "Replace photo" if submission else "Upload photo"
    if st.button(label, key=f"open_{idx}", use_container_width=True):
        st.session_state[f"dialog_open_{idx}"] = True

    if st.session_state.get(f"dialog_open_{idx}"):
        _upload_dialog(user, tile)


@st.dialog("Upload proof")
def _upload_dialog(user: str, tile: dict) -> None:
    idx = tile["index"]
    st.markdown(f"### #{idx + 1} · {tile['title']}")
    st.caption(tile["description"])

    tab_cam, tab_file = st.tabs(["📷 Camera", "🖼️ Gallery"])
    image_bytes: bytes | None = None
    content_type = "image/jpeg"

    with tab_cam:
        cam = st.camera_input("Take a photo", key=f"cam_{idx}")
        if cam is not None:
            image_bytes = cam.getvalue()
            content_type = cam.type or "image/jpeg"

    with tab_file:
        up = st.file_uploader(
            "Choose an image",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"file_{idx}",
        )
        if up is not None:
            image_bytes = up.getvalue()
            content_type = up.type or "image/jpeg"
            st.image(image_bytes, caption="Preview", use_container_width=True)

    col_a, col_b = st.columns(2)
    if col_a.button("Submit", type="primary", disabled=image_bytes is None, key=f"submit_{idx}"):
        fb.upload_submission(user, idx, image_bytes, content_type)
        st.session_state[f"dialog_open_{idx}"] = False
        fb.signed_url.clear()
        st.rerun()
    if col_b.button("Cancel", key=f"cancel_{idx}"):
        st.session_state[f"dialog_open_{idx}"] = False
        st.rerun()
