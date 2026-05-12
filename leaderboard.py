"""Leaderboard rendering: who reached each bingo category first."""
from __future__ import annotations

import streamlit as st

import firebase_client as fb

CATEGORY_ORDER = [
    ("horizontal", "Horizontal", "↔️"),
    ("vertical",   "Vertical",   "↕️"),
    ("diagonal",   "Diagonal",   "🔀"),
    ("full",       "Full Bingo", "🌟"),
]

LEADERBOARD_CSS = """
<style>
.lb-card {
    background: linear-gradient(135deg, #FFFFFF 0%, var(--pink-soft) 100%);
    border: 2px solid var(--gold);
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(236, 72, 153, 0.10);
    height: 100%;
}
.lb-card h3 {
    margin: 0 0 12px 0;
    color: var(--pink-deep);
    font-weight: 800;
    font-size: 1.05rem;
}
.lb-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 4px;
    border-bottom: 1px solid rgba(212, 175, 55, 0.18);
}
.lb-row:last-child { border-bottom: none; }
.lb-rank {
    font-weight: 800;
    min-width: 28px;
    color: var(--pink-deep);
}
.lb-rank.first { color: var(--gold); }
.lb-name { flex-grow: 1; font-weight: 700; color: var(--plum); }
.lb-time { font-size: 0.75rem; color: #8a5570; }
.lb-empty { color: #8a5570; font-style: italic; }
</style>
"""


def render_leaderboard() -> None:
    st.markdown(LEADERBOARD_CSS, unsafe_allow_html=True)
    st.markdown("<h1 class='gold-header'>🏆 Leaderboard</h1>", unsafe_allow_html=True)
    st.caption(f"Round: **{fb.get_round_name()}**")

    verified = fb.list_claims("verified")

    by_type: dict[str, list[dict]] = {k: [] for k, _, _ in CATEGORY_ORDER}
    for c in verified:
        by_type.setdefault(c["type"], []).append(c)
    for k in by_type:
        by_type[k].sort(key=lambda c: c.get("verified_at"))

    cols = st.columns(len(CATEGORY_ORDER))
    for (key, label, icon), col in zip(CATEGORY_ORDER, cols):
        with col:
            entries = by_type.get(key, [])
            rows_html = ""
            if not entries:
                rows_html = "<div class='lb-empty'>No winners yet</div>"
            else:
                for rank, claim in enumerate(entries, start=1):
                    badge = "🏆" if rank == 1 else f"#{rank}"
                    rank_cls = "first" if rank == 1 else ""
                    when = (
                        claim["verified_at"].strftime("%b %d, %H:%M")
                        if claim.get("verified_at") else "—"
                    )
                    rows_html += (
                        f"<div class='lb-row'>"
                        f"<span class='lb-rank {rank_cls}'>{badge}</span>"
                        f"<span class='lb-name'>{claim['user']}</span>"
                        f"<span class='lb-time'>{when}</span>"
                        f"</div>"
                    )
            st.markdown(
                f"<div class='lb-card'><h3>{icon} {label}</h3>{rows_html}</div>",
                unsafe_allow_html=True,
            )
