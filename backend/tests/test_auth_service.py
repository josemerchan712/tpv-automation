import pytest
from datetime import timedelta
from jose import JWTError

from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hash_roundtrip():
    hashed = get_password_hash("secret")
    assert verify_password("secret", hashed) is True


def test_verify_wrong_password():
    hashed = get_password_hash("correct")
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "alice"})
    payload = decode_access_token(token)
    assert payload["sub"] == "alice"


def test_expired_token_raises():
    token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_access_token(token)
