from __future__ import annotations

import smtplib
from email.message import EmailMessage
from os import getenv
from secrets import token_urlsafe

import bcrypt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .table import Users


def send_email(to_email: str, subject: str, body: str) -> None:
    smtp_email = getenv("MY_EMAIL")
    smtp_password = getenv("PASSWORD")
    smtp_host = getenv("HOST")
    smtp_port = getenv("PORT")

    if not all([smtp_email, smtp_password, smtp_host, smtp_port]):
        raise HTTPException(status_code=500, detail="SMTP configuration is missing")

    message = EmailMessage()
    message["From"] = smtp_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(smtp_email, smtp_password)
            smtp.send_message(message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to send verification email") from exc


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate_user(email: str, password: str, session: Session) -> Users:
    user = get_user_by_email(email, session)
    if user is None or not verify_password(password, user.password):
        # One message avoids revealing whether a specific email exists.
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


def get_user_by_email(email: str, session: Session) -> Users | None:
    return session.scalar(select(Users).where(Users.email == email.lower().strip()))


def find_user_by_id(user_id: int, session: Session) -> Users | None:
    return session.get(Users, user_id)


def create_cookie_token() -> str:
    return token_urlsafe(32)
