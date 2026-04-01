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
