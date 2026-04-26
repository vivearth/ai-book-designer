from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import get_settings

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/{filename}")
def get_upload(filename: str):
    if "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    settings = get_settings()
    path = settings.upload_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Upload not found")
    return FileResponse(path)
