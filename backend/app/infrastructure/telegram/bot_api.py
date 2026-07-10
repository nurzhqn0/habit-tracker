"""Minimal Telegram Bot API calls made directly from the API process.

The bot worker owns interactive messaging; this is only for one-shot document
delivery (exports) triggered by an HTTP request, so we call sendDocument over
httpx instead of pulling aiogram into the web process.
"""

import httpx


async def send_document(
    bot_token: str, chat_id: int, filename: str, content: bytes, caption: str | None = None
) -> str | None:
    """Sends a file to a chat. Returns None on success, an error description on failure."""
    if not bot_token:
        return "bot token not configured"
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    data = {"chat_id": str(chat_id)}
    if caption:
        data["caption"] = caption
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, data=data, files={"document": (filename, content)})
    except httpx.HTTPError as exc:
        return f"request failed: {exc}"
    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}"
    if response.status_code == 200 and body.get("ok") is True:
        return None
    return str(body.get("description") or f"HTTP {response.status_code}")
