# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

import logging

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.admin_common import (
    admin_user,
    clean as _clean,
    db_error as _db_error,
    one as _one,
    rows as _rows,
)
from app.database.connection import get_connection
from app.schemas.admin import AdminOrderDetailResponse


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/orders")
def list_orders(q: str = Query(default="", max_length=100), _: dict = Depends(admin_user)):
    query = _clean(q)
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT TOP 200 orders.OrderID AS order_id,
                   customers.CustomerID AS customer_id, customers.CustomerName AS customer,
                   COALESCE(users.FullName, N'Không xác định') AS seller,
                   COALESCE(orders.SubtotalValue, orders.TotalValue) AS subtotal_value,
                   COALESCE(orders.DiscountValue, 0) AS discount_value,
                   orders.TotalValue AS total_value, orders.Status AS order_status,
                   orders.PromotionID AS promotion_id,
                   promotions.Title AS promotion_title,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2)) AS created_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
            LEFT JOIN dbo.Promotions promotions ON promotions.PromotionID = orders.PromotionID
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND (? = '' OR orders.OrderID LIKE '%' + ? + '%'
                OR customers.CustomerName LIKE N'%' + ? + N'%'
                OR users.FullName LIKE N'%' + ? + N'%')
            ORDER BY COALESCE(orders.PaidAt, orders.CreatedAt,
                CAST(orders.OrderDate AS datetime2)) DESC
            """,
            query, query, query, query,
        )
        return {"items": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list orders")
    finally:
        if connection is not None:
            connection.close()


@router.get("/orders/{order_id}", response_model=AdminOrderDetailResponse)
def order_detail(order_id: str, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT orders.OrderID AS order_id, customers.CustomerID AS customer_id,
                   customers.CustomerName AS customer, customers.ContactName AS contact_name,
                   customers.Phone AS phone, COALESCE(users.FullName, N'Không xác định') AS seller,
                   COALESCE(orders.SubtotalValue, orders.TotalValue) AS subtotal_value,
                   COALESCE(orders.DiscountValue, 0) AS discount_value,
                   orders.TotalValue AS total_value,
                   orders.PromotionID AS promotion_id,
                   promotions.Title AS promotion_title,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaymentStatus, orders.Status) AS payment_status,
                   COALESCE(orders.OrderStatus,
                       CASE WHEN orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
                            THEN N'Completed' ELSE orders.Status END) AS order_status,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2)) AS created_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
            LEFT JOIN dbo.Promotions promotions ON promotions.PromotionID = orders.PromotionID
            WHERE orders.OrderID = ?
            """,
            order_id,
        )
        order = _one(cursor)
        if not order:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
        cursor.execute(
            """
            SELECT items.ProductID AS product_id,
                   COALESCE(items.ProductNameSnapshot, products.ProductName) AS name,
                   items.Quantity AS quantity, items.UnitPrice AS unit_price,
                   items.SubTotal AS subtotal
            FROM dbo.SalesOrderItems items
            LEFT JOIN dbo.Products products ON products.ProductID = items.ProductID
            WHERE items.OrderID = ? ORDER BY items.ItemID
            """,
            order_id,
        )
        order["items"] = _rows(cursor)
        return order
    except HTTPException:
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load order detail")
    finally:
        if connection is not None:
            connection.close()
