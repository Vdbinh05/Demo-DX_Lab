# SPDX-License-Identifier: MIT
"""Public registration, login and current-session endpoints."""

import logging
import hashlib
import threading
import time
import uuid

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import current_user
from app.core.security import (
    ACCESS_TOKEN_MINUTES,
    USERNAME_PATTERN,
    create_access_token,
    hash_password,
    password_policy_error,
    password_needs_upgrade,
    verify_password,
)
from app.database.connection import get_connection
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest


router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)
PUBLIC_REGISTRATION_ROLE = "Sales"
LOGIN_FAILED_MESSAGE = "Đăng nhập thất bại."
PORTAL_ROLES = {
    "employee": {"sales", "warehouse"},
    "admin": {"admin"},
}
# Run the same expensive password verification for an unknown username. This
# makes response timing less useful for discovering which accounts exist.
DUMMY_PASSWORD_HASH = hash_password("DXLabCore-Dummy-Authentication-Value")
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW_SECONDS = 300
LOGIN_BLOCK_SECONDS = 900
_login_attempts: dict[str, tuple[int, float, float]] = {}
_login_attempts_lock = threading.Lock()


def _attempt_key(username: str) -> str:
    return hashlib.sha256(username.strip().lower().encode("utf-8")).hexdigest()


def _check_login_rate(username: str) -> None:
    key = _attempt_key(username)
    now = time.monotonic()
    with _login_attempts_lock:
        count, first_at, blocked_until = _login_attempts.get(key, (0, now, 0.0))
        if blocked_until > now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=LOGIN_FAILED_MESSAGE,
                headers={"Retry-After": str(int(blocked_until - now) + 1)},
            )
        if now - first_at > LOGIN_ATTEMPT_WINDOW_SECONDS:
            _login_attempts.pop(key, None)


def _record_failed_login(username: str) -> None:
    key = _attempt_key(username)
    now = time.monotonic()
    with _login_attempts_lock:
        count, first_at, _ = _login_attempts.get(key, (0, now, 0.0))
        if now - first_at > LOGIN_ATTEMPT_WINDOW_SECONDS:
            count, first_at = 0, now
        count += 1
        blocked_until = now + LOGIN_BLOCK_SECONDS if count >= LOGIN_ATTEMPT_LIMIT else 0.0
        _login_attempts[key] = (count, first_at, blocked_until)


def _clear_login_attempts(username: str) -> None:
    with _login_attempts_lock:
        _login_attempts.pop(_attempt_key(username), None)


@router.get("/me")
def read_current_user(user: dict = Depends(current_user)):
    return {key: value for key, value in user.items() if key != "TokenID"}


def validate_register_data(data: RegisterRequest):
    full_name = data.full_name.strip()
    username = data.username.strip()
    password = data.password

    if not 2 <= len(full_name) <= 100:
        raise HTTPException(status_code=400, detail="Họ và tên phải có từ 2 đến 100 ký tự.")
    if not 3 <= len(username) <= 50 or not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(
            status_code=400,
            detail=("Tên đăng nhập phải có 3-50 ký tự và chỉ gồm chữ không dấu, "
                    "số, dấu chấm, gạch dưới hoặc gạch ngang."),
        )
    password_error = password_policy_error(password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)
    return full_name, username, password


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    full_name, username, password = validate_register_data(data)
    role_id = PUBLIC_REGISTRATION_ROLE
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Users WHERE Username = ?", username)
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại.")
        cursor.execute("SELECT RoleID FROM Roles WHERE RoleID = ?", role_id)
        role_row = cursor.fetchone()
        if not role_row:
            raise HTTPException(status_code=400, detail="Vai trò không hợp lệ.")
        cursor.execute(
            """
            INSERT INTO Users (Username, PasswordHash, FullName, RoleID, Status)
            OUTPUT INSERTED.UserID, INSERTED.Username, INSERTED.FullName,
                   INSERTED.RoleID, INSERTED.Status
            VALUES (?, ?, ?, ?, ?)
            """,
            username, hash_password(password), full_name, role_row[0], "Active",
        )
        row = cursor.fetchone()
        connection.commit()
        return {
            "success": True,
            "message": "Tạo tài khoản thành công.",
            "user": {"UserID": row[0], "Username": row[1], "FullName": row[2],
                     "RoleID": row[3], "Status": row[4]},
        }
    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if connection is not None:
            connection.rollback()
        logger.warning("Register integrity error: %s", exc)
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại hoặc dữ liệu không hợp lệ.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None:
            connection.rollback()
        logger.exception("Could not register user")
        raise HTTPException(status_code=503, detail="Không thể lưu tài khoản vào SQL Server.") from exc
    finally:
        if connection is not None:
            connection.close()


@router.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()
    password = data.password
    if not username or not password:
        raise HTTPException(status_code=401, detail=LOGIN_FAILED_MESSAGE)
    _check_login_rate(username)

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT UserID, Username, PasswordHash, FullName, RoleID, Status "
            "FROM Users WHERE Username = ?",
            username,
        )
        row = cursor.fetchone()
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not query user for login")
        raise HTTPException(status_code=503, detail="Không thể kết nối SQL Server.") from exc
    finally:
        if connection is not None:
            connection.close()

    stored_password = str(row[2]) if row else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(password, stored_password)
    if row:
        user_id, saved_username, password_hash, full_name, role_id, user_status = row
        role_is_allowed = str(role_id).strip().lower() in PORTAL_ROLES[data.portal]
        account_is_active = str(user_status).strip().lower() == "active"
    else:
        role_is_allowed = False
        account_is_active = False

    if not row or not password_is_valid or not account_is_active or not role_is_allowed:
        _record_failed_login(username)
        raise HTTPException(status_code=401, detail=LOGIN_FAILED_MESSAGE)

    _clear_login_attempts(username)
    token_id = uuid.uuid4().hex
    access_token = create_access_token(
        user_id, saved_username, role_id, token_id=token_id
    )

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        if password_needs_upgrade(str(password_hash)):
            cursor.execute("UPDATE dbo.Users SET PasswordHash = ? WHERE UserID = ?", hash_password(password), user_id)
        cursor.execute("UPDATE dbo.Users SET LastLoginAt = SYSDATETIME() WHERE UserID = ?", user_id)
        cursor.execute(
            """
            INSERT INTO dbo.UserSessions (TokenID, UserID, CreatedAt, ExpiresAt)
            VALUES (?, ?, SYSDATETIME(), DATEADD(minute, ?, SYSDATETIME()))
            """,
            token_id, user_id, ACCESS_TOKEN_MINUTES,
        )
        cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Account', ?,
                    'LOGIN', 'User', ?)
            """,
            f"{full_name} đã đăng nhập", user_id, str(user_id),
        )
        connection.commit()
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        logger.exception("Could not create login session for user %s", user_id)
        raise HTTPException(
            status_code=503,
            detail="Không thể tạo phiên đăng nhập lúc này.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"UserID": user_id, "Username": saved_username, "FullName": full_name,
                 "RoleID": role_id, "Status": user_status},
    }


@router.post("/change-password")
def change_password(data: ChangePasswordRequest, user: dict = Depends(current_user)):
    password_error = password_policy_error(data.new_password)
    if password_error:
        raise HTTPException(status_code=422, detail=password_error)
    if data.current_password == data.new_password:
        raise HTTPException(status_code=422, detail="Mật khẩu mới phải khác mật khẩu hiện tại.")

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        row = cursor.execute(
            "SELECT PasswordHash FROM dbo.Users WITH (UPDLOCK, ROWLOCK) WHERE UserID = ?",
            int(user["UserID"]),
        ).fetchone()
        if row is None or not verify_password(data.current_password, str(row.PasswordHash)):
            raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng.")
        cursor.execute(
            "UPDATE dbo.Users SET PasswordHash = ? WHERE UserID = ?",
            hash_password(data.new_password), int(user["UserID"]),
        )
        cursor.execute(
            "UPDATE dbo.UserSessions SET RevokedAt = SYSDATETIME() WHERE UserID = ? AND RevokedAt IS NULL",
            int(user["UserID"]),
        )
        cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Account', ?,
                    'CHANGE_PASSWORD', 'User', ?)
            """,
            f"{user['FullName']} đã đổi mật khẩu",
            int(user["UserID"]), str(user["UserID"]),
        )
        connection.commit()
        return {"success": True, "message": "Đổi mật khẩu thành công."}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        logger.exception("Could not change password")
        raise HTTPException(status_code=503, detail="Không thể đổi mật khẩu lúc này.") from exc
    finally:
        if connection is not None: connection.close()


@router.post("/logout")
def logout(user: dict = Depends(current_user)):
    """Revoke the current server-side session."""
    connection = None
    try:
        connection = get_connection()
        connection.cursor().execute(
            "UPDATE dbo.UserSessions SET RevokedAt = SYSDATETIME() WHERE TokenID = ?",
            user["TokenID"],
        )
        connection.commit()
        return {"success": True}
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        logger.exception("Could not revoke login session")
        raise HTTPException(status_code=503, detail="Không thể đăng xuất lúc này.") from exc
    finally:
        if connection is not None: connection.close()
