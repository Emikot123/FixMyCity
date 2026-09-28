from __future__ import annotations

from os import getenv
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEDIA_ROOT = Path(getenv("MEDIA_ROOT", PROJECT_ROOT / "media")).expanduser().resolve()
PFP = MEDIA_ROOT / "pfp"
VIDEOS = MEDIA_ROOT / "videos"

PFP.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
}

MAX_PROFILE_BYTES = 5 * 1024 * 1024
MAX_VIDEO_BYTES = int(getenv("MAX_VIDEO_MB", "150")) * 1024 * 1024


async def _save_upload(upload: UploadFile, destination: Path, max_bytes: int) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    output.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Uploaded file is too large")
                output.write(chunk)
    finally:
        await upload.close()

    return str(destination)


async def save_profile_picture(user_id: int, upload: UploadFile) -> str:
    extension = IMAGE_TYPES.get(upload.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="Profile picture must be PNG, JPG, or WEBP")

    folder = PFP / str(user_id)
    for old_file in folder.glob("avatar.*") if folder.exists() else []:
        old_file.unlink(missing_ok=True)

    return await _save_upload(upload, folder / f"avatar{extension}", MAX_PROFILE_BYTES)


async def save_profile_picture_bytes(user_id: int, image: bytes, content_type: str) -> str:
    extension = IMAGE_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(status_code=415, detail="Profile picture must be PNG, JPG, or WEBP")
    if len(image) > MAX_PROFILE_BYTES:
        raise HTTPException(status_code=413, detail="Profile picture is too large")

    folder = PFP / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"avatar{extension}"
    path.write_bytes(image)
    return str(path)


async def save_post_video(user_id: int, post_id: int, upload: UploadFile) -> str:
    extension = VIDEO_TYPES.get(upload.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=415,
            detail="Video must be MP4, WEBM, MOV, or MKV",
        )

    destination = VIDEOS / str(user_id) / f"{post_id}{extension}"
    return await _save_upload(upload, destination, MAX_VIDEO_BYTES)


def delete_media_file(path: str | None) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def media_file_response(path: str | None, *, not_found: str) -> FileResponse:
    if not path:
        raise HTTPException(status_code=404, detail=not_found)

    file_path = Path(path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=not_found)

    return FileResponse(file_path)
