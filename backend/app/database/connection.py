# SPDX-License-Identifier: MIT
"""SQL Server connection helpers and startup diagnostics."""

from __future__ import annotations

import pyodbc

from app.core.config import settings


pyodbc.pooling = True

REQUIRED_SCHEMA = {
    "Roles": {"RoleID", "RoleName"},
    "Users": {"UserID", "Username", "PasswordHash", "FullName", "RoleID", "Status"},
    "UserSessions": {"TokenID", "UserID", "ExpiresAt", "RevokedAt"},
    "Products": {"ProductID", "ProductName", "Category", "Price", "Stock", "ReorderLevel"},
    "Customers": {"CustomerID", "CustomerName", "Tier", "Status"},
    "Promotions": {
        "PromotionID", "Title", "DiscountType", "DiscountValue", "MinOrderValue",
        "MaxUses", "UsedCount", "StartDate", "EndDate", "Status",
    },
    "SalesOrders": {
        "OrderID", "CustomerID", "CreatedBy", "TotalValue", "Status", "OrderDate",
        "PaymentMethod", "PaymentStatus", "OrderStatus", "IdempotencyKey",
        "RequestFingerprint", "SubtotalValue", "DiscountValue", "PromotionID",
    },
    "SalesOrderItems": {
        "ItemID", "OrderID", "ProductID", "Quantity", "UnitPrice", "SubTotal",
        "ProductNameSnapshot",
    },
    "StockMovements": {
        "MovementID", "ProductID", "MovementType", "Quantity", "ReferenceID",
        "Reason", "PerformedBy", "CreatedAt",
    },
    "PurchaseRequests": {"RequestID", "ProductID", "Quantity", "Reason", "Status", "CreatedAt"},
    "Activities": {
        "ActivityID", "Description", "Category", "UserID", "Action", "EntityType",
        "EntityID", "OldValues", "NewValues", "CreatedAt",
    },
    "SystemSettings": {"SettingKey", "SettingValue", "UpdatedAt", "UpdatedBy"},
}
REQUIRED_TABLES = tuple(REQUIRED_SCHEMA)


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
            f"SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ({placeholders})",
            *REQUIRED_TABLES,
        ).fetchall()
        existing: dict[str, set[str]] = {}
        for table_name, column_name in rows:
            existing.setdefault(str(table_name), set()).add(str(column_name))
        missing_tables = [name for name in REQUIRED_TABLES if name not in existing]
        if missing_tables:
            raise RuntimeError(
                "Database thiếu bảng bắt buộc: " + ", ".join(missing_tables)
                + ". Hãy chạy backend/database/init_database.py."
            )
        missing_columns = [
            f"{table}.{column}"
            for table, required_columns in REQUIRED_SCHEMA.items()
            for column in sorted(required_columns - existing[table])
        ]
        if missing_columns:
            raise RuntimeError(
                "Database thiếu cột bắt buộc: " + ", ".join(missing_columns)
                + ". Hãy chạy backend/database/init_database.py."
            )
        return {
            "status": "ok",
            "database": str(database_name),
            "required_tables": len(REQUIRED_TABLES),
            "required_columns": sum(len(columns) for columns in REQUIRED_SCHEMA.values()),
        }
    finally:
        connection.close()
