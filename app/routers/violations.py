from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/violations")

_last_count = 0


@router.get("/latest")
def latest_violation():
    global _last_count

    folder = Path("violations")

    if not folder.exists():
        return {"new": False, "count": 0, "image_url": None}

    files = sorted(
        folder.glob("*.jpg"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    current = len(files)
    is_new = current > _last_count
    _last_count = current

    if not files:
        return {"new": False, "count": 0, "image_url": None}

    latest_file = files[0].name

    return {
        "new": is_new,
        "count": current,
        "image_url": f"http://localhost:8000/violations/{latest_file}"
    }