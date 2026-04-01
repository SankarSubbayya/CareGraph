import secrets
from base64 import b64decode

from fastapi import HTTPException, Request, status

from app.config import settings


def is_public_path(path: str) -> bool:
    return (
        path == "/"
        or path == "/dashboard"
        or path == "/health"
        or path.startswith("/static/")
        or path.startswith("/api/voice/webhook")
    )


def should_enforce_demo_auth(request: Request) -> bool:
    if not settings.demo_auth_enabled:
        return False
    if is_public_path(request.url.path):
        return False
    return True


def verify_demo_credentials(request: Request) -> None:
    if not should_enforce_demo_auth(request):
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        encoded = auth_header.split(" ", 1)[1]
        decoded = b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication header",
            headers={"WWW-Authenticate": "Basic"},
        ) from exc

    valid_user = secrets.compare_digest(username, settings.demo_username)
    valid_pass = secrets.compare_digest(password, settings.demo_password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def verify_admin_token(request: Request) -> None:
    """Require an explicit admin token for sensitive maintenance endpoints."""
    configured_token = settings.admin_api_token
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API token is not configured",
        )

    bearer = request.headers.get("Authorization", "")
    if bearer.startswith("Bearer "):
        presented_token = bearer.split(" ", 1)[1]
    else:
        presented_token = request.headers.get("X-Admin-Token", "")

    if not presented_token or not secrets.compare_digest(presented_token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
