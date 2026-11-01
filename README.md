# ContentSignal

**ContentSignal** is a web-based AI video creation workspace. The starter release provides a responsive Arabic-first interface and a FastAPI backend for three workflows:

- **Text to Video** — submit a text prompt.
- **Image to Video** — upload an image and describe the motion.
- **Video to Video** — upload a source video and describe the transformation.

## Current status

This repository contains the application foundation, request validation, upload storage, and job-status endpoints. **Video rendering is not active yet**: no generation provider or model has been connected. A submitted job is marked `waiting_for_provider`, not falsely reported as rendered.

The initial job registry is in memory and resets when the API restarts. Uploaded files are stored in a Docker volume when using Compose. This is a development foundation, not a production deployment.

## Run with Docker

Requirements: Docker Desktop with the Compose plugin.

```bash
docker compose up --build
```

Then open:
- Web app: http://localhost:3000
- API health: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs

Stop with `Ctrl+C`; run `docker compose down` to stop and remove containers. Uploaded files remain in the named volume unless it is explicitly removed.

## Run without Docker

### Backend

Python 3.10+ is required.

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

Node.js 20+ is recommended.

```bash
cd frontend
npm install
```

Copy `.env.example` to `.env.local` if you need a custom API URL. Then run:

```bash
npm run dev
```

Open http://localhost:3000.

## API

- `GET /health` — service health.
- `POST /api/jobs` — multipart form with `mode` (`text`, `image`, or `video`), optional `prompt`, and required `file` for image/video modes.
- `GET /api/jobs/{job_id}` — read the current in-memory job record.

Uploads are limited to 100 MB by default. Configure `MAX_UPLOAD_MB`, `UPLOAD_DIR`, and `CORS_ORIGINS` through environment variables. The API checks declared MIME types; production must additionally inspect file signatures, scan uploads, enforce authentication/quotas, and use persistent job storage.

## Next engineering milestones

1. Select a video generation provider/model and verify its API, pricing, and regional availability.
2. Add background workers and persistent job state (Redis + database).
3. Add authentication, user quotas, project history, and secure object storage.
4. Add render progress, output playback, and download handling.
5. Add production monitoring, rate limits, and deployment configuration.

Never commit API keys. Use environment variables or a managed secrets service.
