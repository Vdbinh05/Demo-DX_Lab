# SPDX-License-Identifier: MIT
"""Real SQL Server APIs used by the administrator workspace."""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from core import current_user, get_connection, hash_password, require_admin


router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class ProductPayload(BaseModel):
    product_id: str | None = Field(default=None, max_length=20)
    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=50)
    price: int = Field(ge=0)
    stock: int = Field(ge=0)
    reorder_level: int = Field(ge=0)


class CustomerPayload(BaseModel):
    customer_id: str | None = Field(default=None, max_length=20)
    name: str = Field(min_length=2, max_length=255)
    contact_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    tier: str = Field(default="Standard", max_length=30)
    customer_status: str = Field(default="Active", max_length=20)


class InventoryAdjustment(BaseModel):
    product_id: str
    quantity_change: int
    reason: str = Field(min_length=3, max_length=255)


class AdminAccountPayload(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role_id: str = Field(default="Sales", max_length=20)


class AccountPatch(BaseModel):
    role_id: str | None = Field(default=None, max_length=20)
    account_status: str | None = Field(default=None, max_length=20)


class SettingsPayload(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    company_phone: str = Field(default="", max_length=50)
    company_address: str = Field(default="", max_length=500)
    tax_code: str = Field(default="", max_length=50)


def admin_user(user: dict = Depends(current_user)) -> dict:
    return require_admin(user)


def _json_value(value):
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _rows(cursor) -> list[dict]:
    columns = [column[0] for column in cursor.description]
    return [
        {columns[index]: _json_value(value) for index, value in enumerate(row)}
        for row in cursor.fetchall()
    ]


def _one(cursor) -> dict | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return {columns[index]: _json_value(value) for index, value in enumerate(row)}


def _db_error(exc: Exception, message: str):
    logger.exception(message)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Không thể đọc hoặc cập nhật dữ liệu SQL Server.",
    ) from exc


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _business_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now():%y%m%d}-{uuid.uuid4().hex[:6].upper()}"


@router.get("/dashboard")
def dashboard(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                    AND OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
                    THEN TotalValue ELSE 0 END), 0) AS month_revenue,
                SUM(CASE WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                    AND OrderDate = CONVERT(date, GETDATE()) THEN 1 ELSE 0 END) AS today_orders,
                COALESCE(SUM(CASE WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                    AND OrderDate = CONVERT(date, GETDATE()) THEN TotalValue ELSE 0 END), 0) AS today_revenue,
                SUM(CASE WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                    AND OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
                    THEN 1 ELSE 0 END) AS month_orders
            FROM dbo.SalesOrders
            """
        )
        metrics = _one(cursor)
        cursor.execute("SELECT COUNT(*) AS customer_count FROM dbo.Customers")
        metrics.update(_one(cursor))
        cursor.execute("SELECT COUNT(*) AS account_count FROM dbo.Users")
        metrics.update(_one(cursor))
        cursor.execute("SELECT COUNT(*) AS low_stock_count FROM dbo.Products WHERE Stock <= ReorderLevel")
        metrics.update(_one(cursor))
        cursor.execute(
            """
            WITH month_series AS
            (
                SELECT 0 AS offset_number UNION ALL SELECT 1 UNION ALL SELECT 2
                UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ), months AS
            (
                SELECT DATEADD(month, -offset_number,
                    DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS month_start
                FROM month_series
            )
            SELECT YEAR(months.month_start) AS [year], MONTH(months.month_start) AS [month],
                   COALESCE(SUM(orders.TotalValue), 0) AS revenue
            FROM months
            LEFT JOIN dbo.SalesOrders orders
              ON orders.OrderDate >= months.month_start
             AND orders.OrderDate < DATEADD(month, 1, months.month_start)
             AND orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
            GROUP BY months.month_start ORDER BY months.month_start
            """
        )
        monthly_revenue = _rows(cursor)
        cursor.execute(
            """
            SELECT TOP 5 products.ProductID AS product_id,
                   products.ProductName AS name, products.Category AS category,
                   SUM(items.Quantity) AS sold_quantity,
                   SUM(items.Quantity * items.UnitPrice) AS revenue
            FROM dbo.SalesOrderItems items
            JOIN dbo.Products products ON products.ProductID = items.ProductID
            JOIN dbo.SalesOrders orders ON orders.OrderID = items.OrderID
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND orders.OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            GROUP BY products.ProductID, products.ProductName, products.Category
            ORDER BY sold_quantity DESC, revenue DESC
            """
        )
        top_products = _rows(cursor)
        cursor.execute(
            """
            SELECT TOP 6 orders.OrderID AS order_id, customers.CustomerName AS customer,
                   COALESCE(users.FullName, N'Không xác định') AS seller,
                   orders.TotalValue AS total_value, orders.Status AS order_status,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2)) AS created_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
            ORDER BY COALESCE(orders.PaidAt, orders.CreatedAt,
                CAST(orders.OrderDate AS datetime2)) DESC
            """
        )
        recent_orders = _rows(cursor)
        cursor.execute(
            """
            SELECT DISTINCT customers.CustomerID AS customer_id,
                   customers.CustomerName AS name, customers.ContactName AS contact_name,
                   customers.Phone AS phone
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND orders.OrderDate = CONVERT(date, GETDATE())
            ORDER BY customers.CustomerName
            """
        )
        return {
            "metrics": metrics,
            "monthly_revenue": monthly_revenue,
            "top_products": top_products,
            "recent_orders": recent_orders,
            "today_customers": _rows(cursor),
            "generated_at": datetime.now().isoformat(),
        }
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not build admin dashboard")
    finally:
        if connection is not None:
            connection.close()


@router.get("/revenue")
def revenue(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(TotalValue), 0) AS month_revenue,
                   COUNT(*) AS paid_orders,
                   COALESCE(AVG(CAST(TotalValue AS decimal(18, 2))), 0) AS average_order,
                   COUNT(DISTINCT CustomerID) AS purchasing_customers
            FROM dbo.SalesOrders
            WHERE Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            """
        )
        summary = _one(cursor)
        cursor.execute(
            """
            SELECT products.Category AS category,
                   SUM(items.Quantity * items.UnitPrice) AS revenue,
                   SUM(items.Quantity) AS quantity
            FROM dbo.SalesOrderItems items
            JOIN dbo.Products products ON products.ProductID = items.ProductID
            JOIN dbo.SalesOrders orders ON orders.OrderID = items.OrderID
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND orders.OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            GROUP BY products.Category ORDER BY revenue DESC
            """
        )
        categories = _rows(cursor)
        cursor.execute(
            """
            WITH month_series AS
            (
                SELECT 0 AS offset_number UNION ALL SELECT 1 UNION ALL SELECT 2
                UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ), months AS
            (
                SELECT DATEADD(month, -offset_number,
                    DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS month_start
                FROM month_series
            )
            SELECT YEAR(months.month_start) AS [year], MONTH(months.month_start) AS [month],
                   COALESCE(SUM(orders.TotalValue), 0) AS revenue,
                   COUNT(orders.OrderID) AS order_count
            FROM months
            LEFT JOIN dbo.SalesOrders orders
              ON orders.OrderDate >= months.month_start
             AND orders.OrderDate < DATEADD(month, 1, months.month_start)
             AND orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
            GROUP BY months.month_start ORDER BY months.month_start
            """
        )
        return {"summary": summary, "categories": categories, "months": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load revenue report")
    finally:
        if connection is not None:
            connection.close()


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
                   orders.TotalValue AS total_value, orders.Status AS order_status,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2)) AS created_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
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


@router.get("/orders/{order_id}")
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
                   orders.TotalValue AS total_value, orders.Status AS order_status,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2)) AS created_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
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


@router.get("/products")
def list_products(q: str = Query(default="", max_length=100), _: dict = Depends(admin_user)):
    query = _clean(q)
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT products.ProductID AS product_id, products.ProductName AS name,
                   products.Category AS category, products.Price AS price,
                   products.Stock AS stock, products.ReorderLevel AS reorder_level,
                   COALESCE(SUM(CASE WHEN orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
                       THEN items.Quantity ELSE 0 END), 0) AS sold_quantity
            FROM dbo.Products products
            LEFT JOIN dbo.SalesOrderItems items ON items.ProductID = products.ProductID
            LEFT JOIN dbo.SalesOrders orders ON orders.OrderID = items.OrderID
            WHERE (? = '' OR products.ProductID LIKE '%' + ? + '%'
                OR products.ProductName LIKE N'%' + ? + N'%'
                OR products.Category LIKE N'%' + ? + N'%')
            GROUP BY products.ProductID, products.ProductName, products.Category,
                     products.Price, products.Stock, products.ReorderLevel
            ORDER BY products.ProductName
            """,
            query, query, query, query,
        )
        return {"items": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list products")
    finally:
        if connection is not None:
            connection.close()


@router.post("/products", status_code=201)
def create_product(payload: ProductPayload, user: dict = Depends(admin_user)):
    product_id = _clean(payload.product_id) or _business_id("SP")
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO dbo.Products (ProductID, ProductName, Category, Price, Stock, ReorderLevel) VALUES (?, ?, ?, ?, ?, ?)",
            product_id, _clean(payload.name), _clean(payload.category),
            payload.price, payload.stock, payload.reorder_level,
        )
        cursor.execute(
            "INSERT INTO dbo.Activities (ActivityTime, Description, Category) VALUES (?, ?, ?)",
            datetime.now().strftime("%H:%M"),
            f"{user['FullName']} đã thêm sản phẩm {product_id}", "Product",
        )
        connection.commit()
        return {"success": True, "product_id": product_id}
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Mã sản phẩm đã tồn tại.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create product")
    finally:
        if connection is not None: connection.close()


@router.put("/products/{product_id}")
def update_product(product_id: str, payload: ProductPayload, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE dbo.Products SET ProductName = ?, Category = ?, Price = ?, Stock = ?, ReorderLevel = ? WHERE ProductID = ?",
            _clean(payload.name), _clean(payload.category), payload.price,
            payload.stock, payload.reorder_level, product_id,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update product")
    finally:
        if connection is not None: connection.close()


@router.delete("/products/{product_id}")
def delete_product(product_id: str, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM dbo.Products WHERE ProductID = ?", product_id)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Sản phẩm đã phát sinh giao dịch nên không thể xóa lịch sử.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not delete product")
    finally:
        if connection is not None: connection.close()


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
        cursor.execute("DELETE FROM dbo.Customers WHERE CustomerID = ?", customer_id)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng.")
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Khách hàng đã có đơn hàng nên không thể xóa lịch sử.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not delete customer")
    finally:
        if connection is not None: connection.close()


@router.get("/inventory")
def inventory(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS total_products,
                   COALESCE(SUM(CASE WHEN Stock > ReorderLevel THEN 1 ELSE 0 END), 0) AS healthy_count,
                   COALESCE(SUM(CASE WHEN Stock > 0 AND Stock <= ReorderLevel THEN 1 ELSE 0 END), 0) AS low_count,
                   COALESCE(SUM(CASE WHEN Stock = 0 THEN 1 ELSE 0 END), 0) AS out_count
            FROM dbo.Products
            """
        )
        summary = _one(cursor)
        cursor.execute(
            """
            SELECT ProductID AS product_id, ProductName AS name, Category AS category,
                   Stock AS stock, ReorderLevel AS reorder_level, Price AS price
            FROM dbo.Products WHERE Stock <= ReorderLevel
            ORDER BY CASE WHEN Stock = 0 THEN 0 ELSE 1 END, Stock
            """
        )
        return {"summary": summary, "alerts": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load inventory")
    finally:
        if connection is not None: connection.close()


@router.post("/inventory/adjustments")
def adjust_inventory(payload: InventoryAdjustment, user: dict = Depends(admin_user)):
    if payload.quantity_change == 0:
        raise HTTPException(status_code=400, detail="Số lượng điều chỉnh phải khác 0.")
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT ProductName, Stock FROM dbo.Products WITH (UPDLOCK, ROWLOCK) WHERE ProductID = ?", payload.product_id)
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
        new_stock = int(row.Stock) + payload.quantity_change
        if new_stock < 0:
            raise HTTPException(status_code=400, detail="Tồn kho không thể nhỏ hơn 0.")
        cursor.execute("UPDATE dbo.Products SET Stock = ? WHERE ProductID = ?", new_stock, payload.product_id)
        cursor.execute(
            "INSERT INTO dbo.StockMovements (MovementID, ProductID, MovementType, Quantity, ReferenceID, MovementDate) VALUES (?, ?, ?, ?, ?, CONVERT(date, GETDATE()))",
            _business_id("SM"), payload.product_id,
            "IN" if payload.quantity_change > 0 else "OUT",
            abs(payload.quantity_change), "ADJUSTMENT",
        )
        cursor.execute(
            "INSERT INTO dbo.Activities (ActivityTime, Description, Category) VALUES (?, ?, ?)",
            datetime.now().strftime("%H:%M"),
            f"{user['FullName']} điều chỉnh {payload.product_id}: {payload.reason}", "Inventory",
        )
        connection.commit()
        return {"success": True, "stock": new_stock}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not adjust inventory")
    finally:
        if connection is not None: connection.close()


@router.get("/users")
def list_users(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT users.UserID AS user_id, users.FullName AS full_name,
                   users.Username AS username, users.RoleID AS role_id,
                   users.Status AS account_status, users.CreatedAt AS created_at,
                   users.LastLoginAt AS last_login_at
            FROM dbo.Users users ORDER BY users.CreatedAt DESC, users.UserID DESC
            """
        )
        users = _rows(cursor)
        cursor.execute("SELECT RoleID AS role_id, RoleName AS role_name FROM dbo.Roles ORDER BY RoleName")
        return {"items": users, "roles": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list users")
    finally:
        if connection is not None: connection.close()


@router.post("/users", status_code=201)
def create_user(payload: AdminAccountPayload, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM dbo.Roles WHERE RoleID = ?", _clean(payload.role_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Vai trò không hợp lệ.")
        cursor.execute(
            "INSERT INTO dbo.Users (Username, PasswordHash, FullName, RoleID, Status) VALUES (?, ?, ?, ?, N'Active')",
            _clean(payload.username), hash_password(payload.password),
            _clean(payload.full_name), _clean(payload.role_id),
        )
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create user")
    finally:
        if connection is not None: connection.close()


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: AccountPatch, user: dict = Depends(admin_user)):
    requested_role = _clean(payload.role_id) if payload.role_id is not None else None
    requested_status = _clean(payload.account_status) if payload.account_status is not None else None

    if requested_status is not None and requested_status not in {"Active", "Locked"}:
        raise HTTPException(status_code=400, detail="Trạng thái tài khoản không hợp lệ.")
    if user_id == user["UserID"] and requested_role is not None and requested_role.lower() != "admin":
        raise HTTPException(status_code=400, detail="Bạn không thể tự hạ quyền tài khoản Admin đang đăng nhập.")
    if user_id == user["UserID"] and requested_status is not None and requested_status != "Active":
        raise HTTPException(status_code=400, detail="Bạn không thể tự khóa tài khoản đang đăng nhập.")
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT RoleID, Status FROM dbo.Users WITH (UPDLOCK, HOLDLOCK) WHERE UserID = ?",
            user_id,
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
        if requested_role is not None:
            cursor.execute("SELECT 1 FROM dbo.Roles WHERE RoleID = ?", requested_role)
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Vai trò không hợp lệ.")

        removes_active_admin = (
            str(target.RoleID).lower() == "admin"
            and str(target.Status).lower() == "active"
            and (
                (requested_role is not None and requested_role.lower() != "admin")
                or (requested_status is not None and requested_status != "Active")
            )
        )
        if removes_active_admin:
            cursor.execute(
                "SELECT COUNT(*) FROM dbo.Users WITH (UPDLOCK, HOLDLOCK) "
                "WHERE LOWER(RoleID) = 'admin' AND LOWER(Status) = 'active'"
            )
            if int(cursor.fetchone()[0]) <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Hệ thống phải luôn còn ít nhất một tài khoản Admin đang hoạt động.",
                )

        if requested_role is not None:
            cursor.execute("UPDATE dbo.Users SET RoleID = ? WHERE UserID = ?", requested_role, user_id)
        if requested_status is not None:
            cursor.execute("UPDATE dbo.Users SET Status = ? WHERE UserID = ?", requested_status, user_id)
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update user")
    finally:
        if connection is not None: connection.close()


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
