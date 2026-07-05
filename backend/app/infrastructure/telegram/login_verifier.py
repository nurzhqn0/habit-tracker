"""Verification of Telegram Login Widget payloads.

See https://core.telegram.org/widgets/login#checking-authorization:
data_check_string is all received fields except `hash`, sorted alphabetically,
joined as "key=value" lines; secret key is SHA256(bot_token).
"""

import hashlib
import hmac
import time

MAX_AUTH_AGE_SECONDS = 24 * 60 * 60


def verify_telegram_auth(payload: dict[str, str | int], bot_token: str) -> bool:
    received_hash = str(payload.get("hash", ""))
    if not received_hash or not bot_token:
        return False

    fields = {k: v for k, v in payload.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))

    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        return False

    try:
        auth_date = int(payload.get("auth_date", 0))
    except (TypeError, ValueError):
        return False
    return time.time() - auth_date <= MAX_AUTH_AGE_SECONDS
