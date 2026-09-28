# FixMyCity

FixMyCity is a FastAPI + React app where users can create an account, verify login/sign-up by email, publish city issue videos, browse the public feed, like reports, and manage their own posts.

## What is included

### Backend

- FastAPI API
- SQLAlchemy models
- PostgreSQL support through `DB_URL`
- SQLite fallback for quick local development
- Email verification for sign-up and login
- HTTP-only cookie sessions
- Profile pictures
- Video upload and streaming
- Public video feed
- Like/unlike
- Edit/delete ownership checks
- CORS configuration for the React development server

### Frontend

- React + Vite
- Feed
- Sign up
- Email verification
- Log in / log out
- Create video post
- Profile page
- Delete own posts
- Like/unlike

The UI is intentionally simple so the project stays easy to understand and extend.

## 1. Backend setup

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the environment template:

```bash
cp backend/.env.example backend/.env
```

Set the SMTP values in `backend/.env`. For PostgreSQL, set `DB_URL`. If `DB_URL` is left unset/blank, remove the `DB_URL=` line completely so the SQLite fallback is used.

Run the backend from the project root:

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`.

## 2. Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend defaults to `http://localhost:8000`. If your API uses another address, copy `frontend/.env.example` to `frontend/.env` and change `VITE_API_URL`.

## Storage

Uploaded files are stored under:

```text
media/
  pfp/
  videos/
```

Set `MEDIA_ROOT` in `backend/.env` if you want them elsewhere.

## Important development note

Sessions and pending email verification codes are currently kept in server memory. That is fine for this project stage, but a production deployment should move them to Redis or another shared store. A backend restart currently logs users out and clears unverified codes.
