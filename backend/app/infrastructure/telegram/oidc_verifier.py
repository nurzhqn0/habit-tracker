"""Verification of Telegram Login OIDC id_tokens.

The new Telegram Login (https://core.telegram.org/widgets/login) returns a JWT
signed by Telegram; we verify it against their JWKS and pin issuer + audience
(audience = the bot's Client ID from BotFather -> Web Login).
"""

import jwt
from jwt import PyJWKClient

ISSUER = "https://oauth.telegram.org"
JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"

_jwks_client: PyJWKClient | None = None


def _signing_key_from_token(id_token: str):
    """Fetches the matching Telegram public key (cached). Patched in tests."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)
    return _jwks_client.get_signing_key_from_jwt(id_token).key


def verify_id_token(id_token: str, client_id: str) -> dict | None:
    """Returns the verified claims, or None if the token is invalid."""
    if not id_token or not client_id:
        return None
    try:
        key = _signing_key_from_token(id_token)
        return jwt.decode(
            id_token,
            key,
            algorithms=["RS256", "ES256"],
            audience=str(client_id),
            issuer=ISSUER,
            options={"require": ["exp", "iat", "aud", "iss"]},
        )
    except jwt.PyJWTError:
        return None
