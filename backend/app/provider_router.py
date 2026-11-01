"""Multi-provider text API router for prompt and script assistance.

Provider credentials are read only from server environment variables. Never return
credentials to the browser or commit them to the repository.
"""
import os
from typing import Any

import httpx

PROVIDERS: dict[str, dict[str, str]] = {
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
        "free_note": "قد تتوفر حصة مجانية حسب المنطقة والحساب وشروط Google الحالية.",
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
        "free_note": "توجد حدود استخدام مجانية متغيرة؛ راجع لوحة Groq.",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
        "default_model": "openrouter/free",
        "free_note": "يتوفر مسار نماذج مجانية؛ التوفر والحدود يتغيران.",
    },
}


def list_providers() -> list[dict[str, Any]]:
    """Return safe provider metadata; never expose API keys."""
    result = []
    for provider_id, config in PROVIDERS.items():
        result.append({
            "id": provider_id,
            "name": config["label"],
            "kind": "text",
            "enabled": bool(os.getenv(config["key_env"], "").strip()),
            "model": os.getenv(config["model_env"], config["default_model"]),
            "key_env": config["key_env"],
            "free_tier_note": config["free_note"],
        })
    result.append({
        "id": "wan22_local",
        "name": "Wan 2.2 TI2V-5B (ComfyUI)",
        "kind": "video",
        "enabled": True,
        "model": "Wan2.2-TI2V-5B-GGUF",
        "free_tier_note": "تشغيل محلي؛ لا توجد رسوم API، لكن يلزم GPU وملفات النموذج.",
    })
    return result


async def generate_text(provider_id: str, prompt: str, model: str | None = None) -> dict[str, Any]:
    """Call an OpenAI-compatible chat-completions API."""
    config = PROVIDERS.get(provider_id)
    if config is None:
        raise ValueError("مزود الخدمة غير مدعوم.")
    api_key = os.getenv(config["key_env"], "").strip()
    if not api_key:
        raise RuntimeError(f"لم تتم إضافة مفتاح {config['key_env']} في إعدادات الخادم.")

    selected_model = (model or os.getenv(config["model_env"], config["default_model"])).strip()
    if not selected_model or len(selected_model) > 160:
        raise ValueError("اسم النموذج غير صالح.")

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "You are a precise assistant helping create production-ready video scripts and generation prompts."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if provider_id == "openrouter":
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL", "https://contentsignal.app")
        headers["X-Title"] = "ContentSignal"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
            response = await client.post(
                f'{config["base_url"]}/chat/completions',
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            raise RuntimeError("وصل المزود إلى حد الاستخدام أو الحصة المتاحة. جرّب مزودًا آخر.") from exc
        if status in (401, 403):
            raise RuntimeError("مفتاح API غير صالح أو لا يملك صلاحية الاستخدام.") from exc
        raise RuntimeError(f"فشل مزود الخدمة (HTTP {status}).") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError("انتهت مهلة الاتصال بمزود الخدمة.") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("تعذر الاتصال بمزود الخدمة.") from exc

    choices = data.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("لم يُرجع مزود الخدمة نصًا صالحًا.")
    usage = data.get("usage") or {}
    return {
        "provider": provider_id,
        "model": selected_model,
        "text": content.strip(),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
    }
