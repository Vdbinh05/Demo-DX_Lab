"""Transactional sales order APIs for authenticated employees."""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core import current_user, get_connection


router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)
PAID_STATUSES = ("Paid", "Completed", "Hoàn thành")


class OrderItemPayload(BaseModel):
    product_id: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=1, le=999)


class CreateOrderPayload(BaseModel):
    customer_id: str = Field(min_length=1, max_length=20)
    items: list[OrderItemPayload] = Field(min_length=1, max_length=100)
    payment_method: Literal["Cash", "BankTransfer"] = "Cash"


def _order_id() -> str:
    return f"SO-{datetime.now():%y%m%d-%H%M%S}-{uuid.uuid4().hex[:5].upper()}"


def _movement_id() -> str:
    return f"SM-{datetime.now():%y%m%d}-{uuid.uuid4().hex[:8].upper()}"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: CreateOrderPayload, user: dict = Depends(current_user)):
    """Create a paid POS order and reduce stock in one SQL transaction."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        customer = cursor.execute(
            """
            SELECT CustomerID, CustomerName
            FROM dbo.Customers WITH (UPDLOCK, ROWLOCK)
            WHERE CustomerID = ? AND LOWER(COALESCE(Status, N'Active')) = N'active'
            """,
            payload.customer_id,
        ).fetchone()
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khách hàng không tồn tại hoặc đã ngừng hoạt động.",
            )

        quantities: dict[str, int] = {}
        for item in payload.items:
            product_id = item.product_id.strip()
            quantities[product_id] = quantities.get(product_id, 0) + item.quantity

        order_lines = []
        total = Decimal(0)
        for product_id in sorted(quantities):
            quantity = quantities[product_id]
            product = cursor.execute(
                """
                SELECT ProductID, ProductName, Price, Stock
                FROM dbo.Products WITH (UPDLOCK, ROWLOCK)
                WHERE ProductID = ?
                """,
                product_id,
            ).fetchone()
            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sản phẩm {product_id} không tồn tại.",
                )
            if int(product.Stock) < quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"{product.ProductName} chỉ còn {product.Stock} sản phẩm; "
                        f"không đủ để bán {quantity}."
                    ),
                )

            unit_price = Decimal(product.Price)
            subtotal = unit_price * quantity
            total += subtotal
            order_lines.append(
                {
                    "product_id": product.ProductID,
                    "name": product.ProductName,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                }
            )

        order_id = _order_id()
        cursor.execute(
            """
            INSERT INTO dbo.SalesOrders
                (OrderID, CustomerID, CreatedBy, TotalValue, Status, OrderDate,
                 PaymentMethod, CreatedAt, PaidAt)
            VALUES (?, ?, ?, ?, N'Paid', CONVERT(date, GETDATE()), ?,
                    SYSDATETIME(), SYSDATETIME())
            """,
            order_id,
            payload.customer_id,
            int(user["UserID"]),
            total,
            payload.payment_method,
        )

        for line in order_lines:
            cursor.execute(
                """
                INSERT INTO dbo.SalesOrderItems
                    (OrderID, ProductID, Quantity, UnitPrice)
                VALUES (?, ?, ?, ?)
                """,
                order_id,
                line["product_id"],
                line["quantity"],
                line["unit_price"],
            )
            cursor.execute(
                """
                UPDATE dbo.Products
                SET Stock = Stock - ?
                WHERE ProductID = ? AND Stock >= ?
                """,
                line["quantity"],
                line["product_id"],
                line["quantity"],
            )
            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tồn kho {line['name']} vừa thay đổi. Vui lòng thử lại.",
                )
            cursor.execute(
                """
                INSERT INTO dbo.StockMovements
                    (MovementID, ProductID, MovementType, Quantity,
                     ReferenceID, MovementDate)
                VALUES (?, ?, 'OUT', ?, ?, CONVERT(date, GETDATE()))
                """,
                _movement_id(),
                line["product_id"],
                line["quantity"],
                order_id,
            )

        cursor.execute(
            """
            INSERT INTO dbo.Activities (ActivityTime, Description, Category)
            VALUES (SYSDATETIME(), ?, N'Sales')
            """,
            f"{user['Username']} đã thanh toán đơn {order_id}",
        )
        connection.commit()

        return {
            "order_id": order_id,
            "customer_id": customer.CustomerID,
            "customer_name": customer.CustomerName,
            "seller_id": user["UserID"],
            "seller_name": user["FullName"],
            "payment_method": payload.payment_method,
            "status": "Paid",
            "total_value": int(total),
            "items": [
                {**line, "unit_price": int(line["unit_price"]), "subtotal": int(line["subtotal"])}
                for line in order_lines
            ],
        }
    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None:
            connection.rollback()
        logger.exception("Could not create sales order")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tạo đơn hàng trong SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@router.get("/my-orders")
def my_orders(user: dict = Depends(current_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS total_orders,
                   COALESCE(SUM(TotalValue), 0) AS total_revenue,
                   COALESCE(SUM(CASE WHEN OrderDate = CONVERT(date, GETDATE())
                                     THEN 1 ELSE 0 END), 0) AS today_orders,
                   COALESCE(SUM(CASE WHEN OrderDate = CONVERT(date, GETDATE())
                                     THEN TotalValue ELSE 0 END), 0) AS today_revenue
            FROM dbo.SalesOrders
            WHERE CreatedBy = ?
              AND Status IN (N'Paid', N'Completed', N'Hoàn thành')
            """,
            int(user["UserID"]),
        )
        summary = cursor.fetchone()
        cursor.execute(
            """
            SELECT orders.OrderID AS order_id,
                   customers.CustomerName AS customer,
                   orders.TotalValue AS total_value,
                   orders.PaymentMethod AS payment_method,
                   orders.Status AS order_status,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                            CAST(orders.OrderDate AS datetime2)) AS paid_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            WHERE orders.CreatedBy = ?
              AND orders.Status IN (N'Paid', N'Completed', N'Hoàn thành')
            ORDER BY COALESCE(orders.PaidAt, orders.CreatedAt,
                              CAST(orders.OrderDate AS datetime2)) DESC
            """,
            int(user["UserID"]),
        )
        items = [
            {
                "order_id": row.order_id,
                "customer": row.customer,
                "total_value": int(row.total_value),
                "payment_method": row.payment_method or "Cash",
                "order_status": row.order_status,
                "paid_at": row.paid_at.isoformat() if row.paid_at else None,
            }
            for row in cursor.fetchall()
        ]
        return {
            "summary": {
                "total_orders": int(summary.total_orders),
                "total_revenue": int(summary.total_revenue),
                "today_orders": int(summary.today_orders),
                "today_revenue": int(summary.today_revenue),
            },
            "items": items,
        }
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not list employee orders")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải đơn hàng của nhân viên từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()
