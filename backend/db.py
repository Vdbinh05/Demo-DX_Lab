# SPDX-License-Identifier: MIT
"""SQL Server connection helpers and startup diagnostics."""

from __future__ import annotations

import pyodbc

from config import settings


pyodbc.pooling = True

REQUIRED_TABLES = (
    "Roles",
    "Users",
    "Products",
    "Customers",
    "SalesOrders",
    "SalesOrderItems",
    "StockMovements",
)


def get_connection() -> pyodbc.Connection:
    """Open a request-scoped connection backed by the ODBC connection pool."""
    return pyodbc.connect(settings.sql_connection_string(), timeout=5)


def database_error_message(error: Exception) -> str:
    """Return a safe and actionable message without exposing credentials."""
    message = str(error).lower()
    if "im002" in message or "data source name not found" in message:
        return f"Không tìm thấy {settings.sql_driver}. Hãy cài đúng Microsoft ODBC Driver."
    if "18456" in message or "login failed" in message:
        return "SQL Server từ chối đăng nhập. Hãy kiểm tra tài khoản và mật khẩu trong backend/.env."
    if "4060" in message or "cannot open database" in message:
        return f"Không mở được database {settings.sql_database}. Hãy chạy CAI_DAT_LAN_DAU.bat."
    if any(code in message for code in ("08001", "08004", "10060", "10061", "server does not exist")):
        return f"Không kết nối được SQL Server tại {settings.sql_server}. Hãy kiểm tra dịch vụ, instance và cổng."
    return "SQL Server chưa sẵn sàng. Hãy kiểm tra backend/.env và chạy lại công cụ cài đặt."


def check_database() -> dict[str, object]:
    """Verify connectivity and the minimum schema required by the application."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        database_name = cursor.execute("SELECT DB_NAME()").fetchone()[0]
        placeholders = ",".join("?" for _ in REQUIRED_TABLES)
        rows = cursor.execute(
            f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ({placeholders})",
            *REQUIRED_TABLES,
        ).fetchall()
        existing = {str(row[0]) for row in rows}
        missing = [name for name in REQUIRED_TABLES if name not in existing]
        if missing:
            raise RuntimeError(
                "Database thiếu bảng bắt buộc: " + ", ".join(missing)
                + ". Hãy chạy backend/database/init_database.py."
            )
        return {
            "status": "ok",
            "database": str(database_name),
            "required_tables": len(REQUIRED_TABLES),
        }
    finally:
        connection.close()
