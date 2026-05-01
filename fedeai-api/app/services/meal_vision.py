import base64
import json

import httpx

from ..config import settings


async def estimate_meal_from_image(image_bytes: bytes, caption: str | None = None) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = (
        "Estimate meal nutrition from this image. "
        "Return strict JSON with keys: meal_type, food_item, calories, protein_g, carbs_g, fat_g, notes. "
        "meal_type must be one of breakfast,lunch,dinner,snack."
    )
    if caption:
        prompt += f" Caption/context: {caption}"

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": settings.openai_vision_model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return {
        "meal_type": parsed.get("meal_type", "dinner"),
        "food_item": parsed.get("food_item", "meal photo"),
        "calories": int(parsed.get("calories", 0)),
        "protein_g": float(parsed.get("protein_g", 0)),
        "carbs_g": float(parsed.get("carbs_g", 0)),
        "fat_g": float(parsed.get("fat_g", 0)),
        "notes": parsed.get("notes", "Estimated from Telegram photo"),
    }


def estimate_meal_from_text(text: str) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    prompt = (
        "Extract a structured nutrition estimate from this user meal message. "
        "Return strict JSON with keys: meal_type, food_item, calories, protein_g, carbs_g, fat_g, notes. "
        "meal_type must be one of breakfast,lunch,dinner,snack. "
        "Use realistic macro estimates from the described foods."
    )
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": settings.openai_vision_model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{prompt}\n\nUser text: {text}"},
                ],
            }
        ],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    with httpx.Client(timeout=45) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return {
        "meal_type": parsed.get("meal_type", "lunch"),
        "food_item": parsed.get("food_item", "meal from text"),
        "calories": int(parsed.get("calories", 0)),
        "protein_g": float(parsed.get("protein_g", 0)),
        "carbs_g": float(parsed.get("carbs_g", 0)),
        "fat_g": float(parsed.get("fat_g", 0)),
        "notes": parsed.get("notes", "Estimated from user text"),
    }


def infer_tool_call_from_text(text: str) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    prompt = (
        "Map this user message to one health tool call. "
        "Return strict JSON with keys: tool, params. "
        "Allowed tools: log_food, log_weight, chart_weight, chart_macro, chart_calories, update_food, delete_food, unknown. "
        "For log_weight include weight_kg and optional log_date (YYYY-MM-DD). "
        "For chart_* include days (integer). "
        "For log_food include meal_type, food_item, calories, protein_g, carbs_g, fat_g, optional log_date (YYYY-MM-DD). "
        "For update_food include selectors (food_item_contains and/or meal_type and/or from_date) and target fields (to_date, to_meal_type). "
        "For delete_food include selectors (food_item_contains and/or meal_type and/or log_date). "
        "Interpret time references: if user says 'last night' or 'yesterday', set date to yesterday; "
        "'last monday' should become the correct past Monday date. "
        "If user gives no date, assume today. "
        "If user says 'this week', set days=7. "
        "If user says 'this month', set days=30."
    )
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": settings.openai_vision_model,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": [{"type": "text", "text": f"{prompt}\n\nUser text: {text}"}]}],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    with httpx.Client(timeout=45) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return {
        "tool": parsed.get("tool", "unknown"),
        "params": parsed.get("params", {}) or {},
    }
