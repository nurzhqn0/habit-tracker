"""Verification of Telegram Mini App initData.

When the web app is opened inside Telegram it receives an ``initData`` query
string (https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app).
It is signed with the bot token, so we can trust the ``user`` field without an
extra round-trip to Telegram:

    secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
    hash       = HMAC_SHA256(key=secret_key, msg=data_check_string)

The data_check_string is every field except ``hash``, sorted by key and joined
with newlines as ``key=value``.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def verify_init_data(
    init_data: str, bot_token: str, max_age_seconds: int = 86_400
) -> dict | None:
    """Returns the parsed ``user`` dict, or None if initData is invalid/stale."""
    if not init_data or not bot_token:
        return None

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        return None

    auth_date = pairs.get("auth_date")
    if not auth_date or not auth_date.isdigit():
        return None
    if time.time() - int(auth_date) > max_age_seconds:
        return None

    try:
        user = json.loads(pairs.get("user", ""))
    except ValueError:
        return None
    if not isinstance(user, dict) or not user.get("id"):
        return None
    return user
