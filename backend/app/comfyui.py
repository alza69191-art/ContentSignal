import json
import os
from pathlib import Path
from urllib.parse import urlencode

import httpx

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8189").rstrip("/")
COMFYUI_PUBLIC_URL = os.getenv("COMFYUI_PUBLIC_URL", COMFYUI_URL).rstrip("/")
WORKFLOW_PATH = Path(os.getenv(
    "COMFYUI_WORKFLOW_PATH",
    str(Path(__file__).resolve().parent.parent / "workflows" / "wan22_ti2v_5b_gguf_api.json"),
))
PROMPT_NODE_ID = os.getenv("COMFYUI_PROMPT_NODE_ID", "6")
IMAGE_NODE_ID = os.getenv("COMFYUI_IMAGE_NODE_ID", "56")
LATENT_NODE_ID = os.getenv("COMFYUI_LATENT_NODE_ID", "55")
PROMPT_INPUT = os.getenv("COMFYUI_PROMPT_INPUT", "text")
IMAGE_INPUT = os.getenv("COMFYUI_IMAGE_INPUT", "image")
REQUEST_TIMEOUT = float(os.getenv("COMFYUI_REQUEST_TIMEOUT", "60"))


class ComfyUIError(RuntimeError):
    pass


def _load_workflow() -> dict:
    if not WORKFLOW_PATH.is_file():
        raise ComfyUIError(f"Wan 2.2 workflow file not found: {WORKFLOW_PATH}")
    try:
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComfyUIError(f"Could not read the ComfyUI workflow: {exc}") from exc
    if not isinstance(workflow, dict):
        raise ComfyUIError("The ComfyUI API workflow must be a JSON object.")
    return workflow


async def submit_generation(
    mode: str, prompt: str, source_path: Path | None,
    width: int = 832, height: int = 480, frames: int = 49, steps: int = 20,
) -> str:
    if mode == "video":
        raise ComfyUIError(
            "Video-to-video is not enabled in this first integration. "
            "Wan 2.2 TI2V-5B is configured for text-to-video and image-to-video."
        )
    if mode not in {"text", "image"}:
        raise ComfyUIError(f"Unsupported generation mode: {mode}")
    if not prompt.strip():
        raise ComfyUIError("A prompt is required.")
    workflow = _load_workflow()
    prompt_node = workflow.get(PROMPT_NODE_ID)
    if not isinstance(prompt_node, dict) or not isinstance(prompt_node.get("inputs"), dict):
        raise ComfyUIError(f"Prompt node {PROMPT_NODE_ID} was not found in the workflow.")
    prompt_node["inputs"][PROMPT_INPUT] = prompt.strip()

    latent_node = workflow.get(LATENT_NODE_ID)
    if not isinstance(latent_node, dict) or not isinstance(latent_node.get("inputs"), dict):
        raise ComfyUIError(f"Wan latent node {LATENT_NODE_ID} was not found in the workflow.")
    latent_node["inputs"].update({"width": width, "height": height, "length": frames})
    sampler_node = workflow.get("3")
    if isinstance(sampler_node, dict) and isinstance(sampler_node.get("inputs"), dict):
        sampler_node["inputs"]["steps"] = steps

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        if mode == "image":
            if source_path is None:
                raise ComfyUIError("Image-to-video requires an uploaded source image.")
            image_node = workflow.get(IMAGE_NODE_ID)
            if not isinstance(image_node, dict) or not isinstance(image_node.get("inputs"), dict):
                raise ComfyUIError(f"Image loader node {IMAGE_NODE_ID} was not found in the workflow.")
            with source_path.open("rb") as source:
                response = await client.post(
                    f"{COMFYUI_URL}/upload/image",
                    files={"image": (source_path.name, source, "application/octet-stream")},
                    data={"type": "input", "overwrite": "true"},
                )
            response.raise_for_status()
            image_node["inputs"][IMAGE_INPUT] = response.json()["name"]
            latent_node["inputs"]["start_image"] = [IMAGE_NODE_ID, 0]
        else:
            latent_node["inputs"].pop("start_image", None)
            workflow.pop(IMAGE_NODE_ID, None)

        queued = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        queued.raise_for_status()
        result = queued.json()

    if result.get("node_errors"):
        raise ComfyUIError(f"ComfyUI rejected the workflow: {result['node_errors']}")
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise ComfyUIError(f"ComfyUI did not return a prompt_id: {result}")
    return str(prompt_id)


async def get_generation(prompt_id: str) -> dict:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
        response.raise_for_status()
        history = response.json()

    record = history.get(prompt_id)
    if not record:
        return {"status": "processing", "output_files": []}
    outputs = []
    for node_output in record.get("outputs", {}).values():
        for kind in ("videos", "gifs", "images"):
            for item in node_output.get(kind, []):
                if item.get("filename"):
                    outputs.append({
                        "filename": item["filename"],
                        "subfolder": item.get("subfolder", ""),
                        "type": item.get("type", "output"),
                        "url": f"{COMFYUI_PUBLIC_URL}/view?{urlencode(item)}",
                    })
    status = record.get("status", {})
    if status.get("status_str") == "error":
        return {"status": "failed", "output_files": outputs, "error": status.get("messages", [])}
    completed = status.get("completed", False)
    return {"status": "completed" if completed and outputs else "processing", "output_files": outputs}
