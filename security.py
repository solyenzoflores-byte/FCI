"""Utility functions for password hashing and verification."""

from __future__ import annotations

import hashlib
import secrets


def generate_salt() -> str:
    """Return a random salt encoded as hexadecimal string."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Hash ``password`` with the provided hexadecimal ``salt``.

    The function uses PBKDF2-HMAC with SHA-256 to derive the key. The
    resulting hash is returned as a hexadecimal string so it can be stored in
    JSON files easily.
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        100_000,
    ).hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Check whether ``password`` matches ``password_hash`` using ``salt``."""
    if not salt or not password_hash:
        return False
    return hash_password(password, salt) == password_hash


__all__ = ["generate_salt", "hash_password", "verify_password"]
