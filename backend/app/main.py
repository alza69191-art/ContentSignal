import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .comfyui import COMFYUI_URL, ComfyUIError, get_generation, submit_generation

APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(APP_DIR.parent / "data" / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "100")) * 1024 * 1024

app = FastAPI(title="ContentSignal API", version="0.4.0", description="Backend API for ContentSignal Wan 2.2 workflows")
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Development-only in-memory registry. Use persistent storage and a worker queue for production.
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
    return {"name": "ContentSignal API", "docs": "/docs", "health": "/health", "engine": "Wan 2.2 TI2V-5B GGUF via ComfyUI"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ContentSignal API", "version": app.version}


@app.post("/api/jobs", status_code=202)
async def create_job(
    mode: str = Form(...), prompt: str = Form(""),
    width: int = Form(832), height: int = Form(480), frames: int = Form(49), steps: int = Form(20),
    file: UploadFile | None = File(default=None),
):
    if mode not in {"text", "image", "video"}:
        raise HTTPException(status_code=400, detail="Unsupported generation mode")
    if mode == "text" and not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required for text-to-video")
    if mode in {"image", "video"} and file is None:
        raise HTTPException(status_code=400, detail="A source file is required for this mode")
    if mode == "video":
        raise HTTPException(status_code=501, detail="Video-to-video is not enabled in the initial Wan 2.2 TI2V-5B integration.")
    if not (256 <= width <= 1280 and 256 <= height <= 1280 and width % 16 == 0 and height % 16 == 0):
        raise HTTPException(status_code=400, detail="Width and height must be multiples of 16 between 256 and 1280.")
    if not (9 <= frames <= 121 and (frames - 1) % 4 == 0):
        raise HTTPException(status_code=400, detail="Frame count must be 4n+1 and between 9 and 121.")
    if not (1 <= steps <= 40):
        raise HTTPException(status_code=400, detail="Steps must be between 1 and 40.")

    job_id = str(uuid4())
    source_path = None
    if file is not None:
        if file.content_type not in MODE_TYPES[mode]:
            raise HTTPException(status_code=415, detail="File type does not match the selected mode")
        source_path = UPLOAD_DIR / f"{job_id}{ALLOWED_TYPES[file.content_type]}"
        size = 0
        try:
            with source_path.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
                    output.write(chunk)
        except Exception:
            source_path.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    try:
        comfy_prompt_id = await submit_generation(mode, prompt.strip(), source_path, width, height, frames, steps)
    except ComfyUIError as exc:
        if source_path:
            source_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        if source_path:
            source_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=f"Could not reach ComfyUI: {exc}") from exc

    job = {
        "job_id": job_id,
        "provider_job_id": comfy_prompt_id,
        "status": "processing",
        "mode": mode,
        "prompt": prompt.strip(),
        "width": width,
        "height": height,
        "frames": frames,
        "steps": steps,
        "source_file": source_path.name if source_path else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": "Generation queued in ComfyUI using Wan 2.2 TI2V-5B GGUF.",
        "output_files": [],
    }
    JOBS[job_id] = job
    return job


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "processing":
        try:
            result = await get_generation(job["provider_job_id"])
            job["status"] = result["status"]
            job["output_files"] = result["output_files"]
            if job["status"] == "completed":
                job["message"] = "Video generation completed."
            elif job["status"] == "failed":
                job["message"] = "ComfyUI reported a generation error."
        except httpx.HTTPError as exc:
            job["message"] = f"ComfyUI status check failed: {exc}"
    result = dict(job)
    result["output_files"] = [
        {**item, "url": f"/api/jobs/{job_id}/outputs/{index}"}
        for index, item in enumerate(job["output_files"])
    ]
    return result


@app.get("/api/jobs/{job_id}/outputs/{output_index}")
async def get_job_output(job_id: str, output_index: int):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="The video is not ready yet.")
    if output_index < 0 or output_index >= len(job["output_files"]):
        raise HTTPException(status_code=404, detail="Output file not found.")

    item = job["output_files"][output_index]
    params = {
        "filename": item["filename"],
        "subfolder": item.get("subfolder", ""),
        "type": item.get("type", "output"),
    }
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            upstream = await client.get(f"{COMFYUI_URL}/view", params=params)
            upstream.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not retrieve output from ComfyUI: {exc}") from exc

    media_type = upstream.headers.get("content-type", "video/mp4")
    return Response(
        content=upstream.content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{Path(item["filename"]).name}"'},
    )
