"""Minimal Telegram Bot API calls made directly from the API process.

The bot worker owns interactive messaging; this is only for one-shot document
delivery (exports) triggered by an HTTP request, so we call sendDocument over
httpx instead of pulling aiogram into the web process.
"""

import httpx


async def send_document(
    bot_token: str, chat_id: int, filename: str, content: bytes, caption: str | None = None
) -> bool:
    """Sends a file to a chat. Returns False on any failure (incl. bot not started)."""
    if not bot_token:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    data = {"chat_id": str(chat_id)}
    if caption:
        data["caption"] = caption
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, data=data, files={"document": (filename, content)})
        return response.status_code == 200 and response.json().get("ok") is True
    except (httpx.HTTPError, ValueError):
        return False
