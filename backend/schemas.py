from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field

ValidID = Annotated[int, Field(gt=0)]


class CreateUser(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=30)]
    email: Annotated[str, Field(min_length=4, max_length=100)]
    password: Annotated[str, Field(min_length=6, max_length=72)]
    country: Annotated[str, Field(min_length=2, max_length=80)]
    city: Annotated[str, Field(min_length=1, max_length=80)]
    age: Annotated[int, Field(ge=13, le=120)]
    profile_picture: Any = None


class UpdateUser(BaseModel):
    username: Annotated[str | None, Field(min_length=3, max_length=30)] = None
    country: Annotated[str | None, Field(min_length=2, max_length=80)] = None
    city: Annotated[str | None, Field(min_length=1, max_length=80)] = None


class UpdatePost(BaseModel):
    title: Annotated[str | None, Field(min_length=1, max_length=80)] = None
    details: Annotated[str | None, Field(min_length=1, max_length=2000)] = None


class UserSummary(BaseModel):
    id: ValidID
    username: str
    profile_picture_url: str | None = None


class UserResponse(BaseModel):
    id: ValidID
    username: str
    email: str
    country: str
    city: str
    age: int
    profile_picture_url: str | None = None


class PostResponse(BaseModel):
    id: ValidID
    title: str
    details: str
    country: str
    city: str
    likes: int
    liked_by_me: bool = False
    video_url: str
    user: UserSummary
