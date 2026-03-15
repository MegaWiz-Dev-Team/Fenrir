"""JWT Auth Middleware — protect Fenrir API endpoints via Yggdrasil.

Uses Yggdrasil's `validate_jwt` to verify Zitadel-issued JWTs.
Public endpoints (health, docs) are excluded.
"""

import logging

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("fenrir.auth")

# Routes that NEVER require authentication
PUBLIC_PATHS = frozenset({
    "/healthz",
    "/readyz",
    "/docs",
    "/redoc",
    "/openapi.json",
})

# Path prefixes that are always public
PUBLIC_PREFIXES = (
    "/docs",
    "/redoc",
)


async def validate_jwt(token: str):
    """Validate JWT via Yggdrasil middleware.

    Separated for easy mocking in tests.
    """
    from yggdrasil.middleware import validate_jwt as ygg_validate
    return await ygg_validate(token)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that validates JWT Bearer tokens.

    Skips authentication for:
    - Health endpoints (/healthz, /readyz)
    - OpenAPI docs (/docs, /redoc, /openapi.json)

    When auth_enabled=False (in settings), all requests pass through.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        from fenrir.config import settings
        path = request.url.path

        # Always skip public endpoints
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # Skip auth if disabled (dev mode)
        if not settings.auth_enabled:
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[7:]

        try:
            claims = await validate_jwt(token)
            request.state.claims = claims
        except Exception as e:
            logger.warning(f"JWT validation failed: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid token: {e}"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
