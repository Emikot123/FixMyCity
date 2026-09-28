from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]
    country: Mapped[str]
    city: Mapped[str]
    age: Mapped[int]
    profile_picture: Mapped[str | None] = mapped_column(nullable=True)

    posts: Mapped[list["Posts"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    liked_posts: Mapped[list["PostLike"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Posts(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    details: Mapped[str]
    image: Mapped[str | None] = mapped_column(nullable=True)
    video: Mapped[str | None] = mapped_column(nullable=True)
    country: Mapped[str]
    city: Mapped[str]
    likes: Mapped[int] = mapped_column(default=0)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["Users"] = relationship(back_populates="posts")
    liked_by: Mapped[list["PostLike"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_post_like_user_post"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)

    user: Mapped["Users"] = relationship(back_populates="liked_posts")
    post: Mapped["Posts"] = relationship(back_populates="liked_by")
