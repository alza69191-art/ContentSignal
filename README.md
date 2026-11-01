# ContentSignal

ContentSignal is an AI video creation web app. Its initial generation engine is **Wan 2.2 TI2V-5B in GGUF format**, run by ComfyUI and controlled through FastAPI.

## Included generation paths

- **Text to Video:** supported by the bundled workflow.
- **Image to Video:** supported by the same Wan 2.2 TI2V-5B workflow.
- **Video to Video:** disabled in this first release; it needs a different model/workflow.

The repository includes a ready-to-use ComfyUI API workflow at `backend/workflows/wan22_ti2v_5b_gguf_api.json`. It uses the GGUF loader node from [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF). The default starting resolution is 832×480 at 49 frames to reduce GPU memory pressure; adjust it after confirming the available VRAM.

## Required model files

Put these files in the matching ComfyUI model folders:

| File | ComfyUI folder |
|---|---|
| `Wan2.2-TI2V-5B-Q4_K_M.gguf` | `models/unet/` (GGUF loader's UNet folder) |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `models/text_encoders/` |
| `wan2.2_vae.safetensors` | `models/vae/` |

Install the GGUF custom node and its dependency, then restart ComfyUI:

~~~bash
cd ComfyUI/custom_nodes
git clone https://github.com/city96/ComfyUI-GGUF
pip install -r ComfyUI-GGUF/requirements.txt
~~~

Make sure the model filename in the workflow matches the exact filename visible in ComfyUI. If yours differs, edit the `unet_name` value in the workflow JSON.

## Connect the app to ComfyUI

1. Start ComfyUI with its API listening on port 8189, for example: `python main.py --listen 0.0.0.0 --port 8189`.
2. Set `COMFYUI_URL` to the address reachable from the FastAPI container.
3. Keep the bundled workflow path and node IDs unless you replace the workflow.

For Docker Desktop, `host.docker.internal:8189` usually reaches ComfyUI running on the host. If ComfyUI runs in another container, use its Compose service name. Never expose the ComfyUI API publicly without a secure private network or authenticated proxy.

Generated videos are served through the FastAPI output endpoint, so the user's browser does not need direct access to ComfyUI's port.

## Run the web app and API

Requirements: Docker Desktop with Docker Compose, Node 20+ for local frontend development, Python 3.10+ for local backend development.

~~~bash
docker compose up --build
~~~

Open:
- Web app: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## API endpoints

- `GET /health` — API health.
- `POST /api/jobs` — multipart form with `mode=text` or `mode=image`, `prompt`, and an image file for image mode.
- `GET /api/jobs/{job_id}` — checks ComfyUI and returns job status and output metadata.
- `GET /api/jobs/{job_id}/outputs/{index}` — streams the generated output through FastAPI.

Jobs are stored in memory for this initial integration and reset when the API restarts. Uploaded files are stored in the backend volume. This is an integration package, not a hosted GPU service: ComfyUI, the model weights, and a GPU runtime must be running separately.

## Before production

Add persistent job storage, a background queue, user authentication, quotas, secure object storage, file signature validation, monitoring, and rate limiting. Do not commit model weights, user uploads, or credentials.
