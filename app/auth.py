"""JWT authentication for API requests."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.config import SECRET_KEY

bearer_scheme = HTTPBearer(auto_error=False)


def validate_auth_configuration() -> None:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set to enable JWT authentication")
    if len(SECRET_KEY.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 bytes long")


def get_current_user_email(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    validate_auth_configuration()

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    subject = payload.get("sub")
    if (
        not isinstance(subject, str)
        or subject.count("@") != 1
        or any(character.isspace() for character in subject)
    ):
        raise HTTPException(
            status_code=401,
            detail="Token must contain a valid email address in the sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    local_part, domain = subject.split("@")
    if not local_part or not domain:
        raise HTTPException(
            status_code=401,
            detail="Token must contain a valid email address in the sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return subject
