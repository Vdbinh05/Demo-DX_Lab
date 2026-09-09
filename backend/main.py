"""FastAPI entry point for DX-Lab Core."""

import logging
import re

import pyodbc
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core import current_user, create_access_token, get_connection, hash_password, verify_password
from routers.admin import router as admin_router
from routers.catalog import router as catalog_router
from routers.sales import router as sales_router


app = FastAPI()
logger = logging.getLogger(__name__)

# Cho phép React (thường chạy ở cổng 5173) gọi API trong môi trường phát triển.
# Khi deploy, hãy thay "*" bằng domain frontend thật.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(admin_router)
app.include_router(catalog_router)
app.include_router(sales_router)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
PUBLIC_REGISTRATION_ROLE = "Sales"


@app.get("/health")
def health_check():
    connection = None
    try:
        connection = get_connection()
        connection.cursor().execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "connected"}
    except (pyodbc.Error, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQL Server chưa sẵn sàng.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@app.get("/me")
def read_current_user(user: dict = Depends(current_user)):
    return user


def validate_register_data(data: RegisterRequest):
    full_name = data.full_name.strip()
    username = data.username.strip()
    password = data.password

    if not 2 <= len(full_name) <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Họ và tên phải có từ 2 đến 100 ký tự.",
        )
    if not 3 <= len(username) <= 50 or not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tên đăng nhập phải có 3-50 ký tự và chỉ gồm chữ không dấu, "
                "số, dấu chấm, gạch dưới hoặc gạch ngang."
            ),
        )
    if not 8 <= len(password) <= 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu phải có từ 8 đến 128 ký tự.",
        )
    return full_name, username, password


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    full_name, username, password = validate_register_data(data)
    role_id = PUBLIC_REGISTRATION_ROLE
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM Users WHERE Username = ?", username)
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đăng nhập đã tồn tại.",
            )

        cursor.execute("SELECT RoleID FROM Roles WHERE RoleID = ?", role_id)
        role_row = cursor.fetchone()
        if not role_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vai trò không hợp lệ.",
            )

        cursor.execute(
            """
            INSERT INTO Users (Username, PasswordHash, FullName, RoleID, Status)
            OUTPUT INSERTED.UserID, INSERTED.Username, INSERTED.FullName,
                   INSERTED.RoleID, INSERTED.Status
            VALUES (?, ?, ?, ?, ?)
            """,
            username,
            hash_password(password),
            full_name,
            role_row[0],
            "Active",
        )
        row = cursor.fetchone()
        conn.commit()

        return {
            "success": True,
            "message": "Tạo tài khoản thành công.",
            "user": {
                "UserID": row[0],
                "Username": row[1],
                "FullName": row[2],
                "RoleID": row[3],
                "Status": row[4],
            },
        }
    except HTTPException:
        if conn is not None:
            conn.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if conn is not None:
            conn.rollback()
        logger.warning("Register integrity error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên đăng nhập đã tồn tại hoặc dữ liệu không hợp lệ.",
        ) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if conn is not None:
            conn.rollback()
        logger.exception("Could not register user")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể lưu tài khoản vào SQL Server.",
        ) from exc
    finally:
        if conn is not None:
            conn.close()


@app.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()
    password = data.password

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập tên đăng nhập và mật khẩu.",
        )

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT UserID, Username, PasswordHash, FullName, RoleID, Status
            FROM Users
            WHERE Username = ?
            """,
            username,
        )
        row = cursor.fetchone()
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not query user for login")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối SQL Server.",
        ) from exc
    finally:
        if conn is not None:
            conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập không tồn tại.",
        )

    user_id, saved_username, password_hash, full_name, role_id, user_status = row

    if str(user_status).strip().lower() != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khoá hoặc không còn hoạt động.",
        )

    if not verify_password(password, str(password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai mật khẩu.",
        )

    conn = None
    try:
        conn = get_connection()
        conn.cursor().execute(
            "UPDATE dbo.Users SET LastLoginAt = SYSDATETIME() WHERE UserID = ?",
            user_id,
        )
        conn.commit()
    except (pyodbc.Error, RuntimeError):
        logger.warning("Could not update LastLoginAt for user %s", user_id)
    finally:
        if conn is not None:
            conn.close()
            conn = None

    return {
        "success": True,
        "access_token": create_access_token(user_id, saved_username, role_id),
        "token_type": "bearer",
        "user": {
            "UserID": user_id,
            "Username": saved_username,
            "FullName": full_name,
            "RoleID": role_id,
            "Status": user_status,
        },
    }
