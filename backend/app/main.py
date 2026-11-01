from uuid import uuid4
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ContentSignal API", version="0.1.0", description="API for AI video creation workflows")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ContentSignal API"}

@app.post("/api/jobs")
async def create_job(
    mode: str = Form(...),
    prompt: str = Form(""),
    file: UploadFile | None = File(default=None),
):
    if mode not in {"text", "image", "video"}:
        raise HTTPException(status_code=400, detail="Unsupported generation mode")
    if mode == "text" and not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required for text-to-video")
    if mode in {"image", "video"} and file is None:
        raise HTTPException(status_code=400, detail="A source file is required for this mode")
    if file and file.content_type not in {
        "image/png", "image/jpeg", "image/webp", "video/mp4", "video/quicktime", "video/webm"
    }:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    # Provider integration will be added in the next development phase.
    return {
        "job_id": str(uuid4()),
        "status": "provider_not_configured",
        "mode": mode,
        "message": "Request validated. Connect a video generation provider to start rendering."
    }
