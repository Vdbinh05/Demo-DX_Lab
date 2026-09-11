# SPDX-License-Identifier: MIT
"""Reusable FastAPI dependencies for authentication and authorization.

The separation between security primitives and request dependencies follows the
MIT-licensed Full Stack FastAPI Template architecture at commit
cb740b656d7a0a6c5e12c7bf8e50343ec94ee9c7.
"""

import logging
from collections.abc import Callable

import jwt
import pyodbc
from fastapi import Depends, Header, HTTPException, status

from app.core.security import AUTH_ALGORITHM, AUTH_SECRET
from app.database.connection import get_connection


logger = logging.getLogger(__name__)


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
        token_id = str(payload["jti"])
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
            SELECT users.UserID, users.Username, users.FullName,
                   users.RoleID, users.Status
            FROM dbo.Users users
            JOIN dbo.UserSessions sessions ON sessions.UserID = users.UserID
            WHERE users.UserID = ? AND sessions.TokenID = ?
              AND sessions.RevokedAt IS NULL
              AND sessions.ExpiresAt > SYSDATETIME()
            """,
            user_id, token_id,
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
        "TokenID": token_id,
    }


def require_admin(user: dict) -> dict:
    """Require the administrator role for a previously authenticated user."""
    if str(user.get("RoleID", "")).strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ quản trị viên được sử dụng chức năng này.",
        )
    return user


def require_roles(*allowed_roles: str) -> Callable[..., dict]:
    """Build a dependency that enforces roles on the server, not in React."""
    normalized_roles = {role.strip().lower() for role in allowed_roles if role.strip()}
    if not normalized_roles:
        raise ValueError("At least one role is required.")

    def role_dependency(user: dict = Depends(current_user)) -> dict:
        role = str(user.get("RoleID", "")).strip().lower()
        if role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản không có quyền thực hiện chức năng này.",
            )
        return user

    return role_dependency
