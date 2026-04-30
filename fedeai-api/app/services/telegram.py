import httpx

from ..config import settings


async def send_telegram_message(chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(url, json=payload)


async def get_file_bytes(file_id: str) -> bytes:
    info_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getFile"
    async with httpx.AsyncClient(timeout=30) as client:
        info_resp = await client.get(info_url, params={"file_id": file_id})
        info_resp.raise_for_status()
        info = info_resp.json()
        file_path = info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
        file_resp = await client.get(file_url)
        file_resp.raise_for_status()
        return file_resp.content
