"""Configuration helpers (CORS, env loading)."""

from app.config import parse_cors_allowed_origins


def test_cors_wildcard_default() -> None:
    assert parse_cors_allowed_origins(None) == ("*",)
    assert parse_cors_allowed_origins("*") == ("*",)


def test_cors_comma_separated_origins() -> None:
    assert parse_cors_allowed_origins(
        "https://app.example.com, http://localhost:5173",
    ) == (
        "https://app.example.com",
        "http://localhost:5173",
    )
