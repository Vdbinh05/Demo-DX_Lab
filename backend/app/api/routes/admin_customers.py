# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

import logging

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.admin_common import (
    admin_user,
    business_id as _business_id,
    clean as _clean,
    db_error as _db_error,
    one as _one,
    rows as _rows,
)
from app.database.connection import get_connection
from app.schemas.admin import CustomerPayload


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/customers")
def list_customers(q: str = Query(default="", max_length=100), _: dict = Depends(admin_user)):
    query = _clean(q)
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT customers.CustomerID AS customer_id, customers.CustomerName AS name,
                   customers.ContactName AS contact_name, customers.Phone AS phone,
                   customers.Tier AS tier, customers.Status AS customer_status,
                   COUNT(orders.OrderID) AS order_count,
                   COALESCE(SUM(CASE WHEN orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
                       THEN orders.TotalValue ELSE 0 END), 0) AS total_spent
            FROM dbo.Customers customers
            LEFT JOIN dbo.SalesOrders orders ON orders.CustomerID = customers.CustomerID
            WHERE (? = '' OR customers.CustomerID LIKE '%' + ? + '%'
                OR customers.CustomerName LIKE N'%' + ? + N'%'
                OR customers.ContactName LIKE N'%' + ? + N'%'
                OR customers.Phone LIKE '%' + ? + '%')
            GROUP BY customers.CustomerID, customers.CustomerName, customers.ContactName,
                     customers.Phone, customers.Tier, customers.Status
            ORDER BY customers.CustomerName
            """,
            query, query, query, query, query,
        )
        return {"items": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list customers")
    finally:
        if connection is not None: connection.close()


@router.post("/customers", status_code=201)
def create_customer(payload: CustomerPayload, _: dict = Depends(admin_user)):
    customer_id = _clean(payload.customer_id) or _business_id("CUS")
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO dbo.Customers (CustomerID, CustomerName, ContactName, Phone, Tier, Status) VALUES (?, ?, ?, ?, ?, ?)",
            customer_id, _clean(payload.name), _clean(payload.contact_name),
            _clean(payload.phone), _clean(payload.tier) or "Standard",
            _clean(payload.customer_status) or "Active",
        )
        connection.commit()
        return {"success": True, "customer_id": customer_id}
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Mã khách hàng đã tồn tại.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create customer")
    finally:
        if connection is not None: connection.close()


@router.get("/customers/{customer_id}")
def customer_detail(customer_id: str, _: dict = Depends(admin_user)):
    """Return one customer with purchase totals and complete order history."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT customers.CustomerID AS customer_id,
                   customers.CustomerName AS name,
                   customers.ContactName AS contact_name,
                   customers.Phone AS phone,
                   customers.Tier AS tier,
                   customers.Status AS customer_status,
                   customers.CreatedAt AS created_at,
                   COUNT(orders.OrderID) AS order_count,
                   COALESCE(SUM(CASE WHEN orders.Status IN
                       (N'Completed', N'Paid', N'Hoàn thành')
                       THEN orders.TotalValue ELSE 0 END), 0) AS total_spent,
                   MAX(COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2))) AS last_purchase_at
            FROM dbo.Customers customers
            LEFT JOIN dbo.SalesOrders orders
                   ON orders.CustomerID = customers.CustomerID
            WHERE customers.CustomerID = ?
            GROUP BY customers.CustomerID, customers.CustomerName,
                     customers.ContactName, customers.Phone, customers.Tier,
                     customers.Status, customers.CreatedAt
            """,
            customer_id,
        )
        customer = _one(cursor)
        if customer is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng.")
        cursor.execute(
            """
            SELECT orders.OrderID AS order_id,
                   orders.TotalValue AS total_value,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaymentStatus, N'Paid') AS payment_status,
                   COALESCE(orders.OrderStatus, N'Completed') AS order_status,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                            CAST(orders.OrderDate AS datetime2)) AS paid_at,
                   users.FullName AS seller_name
            FROM dbo.SalesOrders orders
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
            WHERE orders.CustomerID = ?
            ORDER BY COALESCE(orders.PaidAt, orders.CreatedAt,
                              CAST(orders.OrderDate AS datetime2)) DESC
            """,
            customer_id,
        )
        customer["orders"] = _rows(cursor)
        return customer
    except HTTPException:
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load customer detail")
    finally:
        if connection is not None: connection.close()


@router.put("/customers/{customer_id}")
def update_customer(customer_id: str, payload: CustomerPayload, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE dbo.Customers SET CustomerName = ?, ContactName = ?, Phone = ?, Tier = ?, Status = ? WHERE CustomerID = ?",
            _clean(payload.name), _clean(payload.contact_name), _clean(payload.phone),
            _clean(payload.tier) or "Standard", _clean(payload.customer_status) or "Active",
            customer_id,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng.")
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update customer")
    finally:
        if connection is not None: connection.close()


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: str, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE dbo.Customers SET Status = N'Inactive' WHERE CustomerID = ?",
            customer_id,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng.")
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not delete customer")
    finally:
        if connection is not None: connection.close()
