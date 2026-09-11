# SPDX-License-Identifier: MIT
"""Password hashing and access-token helpers for DX-Lab Core."""

import base64
import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]
AUTH_SECRET_FILE = BACKEND_ROOT / ".auth-secret"


def _load_auth_secret() -> str:
    configured = settings.auth_secret
    if configured and configured != "replace-with-a-long-random-secret":
        return configured

    try:
        saved = AUTH_SECRET_FILE.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    except FileNotFoundError:
        pass

    generated = secrets.token_urlsafe(48)
    try:
        with AUTH_SECRET_FILE.open("x", encoding="utf-8") as secret_file:
            secret_file.write(generated)
        return generated
    except FileExistsError:
        return AUTH_SECRET_FILE.read_text(encoding="utf-8").strip()


AUTH_SECRET = _load_auth_secret()
AUTH_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = settings.access_token_minutes

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
PASSWORD_UPPER_PATTERN = re.compile(r"[A-Z]")
PASSWORD_LOWER_PATTERN = re.compile(r"[a-z]")
PASSWORD_DIGIT_PATTERN = re.compile(r"\d")
PASSWORD_SPECIAL_PATTERN = re.compile(r"[^A-Za-z0-9]")


def password_policy_error(password: str) -> str | None:
    """Return a user-facing validation error, or ``None`` for a strong password."""
    if not 8 <= len(password) <= 128:
        return "Mật khẩu phải có từ 8 đến 128 ký tự."
    if not PASSWORD_UPPER_PATTERN.search(password):
        return "Mật khẩu phải có ít nhất một chữ hoa."
    if not PASSWORD_LOWER_PATTERN.search(password):
        return "Mật khẩu phải có ít nhất một chữ thường."
    if not PASSWORD_DIGIT_PATTERN.search(password):
        return "Mật khẩu phải có ít nhất một chữ số."
    if not PASSWORD_SPECIAL_PATTERN.search(password):
        return "Mật khẩu phải có ít nhất một ký tự đặc biệt."
    return None

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt_text}${digest_text}"


def verify_password(password: str, stored_password: str) -> bool:
    if stored_password.startswith(f"{PASSWORD_SCHEME}$"):
        try:
            _, iterations_text, salt_text, digest_text = stored_password.split("$", 3)
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected_digest = base64.urlsafe_b64decode(digest_text.encode("ascii"))
            candidate_digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, int(iterations_text)
            )
            return hmac.compare_digest(candidate_digest, expected_digest)
        except (ValueError, TypeError):
            return False

    return hmac.compare_digest(password, stored_password)


def password_needs_upgrade(stored_password: str) -> bool:
    """Identify legacy plaintext passwords that should be re-hashed on login."""
    return not stored_password.startswith(f"{PASSWORD_SCHEME}$")


def create_access_token(
    user_id: int,
    username: str,
    role_id: str,
    *,
    token_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role_id,
        "jti": token_id or uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)
