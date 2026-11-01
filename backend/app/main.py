import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(APP_DIR.parent / "data" / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "100")) * 1024 * 1024

app = FastAPI(title="ContentSignal API", version="0.2.0", description="Backend API for ContentSignal AI video workflows")
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Development-only in-memory registry. Replace with persistent storage and a worker queue for production.
JOBS: dict[str, dict] = {}
ALLOWED_TYPES = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
    "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
}
MODE_TYPES = {
    "image": {"image/png", "image/jpeg", "image/webp"},
    "video": {"video/mp4", "video/quicktime", "video/webm"},
}


@app.get("/")
def root():
    return {"name": "ContentSignal API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "ContentSignal API", "version": app.version}


@app.post("/api/jobs", status_code=202)
async def create_job(mode: str = Form(...), prompt: str = Form(""), file: UploadFile | None = File(default=None)):
    if mode not in {"text", "image", "video"}:
        raise HTTPException(status_code=400, detail="Unsupported generation mode")
    if mode == "text" and not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required for text-to-video")
    if mode in {"image", "video"} and file is None:
        raise HTTPException(status_code=400, detail="A source file is required for this mode")

    job_id = str(uuid4())
    stored_name = None
    if file is not None:
        if file.content_type not in MODE_TYPES[mode]:
            raise HTTPException(status_code=415, detail="File type does not match the selected mode")
        destination = UPLOAD_DIR / f"{job_id}{ALLOWED_TYPES[file.content_type]}"
        size = 0
        try:
            with destination.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await file.close()
        stored_name = destination.name

    job = {
        "job_id": job_id,
        "status": "waiting_for_provider",
        "mode": mode,
        "prompt": prompt.strip(),
        "source_file": stored_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": "Request validated and stored. A video generation provider is not configured yet.",
    }
    JOBS[job_id] = job
    return job


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
