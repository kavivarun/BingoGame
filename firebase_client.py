"""Firebase initialization and helpers for Firestore + Storage.

All app state lives here so we can run on Streamlit Cloud's ephemeral filesystem.
"""
from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter
from PIL import Image, ImageOps

TILES_JSON_PATH = Path(__file__).parent / "tiles.json"
MAX_IMAGE_EDGE = 1024
JPEG_QUALITY = 80


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _init_firebase() -> firebase_admin.App:
    """Initialize Firebase once per Streamlit process."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    sa_info = dict(st.secrets["firebase"]["service_account"])
    bucket_name = st.secrets["firebase"]["storage_bucket"]
    cred = credentials.Certificate(sa_info)
    return firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})


def db():
    _init_firebase()
    return firestore.client()


def bucket():
    _init_firebase()
    return storage.bucket()


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------

def get_game_state() -> dict:
    doc = db().collection("game_state").document("current").get()
    if doc.exists:
        return doc.to_dict()
    initial = {
        "round_id": "r1",
        "round_name": "Round 1",
        "started_at": datetime.now(timezone.utc),
        "reset_count": 0,
    }
    db().collection("game_state").document("current").set(initial)
    return initial


def get_round_id() -> str:
    return get_game_state()["round_id"]


def get_round_name() -> str:
    state = get_game_state()
    return state.get("round_name") or state["round_id"]


def reset_game(round_name: str | None = None) -> tuple[str, str]:
    """Archive current round and start a new one.

    Returns (new_round_id, new_round_name).
    """
    state = get_game_state()
    old_round = state["round_id"]
    new_count = state.get("reset_count", 0) + 1
    new_round = f"r{new_count + 1}"
    new_name = (round_name or "").strip() or f"Round {new_count + 1}"

    db().collection("rounds_history").document(old_round).set({
        "archived_at": datetime.now(timezone.utc),
        "previous_state": state,
    })

    _delete_collection_where("submissions", "round_id", "==", old_round)
    _delete_collection_where("claims", "round_id", "==", old_round)

    db().collection("game_state").document("current").set({
        "round_id": new_round,
        "round_name": new_name,
        "started_at": datetime.now(timezone.utc),
        "reset_count": new_count,
    })
    return new_round, new_name


def rename_current_round(round_name: str) -> None:
    name = (round_name or "").strip()
    if not name:
        return
    db().collection("game_state").document("current").update({"round_name": name})


def _delete_collection_where(name: str, field: str, op: str, value: Any, batch_size: int = 100) -> None:
    coll = db().collection(name)
    flt = FieldFilter(field, op, value)
    docs = list(coll.where(filter=flt).limit(batch_size).stream())
    while docs:
        batch = db().batch()
        for d in docs:
            batch.delete(d.reference)
        batch.commit()
        docs = list(coll.where(filter=flt).limit(batch_size).stream())


# ---------------------------------------------------------------------------
# Tiles
# ---------------------------------------------------------------------------

def bootstrap_tiles() -> None:
    """If tiles/current doesn't exist, seed it from tiles.json."""
    ref = db().collection("tiles").document("current")
    if ref.get().exists:
        return
    data = json.loads(TILES_JSON_PATH.read_text(encoding="utf-8"))
    ref.set(data)


def get_tiles() -> list[dict]:
    bootstrap_tiles()
    doc = db().collection("tiles").document("current").get()
    return doc.to_dict()["tasks"]


def save_tiles(tasks: list[dict]) -> None:
    db().collection("tiles").document("current").set({
        "round_id": get_round_id(),
        "tasks": tasks,
    })


# ---------------------------------------------------------------------------
# Users / sessions
# ---------------------------------------------------------------------------

def login_or_create_user(name: str) -> str:
    """Create user if missing, set a new session token, return the token."""
    name = name.strip()
    token = uuid.uuid4().hex
    ref = db().collection("users").document(name)
    snap = ref.get()
    if snap.exists:
        ref.update({"session_token": token, "last_login_at": datetime.now(timezone.utc)})
    else:
        ref.set({
            "name": name,
            "joined_at": datetime.now(timezone.utc),
            "last_login_at": datetime.now(timezone.utc),
            "session_token": token,
        })
    return token


def user_by_session(token: str) -> str | None:
    """Return username for a valid session token, or None."""
    if not token:
        return None
    docs = (
        db().collection("users")
        .where(filter=FieldFilter("session_token", "==", token))
        .limit(1)
        .stream()
    )
    for d in docs:
        return d.to_dict()["name"]
    return None


def clear_session(name: str) -> None:
    db().collection("users").document(name).update({"session_token": ""})


def list_users() -> list[str]:
    return [d.id for d in db().collection("users").stream()]


# ---------------------------------------------------------------------------
# Submissions (uploaded tiles)
# ---------------------------------------------------------------------------

def _submission_id(round_id: str, user: str, tile_index: int) -> str:
    return f"{round_id}__{user}__{tile_index}"


def upload_submission(user: str, tile_index: int, image_bytes: bytes, content_type: str) -> dict:
    """Compress, upload to Storage, write submission doc, return the doc data."""
    round_id = get_round_id()
    compressed = _compress_image(image_bytes)
    path = f"games/{round_id}/{user}/tile_{tile_index}.jpg"

    blob = bucket().blob(path)
    blob.upload_from_string(compressed, content_type="image/jpeg")

    data = {
        "user": user,
        "round_id": round_id,
        "tile_index": tile_index,
        "image_path": path,
        "uploaded_at": datetime.now(timezone.utc),
    }
    db().collection("submissions").document(_submission_id(round_id, user, tile_index)).set(data)
    return data


def get_user_submissions(user: str) -> dict[int, dict]:
    round_id = get_round_id()
    q = (
        db().collection("submissions")
        .where(filter=FieldFilter("round_id", "==", round_id))
        .where(filter=FieldFilter("user", "==", user))
    )
    out: dict[int, dict] = {}
    for d in q.stream():
        sub = d.to_dict()
        out[sub["tile_index"]] = sub
    return out


def list_all_submissions() -> list[dict]:
    round_id = get_round_id()
    q = db().collection("submissions").where(filter=FieldFilter("round_id", "==", round_id))
    return [d.to_dict() for d in q.stream()]


@st.cache_data(show_spinner=False, ttl=300)
def signed_url(path: str) -> str:
    """Short-lived signed URL for displaying an image."""
    blob = bucket().blob(path)
    return blob.generate_signed_url(expiration=timedelta(hours=1), version="v4", method="GET")


def _compress_image(raw: bytes) -> bytes:
    img = Image.open(io.BytesIO(raw))
    # Bake the EXIF orientation into the pixels so the saved JPEG renders
    # right-side-up regardless of how the phone was held.
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, MAX_IMAGE_EDGE / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Claims (bingo wins, pending or verified)
# ---------------------------------------------------------------------------

def _claim_id(round_id: str, user: str, claim_type: str, line_id: str) -> str:
    return f"{round_id}__{user}__{claim_type}__{line_id}"


def create_claim(user: str, claim_type: str, line_indices: list[int], line_id: str) -> None:
    round_id = get_round_id()
    cid = _claim_id(round_id, user, claim_type, line_id)
    db().collection("claims").document(cid).set({
        "user": user,
        "round_id": round_id,
        "type": claim_type,
        "line_id": line_id,
        "line_indices": line_indices,
        "claimed_at": datetime.now(timezone.utc),
        "status": "pending",
        "verified_at": None,
        "verified_by": None,
    })


def get_user_claims(user: str) -> list[dict]:
    round_id = get_round_id()
    q = (
        db().collection("claims")
        .where(filter=FieldFilter("round_id", "==", round_id))
        .where(filter=FieldFilter("user", "==", user))
    )
    return [d.to_dict() | {"_id": d.id} for d in q.stream()]


def list_claims(status: str | None = None) -> list[dict]:
    round_id = get_round_id()
    q = db().collection("claims").where(filter=FieldFilter("round_id", "==", round_id))
    if status:
        q = q.where(filter=FieldFilter("status", "==", status))
    return [d.to_dict() | {"_id": d.id} for d in q.stream()]


def verify_claim(claim_id: str, approve: bool, admin_label: str = "admin") -> None:
    db().collection("claims").document(claim_id).update({
        "status": "verified" if approve else "rejected",
        "verified_at": datetime.now(timezone.utc),
        "verified_by": admin_label,
    })


def line_ids_already_claimed(user: str) -> set[tuple[str, str]]:
    """Return {(type, line_id)} for claims the user already has (any status)."""
    return {(c["type"], c["line_id"]) for c in get_user_claims(user)}
