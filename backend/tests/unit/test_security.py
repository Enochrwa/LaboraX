"""Unit tests for app.core.security."""

import pytest

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from tests.conftest import fixture_credential


def test_hash_password_produces_a_verifiable_but_different_string() -> None:
    password = fixture_credential()
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password(fixture_credential())
    assert not verify_password("a-different-value", hashed)


def test_access_token_round_trips_subject_and_role() -> None:
    token = create_access_token(subject="user-123", role="student")
    payload = decode_token(token, expected_type=TokenType.ACCESS)
    assert payload.sub == "user-123"
    assert payload.role == "student"
    assert payload.type == TokenType.ACCESS


def test_refresh_token_round_trips_subject_and_role() -> None:
    token = create_refresh_token(subject="user-456", role="lecturer")
    payload = decode_token(token, expected_type=TokenType.REFRESH)
    assert payload.sub == "user-456"
    assert payload.type == TokenType.REFRESH


def test_decode_token_rejects_wrong_token_type() -> None:
    access_token = create_access_token(subject="user-123", role="student")
    with pytest.raises(InvalidTokenError):
        decode_token(access_token, expected_type=TokenType.REFRESH)


def test_decode_token_rejects_garbage_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-real-token", expected_type=TokenType.ACCESS)
