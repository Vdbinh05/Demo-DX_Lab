"""FastAPI backend for DX-Lab Core authentication."""

import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
from pathlib import Path

import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Tự đọc cấu hình phát triển cục bộ. Các biến môi trường đã được hệ thống
# thiết lập vẫn được ưu tiên vì load_dotenv không ghi đè mặc định.
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


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


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str
    role_id: str


# Có thể ghi đè các giá trị này bằng biến môi trường khi deploy.
SQL_SERVER = os.getenv("DXLAB_SQL_SERVER", "localhost")
SQL_DATABASE = os.getenv("DXLAB_SQL_DATABASE", "DXLabCore")
SQL_USER = os.getenv("DXLAB_SQL_USER", "sa")
SQL_PASSWORD = os.getenv("DXLAB_SQL_PASSWORD")
SQL_DRIVER = os.getenv("DXLAB_SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def get_connection():
    if not SQL_PASSWORD:
        raise RuntimeError("Chưa cấu hình biến môi trường DXLAB_SQL_PASSWORD.")

    conn_str = (
        f"DRIVER={SQL_DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=5)


def hash_password(password: str) -> str:
    """Hash a password without requiring an additional third-party package."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt_text}${digest_text}"


def verify_password(password: str, stored_password: str) -> bool:
    """Verify new PBKDF2 hashes while keeping old plain-text accounts usable."""
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

    # Tương thích với các tài khoản cũ đang lưu mật khẩu dạng thường.
    return hmac.compare_digest(password, stored_password)


def validate_register_data(data: RegisterRequest):
    full_name = data.full_name.strip()
    username = data.username.strip()
    password = data.password
    role_id = data.role_id.strip()

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
    if not role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng chọn vai trò.",
        )

    return full_name, username, password, role_id


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    full_name, username, password, role_id = validate_register_data(data)
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

    return {
        "success": True,
        "user": {
            "UserID": user_id,
            "Username": saved_username,
            "FullName": full_name,
            "RoleID": role_id,
            "Status": user_status,
        },
    }
