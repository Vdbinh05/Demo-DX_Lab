# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

import logging
from datetime import datetime

import pyodbc
from fastapi import APIRouter, Depends, Query

from app.api.admin_common import (
    admin_user,
    clean as _clean,
    db_error as _db_error,
    one as _one,
    rows as _rows,
)
from app.database.connection import get_connection
from app.schemas.admin import SettingsPayload


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/settings")
def get_settings(_: dict = Depends(admin_user)):
    defaults = {"company_name": "DX-Lab Core", "company_phone": "", "company_address": "", "tax_code": ""}
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT SettingKey AS setting_key, SettingValue AS setting_value FROM dbo.SystemSettings")
        values = {row["setting_key"]: row["setting_value"] for row in _rows(cursor)}
        defaults.update({key: values.get(key, value) for key, value in defaults.items()})
        cursor.execute("SELECT COUNT(*) AS activity_count FROM dbo.Activities")
        return {
            "settings": defaults,
            "system": {"database": "Đã kết nối", "activity_count": _one(cursor)["activity_count"], "checked_at": datetime.now().isoformat()},
        }
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load settings")
    finally:
        if connection is not None: connection.close()


@router.put("/settings")
def update_settings(payload: SettingsPayload, user: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        for key, value in payload.model_dump().items():
            cursor.execute(
                """
                UPDATE dbo.SystemSettings SET SettingValue = ?, UpdatedAt = SYSDATETIME(), UpdatedBy = ? WHERE SettingKey = ?;
                IF @@ROWCOUNT = 0 INSERT INTO dbo.SystemSettings (SettingKey, SettingValue, UpdatedAt, UpdatedBy) VALUES (?, ?, SYSDATETIME(), ?);
                """,
                _clean(value), user["UserID"], key, key, _clean(value), user["UserID"],
            )
        connection.commit()
        return {"success": True}
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update settings")
    finally:
        if connection is not None: connection.close()


@router.get("/notifications")
def notifications(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT TOP 8 'stock-' + ProductID AS notification_id, N'Tồn kho cần chú ý' AS title,
                   ProductName + N' chỉ còn ' + CAST(Stock AS nvarchar(20)) + N' sản phẩm.' AS message,
                   N'inventory' AS target, 1 AS priority
            FROM dbo.Products WHERE Stock <= ReorderLevel ORDER BY Stock
            """
        )
        items = _rows(cursor)
        cursor.execute(
            """
            SELECT TOP 5 'order-' + OrderID AS notification_id, N'Đơn hàng mới hôm nay' AS title,
                   OrderID + N' · ' + FORMAT(TotalValue, 'N0', 'vi-VN') + N' ₫' AS message,
                   N'orders' AS target, 0 AS priority
            FROM dbo.SalesOrders
            WHERE OrderDate = CONVERT(date, GETDATE())
              AND Status IN (N'Completed', N'Paid', N'Hoàn thành')
            ORDER BY COALESCE(PaidAt, CreatedAt, CAST(OrderDate AS datetime2)) DESC
            """
        )
        items.extend(_rows(cursor))
        return {"items": items, "count": len(items)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load notifications")
    finally:
        if connection is not None: connection.close()


@router.get("/search")
def global_search(q: str = Query(min_length=2, max_length=100), _: dict = Depends(admin_user)):
    query = _clean(q)
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        results = []
        searches = [
            ("SELECT TOP 5 ProductID AS result_id, ProductName AS title, Category AS subtitle, N'products' AS target, N'Sản phẩm' AS result_type FROM dbo.Products WHERE ProductID LIKE '%' + ? + '%' OR ProductName LIKE N'%' + ? + N'%' ORDER BY ProductName", (query, query)),
            ("SELECT TOP 5 CustomerID AS result_id, CustomerName AS title, COALESCE(Phone, N'Chưa có số điện thoại') AS subtitle, N'customers' AS target, N'Khách hàng' AS result_type FROM dbo.Customers WHERE CustomerID LIKE '%' + ? + '%' OR CustomerName LIKE N'%' + ? + N'%' ORDER BY CustomerName", (query, query)),
            ("SELECT TOP 5 orders.OrderID AS result_id, orders.OrderID AS title, customers.CustomerName AS subtitle, N'orders' AS target, N'Đơn hàng' AS result_type FROM dbo.SalesOrders orders JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID WHERE orders.OrderID LIKE '%' + ? + '%' OR customers.CustomerName LIKE N'%' + ? + N'%' ORDER BY orders.OrderDate DESC", (query, query)),
            ("SELECT TOP 5 CAST(UserID AS varchar(20)) AS result_id, FullName AS title, Username + N' · ' + RoleID AS subtitle, N'users' AS target, N'Tài khoản' AS result_type FROM dbo.Users WHERE Username LIKE '%' + ? + '%' OR FullName LIKE N'%' + ? + N'%' ORDER BY FullName", (query, query)),
        ]
        for sql, params in searches:
            cursor.execute(sql, *params)
            results.extend(_rows(cursor))
        return {"items": results}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not run global search")
    finally:
        if connection is not None: connection.close()


@router.get("/activities")
def list_activities(
    category: str | None = Query(default=None, max_length=50),
    action: str | None = Query(default=None, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    _: dict = Depends(admin_user),
):
    filters = ["1 = 1"]
    parameters: list[object] = []
    if category:
        filters.append("LOWER(activities.Category) = LOWER(?)")
        parameters.append(category.strip())
    if action:
        filters.append("LOWER(activities.Action) = LOWER(?)")
        parameters.append(action.strip())
    where_sql = " AND ".join(filters)
    offset = (page - 1) * page_size
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        total = int(
            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.Activities activities WHERE {where_sql}",
                *parameters,
            ).fetchone()[0]
        )
        cursor.execute(
            f"""
            SELECT activities.ActivityID AS activity_id,
                   activities.Description AS description,
                   activities.Category AS category,
                   activities.Action AS action,
                   activities.EntityType AS entity_type,
                   activities.EntityID AS entity_id,
                   activities.OldValues AS old_values,
                   activities.NewValues AS new_values,
                   activities.CreatedAt AS created_at,
                   activities.UserID AS user_id,
                   users.FullName AS user_name
            FROM dbo.Activities activities
            LEFT JOIN dbo.Users users ON users.UserID = activities.UserID
            WHERE {where_sql}
            ORDER BY activities.CreatedAt DESC, activities.ActivityID DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *parameters, offset, page_size,
        )
        return {
            "items": _rows(cursor),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list activities")
    finally:
        if connection is not None: connection.close()
