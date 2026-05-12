# 🎯 Bingo Game (Streamlit + Firebase)

A multiplayer photo-bingo app. Players log in with just a name (persisted via browser cookie), tap any of the 16 tiles on a 4×4 board to upload a photo from their camera or gallery, and race to complete bingo lines. A single admin account verifies bingo claims and can reset the game.

Win categories tracked on the leaderboard:
- **Horizontal** (any of 4 rows)
- **Vertical** (any of 4 columns)
- **Diagonal** (either of the 2 diagonals)
- **Full bingo** (all 16 tiles)

The first verified claim in each category gets the 🏆 badge.

---

## 1. Local setup

```bash
python -m venv .venv
. .venv/Scripts/activate         # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

## 2. Firebase setup (one-time)

1. Go to <https://console.firebase.google.com/> and create a new project.
2. **Build → Firestore Database → Create database** → Production mode → pick a region.
3. **Build → Storage → Get started** → keep the default rules for now.
4. **Project settings (⚙) → Service accounts → Generate new private key.** A JSON file downloads.
5. **Build → Storage → Files** — copy the bucket name shown at the top (after `gs://`). Newer projects (created after Oct 2024) use `<project-id>.firebasestorage.app`; older ones use `<project-id>.appspot.com`. Use whatever the console actually shows.

### Firestore security note
For a small private game with trusted players, the default Storage rules are fine. For public/internet deployments, lock Storage and Firestore so only the service account can read/write (the app uses the service account credentials directly).

## 3. Configure secrets

Copy the example file and fill it in:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` and:
- set `[admin] password` to anything you like
- set `[firebase] storage_bucket` to the bucket name from step 5 above (e.g., `your-project-id.firebasestorage.app`)
- paste each field from the Firebase service-account JSON into `[firebase.service_account]`

`.streamlit/secrets.toml` is gitignored — never commit it.

## 4. Run locally

```bash
streamlit run app.py
```

Visit <http://localhost:8501>. Log in with any name. Open the sidebar → **Admin** isn't visible until you log in as admin from the login screen's "Admin login" expander.

## 5. Customize the tiles

Edit [tiles.json](tiles.json) before first run, or use **Admin → Edit tiles** in the running app to update them live (saves to Firestore).

## 6. Deploy to Streamlit Cloud

1. Push this repo to GitHub (public or private both work).
2. Sign in to <https://share.streamlit.io>, click **New app**, point it at your repo, main file `app.py`.
3. In **App settings → Secrets**, paste the same contents as your local `.streamlit/secrets.toml`.
4. Click **Deploy**. First boot takes ~2 min.
5. After deploy, open the public URL on your phone — camera input opens the device camera.

### Reboot persistence check
After deploying, go to **Manage app → Reboot**. After reboot, all uploaded images and progress should still be there (they live in Firebase, not on the Streamlit container).

---

## How a player uses it

1. Open the app, type a name, hit **Start playing**.
2. Tap any tile → choose **Camera** or **Gallery** → submit.
3. As soon as you complete a row/column/diagonal/full, a **pending claim** is automatically filed for the admin to verify.
4. Watch the **Leaderboard** to see who's winning each category.

## How the admin uses it

1. From the login screen, expand **Admin login** and enter the password from `secrets.toml`.
2. **Pending claims** tab — review the 4 tile photos for each claim, approve or reject.
3. **All submissions** — browse every photo, filter by user.
4. **Edit tiles** — change the 16 tasks live (validated as JSON with exactly 16 entries indexed 0–15).
5. **Reset game** — archives the round and gives everyone a fresh empty board.

---

## Project layout

| File | Purpose |
|------|---------|
| [app.py](app.py) | Streamlit entry point, sidebar nav |
| [auth.py](auth.py) | Cookie-based player session + admin gating |
| [firebase_client.py](firebase_client.py) | All Firestore + Storage I/O |
| [bingo_board.py](bingo_board.py) | 4×4 grid + upload dialog (camera + gallery) |
| [bingo_logic.py](bingo_logic.py) | Pure bingo-pattern detection |
| [leaderboard.py](leaderboard.py) | Per-category rankings |
| [admin.py](admin.py) | Verify claims, edit tiles, reset game |
| [tiles.json](tiles.json) | Default 16-task board (seeded on first run) |

## Testing

Logic-only unit tests (no Firebase needed):

```bash
pip install pytest
pytest test_bingo_logic.py
```
