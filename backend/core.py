"""Shared database and authentication helpers for DX-Lab Core."""

import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pyodbc
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status


load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

logger = logging.getLogger(__name__)

SQL_SERVER = os.getenv("DXLAB_SQL_SERVER", "localhost")
SQL_DATABASE = os.getenv("DXLAB_SQL_DATABASE", "DXLabCore")
SQL_USER = os.getenv("DXLAB_SQL_USER", "sa")
SQL_PASSWORD = os.getenv("DXLAB_SQL_PASSWORD")
SQL_DRIVER = os.getenv("DXLAB_SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

AUTH_SECRET_FILE = Path(__file__).resolve().parent / ".auth-secret"


def _load_auth_secret() -> str:
    configured = (os.getenv("DXLAB_AUTH_SECRET") or "").strip()
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
ACCESS_TOKEN_MINUTES = int(os.getenv("DXLAB_ACCESS_TOKEN_MINUTES", "480"))

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

# pyodbc reuses underlying ODBC connections after close(), reducing handshake
# overhead while keeping the request-level connection lifecycle simple.
pyodbc.pooling = True


def get_connection():
    """Open a short-lived SQL Server connection."""
    if not SQL_PASSWORD:
        raise RuntimeError("Chưa cấu hình biến môi trường DXLAB_SQL_PASSWORD.")

    connection_string = (
        f"DRIVER={SQL_DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(connection_string, timeout=5)


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


def create_access_token(user_id: int, username: str, role_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Validate the bearer token and reload the account from SQL Server."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ.",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[AUTH_ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn hoặc không hợp lệ.",
        ) from exc

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT UserID, Username, FullName, RoleID, Status
            FROM dbo.Users
            WHERE UserID = ?
            """,
            user_id,
        )
        row = cursor.fetchone()
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not validate authenticated user")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể xác thực tài khoản với SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()

    if not row or str(row.Status).strip().lower() != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị khóa.",
        )

    return {
        "UserID": row.UserID,
        "Username": row.Username,
        "FullName": row.FullName,
        "RoleID": row.RoleID,
        "Status": row.Status,
    }


def require_admin(user: dict) -> dict:
    if str(user.get("RoleID", "")).strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ quản trị viên được sử dụng chức năng này.",
        )
    return user
