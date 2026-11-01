import json
import os
from pathlib import Path
from urllib.parse import urlencode

import httpx

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8189").rstrip("/")
COMFYUI_PUBLIC_URL = os.getenv("COMFYUI_PUBLIC_URL", COMFYUI_URL).rstrip("/")
WORKFLOW_PATH = Path(os.getenv("COMFYUI_WORKFLOW_PATH", ""))
PROMPT_NODE_ID = os.getenv("COMFYUI_PROMPT_NODE_ID", "")
IMAGE_NODE_ID = os.getenv("COMFYUI_IMAGE_NODE_ID", "")
PROMPT_INPUT = os.getenv("COMFYUI_PROMPT_INPUT", "text")
IMAGE_INPUT = os.getenv("COMFYUI_IMAGE_INPUT", "image")
REQUEST_TIMEOUT = float(os.getenv("COMFYUI_REQUEST_TIMEOUT", "60"))


class ComfyUIError(RuntimeError):
    pass


def _load_workflow() -> dict:
    if not WORKFLOW_PATH.is_file():
        raise ComfyUIError("COMFYUI_WORKFLOW_PATH must point to an API-format workflow JSON.")
    try:
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComfyUIError(f"Could not read the ComfyUI workflow: {exc}") from exc
    if not isinstance(workflow, dict):
        raise ComfyUIError("The ComfyUI workflow must be a JSON object.")
    return workflow


async def submit_generation(mode: str, prompt: str, source_path: Path | None) -> str:
    if mode == "video":
        raise ComfyUIError("Wan 2.2 TI2V-5B supports text-to-video and image-to-video. Video-to-video needs a separate compatible workflow.")
    if not PROMPT_NODE_ID:
        raise ComfyUIError("Set COMFYUI_PROMPT_NODE_ID to the prompt node in your API workflow.")
    workflow = _load_workflow()
    prompt_node = workflow.get(PROMPT_NODE_ID)
    if not isinstance(prompt_node, dict) or not isinstance(prompt_node.get("inputs"), dict):
        raise ComfyUIError(f"Prompt node {PROMPT_NODE_ID} was not found in the workflow.")
    prompt_node["inputs"][PROMPT_INPUT] = prompt

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        if mode == "image":
            if source_path is None or not IMAGE_NODE_ID:
                raise ComfyUIError("Image-to-video requires a source image and COMFYUI_IMAGE_NODE_ID.")
            image_node = workflow.get(IMAGE_NODE_ID)
            if not isinstance(image_node, dict) or not isinstance(image_node.get("inputs"), dict):
                raise ComfyUIError(f"Image node {IMAGE_NODE_ID} was not found in the workflow.")
            with source_path.open("rb") as source:
                response = await client.post(
                    f"{COMFYUI_URL}/upload/image",
                    files={"image": (source_path.name, source, "application/octet-stream")},
                    data={"type": "input", "overwrite": "true"},
                )
            response.raise_for_status()
            image_node["inputs"][IMAGE_INPUT] = response.json()["name"]
        queued = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        queued.raise_for_status()
        result = queued.json()

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
    completed = record.get("status", {}).get("completed", False)
    return {"status": "completed" if completed and outputs else "processing", "output_files": outputs}
