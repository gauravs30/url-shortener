"""Short-code generation and custom-alias validation. See decisions/0003."""

import re
import secrets

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"  # base62

ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")

# Codes that would collide with real routes or confuse tooling.
RESERVED = frozenset(
    {"api", "healthz", "static", "docs", "redoc", "openapi.json", "admin", "favicon.ico"}
)


class InvalidAlias(ValueError):
    """Raised when a user-supplied alias fails validation."""


def generate_code(length: int) -> str:
    """A random base62 string of the given length."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def validate_alias(alias: str) -> str:
    """Return the alias unchanged if acceptable, else raise InvalidAlias."""
    if not ALIAS_RE.match(alias):
        raise InvalidAlias("alias must be 3-32 chars of letters, digits, hyphen or underscore")
    if alias.lower() in RESERVED:
        raise InvalidAlias(f"'{alias}' is reserved")
    return alias
