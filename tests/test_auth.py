from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import jwt
import pytest

import app.auth as auth


SECRET = "test-secret-key-with-at-least-32-bytes"


def credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def token_for(claims: dict) -> str:
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_accepts_valid_token_and_returns_email(monkeypatch):
    monkeypatch.setattr(auth, "SECRET_KEY", SECRET)
    token = token_for(
        {
            "sub": "user@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )

    assert auth.get_current_user_email(credentials(token)) == "user@example.com"


def test_rejects_missing_credentials():
    with pytest.raises(HTTPException) as error:
        auth.get_current_user_email(None)

    assert error.value.status_code == 401
    assert error.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "42", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        {"sub": "42"},
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        {"sub": "not-an-email", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        {"sub": "@example.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        {"sub": "user@", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        {"sub": "user @example.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
    ],
)
def test_rejects_expired_or_invalid_token_claims(monkeypatch, claims):
    monkeypatch.setattr(auth, "SECRET_KEY", SECRET)

    with pytest.raises(HTTPException) as error:
        auth.get_current_user_email(credentials(token_for(claims)))

    assert error.value.status_code == 401


def test_authentication_requires_a_configured_secret(monkeypatch):
    monkeypatch.setattr(auth, "SECRET_KEY", None)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        auth.validate_auth_configuration()
