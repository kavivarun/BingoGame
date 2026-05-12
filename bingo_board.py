"""4x4 grid renderer + upload dialog for the logged-in player."""
from __future__ import annotations

import html as html_lib

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
    padding: 2px 7px;
    border-radius: 999px;
    font-size: 0.6rem;
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

/* Info icon + description overlay on empty tiles */
.tile-info {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.95);
    border: 1.5px solid var(--pink);
    color: var(--pink-deep);
    font-family: Georgia, 'Times New Roman', serif;
    font-style: italic;
    font-weight: 800;
    font-size: 0.78rem;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: help;
    z-index: 4;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    user-select: none;
}
.tile-info:hover,
.tile-info:focus {
    background: var(--pink);
    color: white;
    border-color: var(--pink-deep);
    outline: none;
}

.tile-desc-overlay {
    position: absolute;
    inset: 0;
    background: rgba(61, 15, 38, 0.94);
    color: white;
    padding: 14px;
    border-radius: inherit;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.18s ease, visibility 0.18s ease;
    z-index: 3;
    pointer-events: none;
}
.tile-desc-overlay span {
    font-size: 0.8rem;
    line-height: 1.4;
    font-weight: 500;
    display: -webkit-box;
    -webkit-line-clamp: 7;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.tile-info:hover ~ .tile-desc-overlay,
.tile-info:focus ~ .tile-desc-overlay {
    opacity: 1;
    visibility: visible;
}

/* Buttons under tiles */
div[data-testid="stButton"] > button {
    border-radius: 12px;
    font-weight: 600;
}

/* Smaller text on the upload/replace photo buttons under each tile. */
[data-testid="stColumn"]:has(.tile-card) [data-testid="stButton"] > button,
div[class*="st-key-board_row_"] [data-testid="stButton"] > button {
    font-size: 0.68rem !important;
    padding: 2px 6px !important;
    min-height: 0 !important;
    line-height: 1.2 !important;
    height: auto !important;
}
[data-testid="stColumn"]:has(.tile-card) [data-testid="stButton"] > button p,
[data-testid="stColumn"]:has(.tile-card) [data-testid="stButton"] > button div,
div[class*="st-key-board_row_"] [data-testid="stButton"] > button p,
div[class*="st-key-board_row_"] [data-testid="stButton"] > button div {
    font-size: 0.68rem !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
@media (max-width: 640px) {
    [data-testid="stColumn"]:has(.tile-card) [data-testid="stButton"] > button,
    div[class*="st-key-board_row_"] [data-testid="stButton"] > button {
        font-size: 0.5rem !important;
        padding: 2px 3px !important;
    }
    [data-testid="stColumn"]:has(.tile-card) [data-testid="stButton"] > button p,
    [data-testid="stColumn"]:has(.tile-card) [data-testid="stButton"] > button div,
    div[class*="st-key-board_row_"] [data-testid="stButton"] > button p,
    div[class*="st-key-board_row_"] [data-testid="stButton"] > button div {
        font-size: 0.55rem !important;
    }
}

/* Pin the logout group to the bottom of the sidebar viewport when there is room. */
section[data-testid="stSidebar"] div[class*="st-key-sidebar_logout"] {
    position: sticky;
    bottom: 0;
    margin-top: 12px;
}

/* Force a 4-wide grid on every screen size for the board rows. */
div[class*="st-key-board_row_"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px;
}
div[class*="st-key-board_row_"] [data-testid="stColumn"] {
    flex: 1 1 0 !important;
    width: 25% !important;
    min-width: 0 !important;
}

/* Compact tile content on phones. */
@media (max-width: 640px) {
    .board-title h2 { font-size: 1.15rem; }
    .board-title .round-name { font-size: 0.8rem; }

    .tile-card { border-radius: 12px; border-width: 1.5px; }
    .tile-empty-body {
        padding: 6px;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .tile-empty-body .num { font-size: 0.5rem; letter-spacing: 0.3px; }
    .tile-empty-body .title {
        font-size: 0.65rem;
        line-height: 1.1;
        margin-top: 2px;
    }
    .tile-empty-body .desc { display: none; }
    .tile-empty-body .cam { display: none; }

    .tile-info {
        width: 16px;
        height: 16px;
        font-size: 0.55rem;
        top: 4px;
        right: 4px;
        border-width: 1px;
    }
    .tile-desc-overlay { padding: 5px; }
    .tile-desc-overlay span {
        font-size: 0.55rem;
        line-height: 1.25;
        -webkit-line-clamp: 6;
    }

    .tile-badge { padding: 2px 5px; font-size: 0.5rem; letter-spacing: 0; }
    .tile-state { padding: 2px 5px; font-size: 0.5rem; }
    .tile-overlay-top { top: 4px; left: 4px; right: 4px; gap: 2px; }
    .tile-overlay-bottom { padding: 10px 5px 3px; font-size: 0.55rem; }

    /* Hide the (invisible) overlay button label entirely on touch — taps still work. */
    div[class*="st-key-tile_"] div[data-testid="stButton"] { height: 100%; }

    /* Shrink the upload-photo dialog UI on mobile. */
    [data-testid="stFileUploader"] label { font-size: 0.8rem; }
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"] {
        padding: 0.4rem 0.6rem;
        min-height: auto;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] { padding: 0; }
    [data-testid="stFileUploaderDropzoneInstructions"] > div,
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        font-size: 0.7rem;
        line-height: 1.2;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        font-size: 0.6rem;
    }
    [data-testid="stFileUploader"] button {
        font-size: 0.75rem;
        padding: 0.25rem 0.6rem;
    }
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
        with st.container(key=f"board_row_{row}"):
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
    desc = html_lib.escape(tile["description"])

    if submission:
        url = fb.signed_url(submission["image_path"])
        state_class = state if state in _STATE_LABELS else "uploaded"
        state_label = _STATE_LABELS[state_class]
        tile_html = (
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
        tile_html = (
            f'<div class="tile-card empty">'
            f'  <span class="tile-info" tabindex="0">i</span>'
            f'  <div class="tile-desc-overlay"><span>{desc}</span></div>'
            f'  <div class="tile-empty-body">'
            f'    <div>'
            f'      <div class="num">TILE #{idx + 1}</div>'
            f'      <div class="title">{tile["title"]}</div>'
            f'    </div>'
            f'    <div class="cam">📷 Tap below to upload</div>'
            f'  </div>'
            f'</div>'
        )
    st.markdown(tile_html, unsafe_allow_html=True)

    label = "Replace photo" if submission else "Upload photo"
    if st.button(label, key=f"open_{idx}", use_container_width=True):
        st.session_state.open_dialog_idx = idx

    if st.session_state.get("open_dialog_idx") == idx:
        _upload_dialog(user, tile)


def _upload_dialog(user: str, tile: dict) -> None:
    idx = tile["index"]

    @st.dialog(f"Upload — Tile #{idx + 1}")
    def _impl() -> None:
        st.markdown(f"### {tile['title']}")
        st.caption(tile["description"])

        image_bytes: bytes | None = None
        content_type = "image/jpeg"

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
            st.session_state.open_dialog_idx = None
            fb.signed_url.clear()
            st.rerun()
        if col_b.button("Cancel", key=f"cancel_{idx}"):
            st.session_state.open_dialog_idx = None
            st.rerun()

    _impl()
