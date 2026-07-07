"""Verification of Telegram Login OIDC id_tokens.

The new Telegram Login (https://core.telegram.org/widgets/login) returns a JWT
signed by Telegram; we verify it against their JWKS and pin issuer + audience
(audience = the bot's Client ID from BotFather -> Web Login).
"""

import httpx
import jwt
from jwt import PyJWKClient

ISSUER = "https://oauth.telegram.org"
JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"
TOKEN_URL = "https://oauth.telegram.org/token"

_jwks_client: PyJWKClient | None = None


def _signing_key_from_token(id_token: str):
    """Fetches the matching Telegram public key (cached). Patched in tests."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)
    return _jwks_client.get_signing_key_from_jwt(id_token).key


async def exchange_code(
    code: str, code_verifier: str, redirect_uri: str, client_id: str, client_secret: str
) -> str | None:
    """Redeems an authorization code (redirect flow, PKCE) for an id_token."""
    if not code or not client_id or not client_secret:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                TOKEN_URL,
                auth=(client_id, client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "code_verifier": code_verifier,
                },
            )
        if response.status_code != 200:
            return None
        id_token = response.json().get("id_token")
        return id_token if isinstance(id_token, str) else None
    except (httpx.HTTPError, ValueError):
        return None


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
