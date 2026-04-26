from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import get_settings

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{filename}")
def download_export(filename: str):
    settings = get_settings()
    path = settings.export_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Export not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)
