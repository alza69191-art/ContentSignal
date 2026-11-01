# ContentSignal

**ContentSignal** is a web-based AI video creation workspace. The backend includes a ComfyUI integration bridge for open-source **Wan 2.2 TI2V-5B** workflows.

## Generation engine

- **Text to Video:** Wan 2.2 TI2V-5B.
- **Image to Video:** Wan 2.2 TI2V-5B.
- **Video to Video:** not enabled in this first integration; it requires a separate compatible workflow/model.
- ComfyUI runs the model; FastAPI submits jobs and checks their status.

Wan 2.2 TI2V-5B supports text-to-video and image-to-video. The upstream project documents 720p at 24 FPS. Actual speed and feasible resolution depend on GPU memory, quantization, and workflow settings.

## Connect ComfyUI

1. Install and run ComfyUI on a machine with a supported NVIDIA GPU.
2. Install/download the Wan 2.2 TI2V-5B model files and load the matching workflow.
3. In ComfyUI, export the workflow using **Save (API Format)**.
4. Place the exported JSON at `backend/workflows/wan22_ti2v_5b_api.json` (create the folder if needed).
5. Identify the prompt node ID/input key and image node ID/input key in the exported JSON.
6. Set these variables in `backend/.env` or the API container environment: `COMFYUI_URL`, `COMFYUI_WORKFLOW_PATH`, `COMFYUI_PROMPT_NODE_ID`, `COMFYUI_PROMPT_INPUT`, `COMFYUI_IMAGE_NODE_ID`, and `COMFYUI_IMAGE_INPUT`.

The API-format workflow is deployment-specific because node IDs and input names differ. Never expose ComfyUI directly to the public internet; keep it on a private network and authenticate the ContentSignal API.

For Docker Desktop, `host.docker.internal` usually lets the API container reach ComfyUI running on the host. If ComfyUI runs in another container, use its Compose service name.

## Run the app

Requirements: Docker Desktop with the Compose plugin.

~~~bash
docker compose up --build
~~~

Open:
- Web app: http://localhost:3000
- API health: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs

For local development, use Python 3.10+ and Node.js 20+. Install backend dependencies with `pip install -r backend/requirements.txt`, then run `uvicorn app.main:app --app-dir backend --reload`. Run the frontend with `cd frontend && npm install && npm run dev`.

## API

- `GET /health` — API health.
- `POST /api/jobs` — multipart form: `mode=text|image`, `prompt`, and an image `file` for image mode.
- `GET /api/jobs/{job_id}` — refreshes ComfyUI job state and returns generated output file metadata.

Jobs are currently stored in memory and reset when the API restarts. Uploaded inputs are stored on disk. The API returns ComfyUI output URLs; configure browser access to the ComfyUI host, or add an authenticated output proxy/object-storage layer before public deployment.

## Current limitations and production work

- This is an integration bridge, not a hosted GPU service. ComfyUI and Wan weights must be running and configured separately.
- The exported API workflow must use the configured node IDs and input names.
- The first integration supports text-to-video and image-to-video only.
- Add a persistent database, background queue, authentication, per-user quotas, secure object storage, output proxying, upload signature validation, and monitoring before production use.
- Do not commit model weights, workflow secrets, or credentials.
