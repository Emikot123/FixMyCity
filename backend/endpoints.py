from __future__ import annotations

from contextlib import asynccontextmanager
from os import getenv
from secrets import randbelow
from time import monotonic
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .database import Base, engine, ensure_legacy_columns, get_session
from .extra import (
    authenticate_user,
    create_cookie_token,
    find_user_by_id,
    get_user_by_email,
    hash_password,
    send_email,
)
from .image import (
    IMAGE_TYPES,
    MAX_PROFILE_BYTES,
    delete_media_file,
    media_file_response,
    save_post_video,
    save_profile_picture_bytes,
)
from .schemas import CreateUser, PostResponse, UpdatePost, UpdateUser, UserResponse, UserSummary
from .table import PostLike, Posts, Users

VERIFICATION_TTL_SECONDS = 10 * 60
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
COOKIE_SECURE = getenv("COOKIE_SECURE", "false").lower() == "true"

sessions: dict[str, int] = {}
pending_signups: dict[str, dict] = {}
pending_logins: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    ensure_legacy_columns()
    yield


app = FastAPI(title="FixMyCity API", version="1.0.0", lifespan=lifespan)

origins = [
    origin.strip()
    for origin in getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def generate_code() -> int:
    return 100000 + randbelow(900000)


def validate_pending(pending: dict | None, code: int, missing_message: str) -> dict:
    if pending is None:
        raise HTTPException(status_code=404, detail=missing_message)
    if monotonic() > pending["expires"]:
        raise HTTPException(status_code=410, detail="Verification code expired")
    if pending["code"] != code:
        raise HTTPException(status_code=400, detail="Incorrect verification code")
    return pending


def set_session_cookie(response: Response, user_id: int) -> None:
    token = create_cookie_token()
    sessions[token] = user_id
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=SESSION_MAX_AGE_SECONDS,
        path="/",
    )


def require_user_id(token: str | None) -> int:
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    user_id = sessions.get(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user_id


def optional_user_id(token: str | None) -> int | None:
    return sessions.get(token) if token else None


def user_to_response(user: Users) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        country=user.country,
        city=user.city,
        age=user.age,
        profile_picture_url=f"/users/{user.id}/image" if user.profile_picture else None,
    )


def post_to_response(post: Posts, viewer_id: int | None, liked_ids: set[int] | None = None) -> PostResponse:
    liked = post.id in liked_ids if liked_ids is not None else False
    return PostResponse(
        id=post.id,
        title=post.title,
        details=post.details,
        country=post.country,
        city=post.city,
        likes=post.likes or 0,
        liked_by_me=liked if viewer_id else False,
        video_url=f"/posts/{post.id}/video",
        user=UserSummary(
            id=post.user.id,
            username=post.user.username,
            profile_picture_url=f"/users/{post.user.id}/image" if post.user.profile_picture else None,
        ),
    )


def get_liked_post_ids(session: Session, viewer_id: int | None, post_ids: list[int]) -> set[int]:
    if not viewer_id or not post_ids:
        return set()
    return set(
        session.scalars(
            select(PostLike.post_id).where(
                PostLike.user_id == viewer_id,
                PostLike.post_id.in_(post_ids),
            )
        ).all()
    )


@app.get("/")
def root():
    return {"name": "FixMyCity API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", status_code=202)
async def register(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    country: str = Form(...),
    city: str = Form(...),
    age: int = Form(...),
    profile_picture: UploadFile | None = File(None),
    session: Session = Depends(get_session),
):
    email = normalize_email(email)
    if get_user_by_email(email, session):
        raise HTTPException(status_code=409, detail="Email already registered")

    profile_bytes: bytes | None = None
    profile_content_type: str | None = None
    if profile_picture is not None:
        profile_content_type = profile_picture.content_type or ""
        if profile_content_type not in IMAGE_TYPES:
            raise HTTPException(status_code=415, detail="Profile picture must be PNG, JPG, or WEBP")
        profile_bytes = await profile_picture.read(MAX_PROFILE_BYTES + 1)
        await profile_picture.close()
        if len(profile_bytes) > MAX_PROFILE_BYTES:
            raise HTTPException(status_code=413, detail="Profile picture is too large")

    try:
        user_data = CreateUser(
            username=username.strip(),
            password=password,
            email=email,
            country=country.strip(),
            city=city.strip(),
            age=age,
            profile_picture=None,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    code = generate_code()
    pending_signups[email] = {
        "code": code,
        "expires": monotonic() + VERIFICATION_TTL_SECONDS,
        "user": user_data.model_dump(exclude={"profile_picture"}),
        "profile_bytes": profile_bytes,
        "profile_content_type": profile_content_type,
    }

    send_email(email, "FixMyCity verification", f"Your verification code is: {code}")
    return {"detail": "Verification code sent", "email": email}


@app.post("/auth/verify_signup", response_model=UserResponse)
async def verify_signup(
    response: Response,
    email: str = Form(...),
    code: int = Form(...),
    session: Session = Depends(get_session),
):
    email = normalize_email(email)
    pending = validate_pending(
        pending_signups.get(email),
        code,
        "No pending signup found for this email",
    )

    data = pending["user"]
    user = Users(
        username=data["username"],
        email=email,
        password=hash_password(data["password"]),
        country=data["country"],
        city=data["city"],
        age=data["age"],
        profile_picture=None,
    )

    try:
        session.add(user)
        session.flush()
        if pending["profile_bytes"] is not None:
            user.profile_picture = await save_profile_picture_bytes(
                user.id,
                pending["profile_bytes"],
                pending["profile_content_type"],
            )
        session.commit()
        session.refresh(user)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from exc

    pending_signups.pop(email, None)
    set_session_cookie(response, user.id)
    return user_to_response(user)


@app.post("/auth/login", status_code=202)
def login(
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    email = normalize_email(email)
    user = authenticate_user(email, password, session)
    code = generate_code()
    pending_logins[email] = {
        "code": code,
        "expires": monotonic() + VERIFICATION_TTL_SECONDS,
        "user_id": user.id,
    }
    send_email(email, "FixMyCity login verification", f"Your verification code is: {code}")
    return {"detail": "Verification code sent", "email": email}


@app.post("/auth/verify_login", response_model=UserResponse)
def verify_login(
    response: Response,
    email: str = Form(...),
    code: int = Form(...),
    session: Session = Depends(get_session),
):
    email = normalize_email(email)
    pending = validate_pending(
        pending_logins.get(email),
        code,
        "No pending login found for this email",
    )

    user = find_user_by_id(pending["user_id"], session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    pending_logins.pop(email, None)
    set_session_cookie(response, user.id)
    return user_to_response(user)


@app.post("/auth/logout")
def logout(
    response: Response,
    token: Annotated[str | None, Cookie()] = None,
):
    if token:
        sessions.pop(token, None)
    response.delete_cookie("token", path="/")
    return {"detail": "Logged out"}


@app.get("/me", response_model=UserResponse)
def get_me(
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    user = find_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@app.patch("/me", response_model=UserResponse)
def update_me(
    update: UpdateUser,
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    user = find_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip()
        setattr(user, field, value)

    session.commit()
    session.refresh(user)
    return user_to_response(user)


@app.get("/users/{user_id}/image")
def get_user_image(user_id: int, session: Session = Depends(get_session)):
    user = find_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return media_file_response(user.profile_picture, not_found="Profile picture not found")


@app.get("/me/image")
def get_my_image(
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    user = find_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return media_file_response(user.profile_picture, not_found="Profile picture not found")


@app.get("/posts", response_model=list[PostResponse])
def list_posts(
    token: Annotated[str | None, Cookie()] = None,
    limit: int = 30,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    posts = session.scalars(
        select(Posts)
        .where(Posts.video.is_not(None))
        .options(selectinload(Posts.user))
        .order_by(Posts.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    viewer_id = optional_user_id(token)
    liked_ids = get_liked_post_ids(session, viewer_id, [post.id for post in posts])
    return [post_to_response(post, viewer_id, liked_ids) for post in posts]


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    post = session.scalar(
        select(Posts).where(Posts.id == post_id).options(selectinload(Posts.user))
    )
    if post is None or not post.video:
        raise HTTPException(status_code=404, detail="Post not found")

    viewer_id = optional_user_id(token)
    liked_ids = get_liked_post_ids(session, viewer_id, [post.id])
    return post_to_response(post, viewer_id, liked_ids)


@app.get("/posts/{post_id}/video")
def get_post_video(post_id: int, session: Session = Depends(get_session)):
    post = session.get(Posts, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return media_file_response(post.video, not_found="Video not found")


@app.post("/me/posts", response_model=PostResponse, status_code=201)
@app.post("/me/post", response_model=PostResponse, status_code=201, include_in_schema=False)
async def create_post(
    title: str = Form(...),
    details: str = Form(...),
    video: UploadFile = File(...),
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    user = find_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    title = title.strip()
    details = details.strip()
    if not 1 <= len(title) <= 80:
        raise HTTPException(status_code=422, detail="Title must contain 1 to 80 characters")
    if not 1 <= len(details) <= 2000:
        raise HTTPException(status_code=422, detail="Details must contain 1 to 2000 characters")

    post = Posts(
        title=title,
        details=details,
        image=None,
        video=None,
        country=user.country,
        city=user.city,
        likes=0,
        user_id=user.id,
    )
    session.add(post)
    session.flush()

    video_path: str | None = None
    try:
        video_path = await save_post_video(user.id, post.id, video)
        post.video = video_path
        session.commit()
        session.refresh(post)
        post.user = user
    except Exception:
        session.rollback()
        delete_media_file(video_path)
        raise

    return post_to_response(post, user.id, set())


@app.get("/me/posts", response_model=list[PostResponse])
def get_my_posts(
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    posts = session.scalars(
        select(Posts)
        .where(Posts.user_id == user_id, Posts.video.is_not(None))
        .options(selectinload(Posts.user))
        .order_by(Posts.id.desc())
    ).all()
    liked_ids = get_liked_post_ids(session, user_id, [post.id for post in posts])
    return [post_to_response(post, user_id, liked_ids) for post in posts]


@app.patch("/me/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    update: UpdatePost,
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    post = session.scalar(
        select(Posts).where(Posts.id == post_id).options(selectinload(Posts.user))
    )
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can edit only your own posts")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(post, field, value.strip() if isinstance(value, str) else value)

    session.commit()
    session.refresh(post)
    liked_ids = get_liked_post_ids(session, user_id, [post.id])
    return post_to_response(post, user_id, liked_ids)


@app.delete("/me/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    post = session.get(Posts, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can delete only your own posts")

    video_path = post.video
    image_path = post.image
    session.delete(post)
    session.commit()
    delete_media_file(video_path)
    delete_media_file(image_path)
    return Response(status_code=204)


@app.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session),
):
    user_id = require_user_id(token)
    post = session.get(Posts, post_id)
    if post is None or not post.video:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = session.scalar(
        select(PostLike).where(
            PostLike.user_id == user_id,
            PostLike.post_id == post_id,
        )
    )

    if existing:
        session.delete(existing)
        post.likes = max((post.likes or 0) - 1, 0)
        liked = False
    else:
        session.add(PostLike(user_id=user_id, post_id=post_id))
        post.likes = (post.likes or 0) + 1
        liked = True

    session.commit()
    return {"liked": liked, "likes": post.likes}
