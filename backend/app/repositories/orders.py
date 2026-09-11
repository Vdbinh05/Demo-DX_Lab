# SPDX-License-Identifier: MIT
"""SQL Server queries used by the sales-order service."""

from __future__ import annotations

import json
from typing import Any


class OrderRepository:
    """Keep SQL details out of FastAPI routes and business-rule functions."""

    def __init__(self, cursor):
        self.cursor = cursor

    def find_by_idempotency_key(self, idempotency_key: str):
        return self.cursor.execute(
            """
            SELECT OrderID, CreatedBy, RequestFingerprint
            FROM dbo.SalesOrders WITH (UPDLOCK, HOLDLOCK)
            WHERE IdempotencyKey = ?
            """,
            idempotency_key,
        ).fetchone()

    def get_customer(self, customer_id: str, *, lock: bool = False):
        hint = " WITH (UPDLOCK, ROWLOCK)" if lock else ""
        return self.cursor.execute(
            f"""
            SELECT CustomerID, CustomerName, Tier
            FROM dbo.Customers{hint}
            WHERE CustomerID = ? AND LOWER(COALESCE(Status, N'Active')) = N'active'
            """,
            customer_id,
        ).fetchone()

    def get_product(self, product_id: str, *, lock: bool = False):
        hint = " WITH (UPDLOCK, ROWLOCK)" if lock else ""
        return self.cursor.execute(
            f"""
            SELECT ProductID, ProductName, Category, Price, Stock
            FROM dbo.Products{hint}
            WHERE ProductID = ?
            """,
            product_id,
        ).fetchone()

    def get_active_promotion(self, promotion_id: str, *, lock: bool = False):
        hint = " WITH (UPDLOCK, HOLDLOCK)" if lock else ""
        return self.cursor.execute(
            f"""
            SELECT PromotionID, Title, CustomerTier, DiscountType, DiscountValue,
                   MinOrderValue, MaxUses, UsedCount, AppliedProductID,
                   AppliedCategory
            FROM dbo.Promotions{hint}
            WHERE PromotionID = ? AND LOWER(Status) = N'active'
              AND StartDate <= CONVERT(date, GETDATE())
              AND EndDate >= CONVERT(date, GETDATE())
            """,
            promotion_id,
        ).fetchone()

    def insert_order(
        self,
        *,
        order_id: str,
        customer_id: str,
        user_id: int,
        total,
        payment_method: str,
        idempotency_key: str,
        request_fingerprint: str,
        subtotal,
        discount,
        promotion_id: str | None,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.SalesOrders
                (OrderID, CustomerID, CreatedBy, TotalValue, Status, OrderDate,
                 PaymentMethod, CreatedAt, PaidAt, PaymentStatus, OrderStatus,
                 IdempotencyKey, RequestFingerprint, SubtotalValue,
                 DiscountValue, PromotionID)
            VALUES (?, ?, ?, ?, N'Paid', CONVERT(date, GETDATE()), ?,
                    SYSDATETIME(), SYSDATETIME(), N'Paid', N'Completed',
                    ?, ?, ?, ?, ?)
            """,
            order_id,
            customer_id,
            user_id,
            total,
            payment_method,
            idempotency_key,
            request_fingerprint,
            subtotal,
            discount,
            promotion_id,
        )

    def increment_promotion_usage(self, promotion_id: str) -> None:
        self.cursor.execute(
            """
            UPDATE dbo.Promotions
            SET UsedCount = UsedCount + 1, UpdatedAt = SYSDATETIME()
            WHERE PromotionID = ?
            """,
            promotion_id,
        )

    def insert_order_item(self, order_id: str, line: dict[str, Any]) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.SalesOrderItems
                (OrderID, ProductID, ProductNameSnapshot, Quantity, UnitPrice)
            VALUES (?, ?, ?, ?, ?)
            """,
            order_id,
            line["product_id"],
            line["name"],
            line["quantity"],
            line["unit_price"],
        )

    def decrement_stock(self, line: dict[str, Any]) -> bool:
        self.cursor.execute(
            """
            UPDATE dbo.Products
            SET Stock = Stock - ?
            WHERE ProductID = ? AND Stock >= ?
            """,
            line["quantity"],
            line["product_id"],
            line["quantity"],
        )
        return self.cursor.rowcount == 1

    def insert_stock_movement(
        self,
        *,
        movement_id: str,
        order_id: str,
        line: dict[str, Any],
        user_id: int,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.StockMovements
                (MovementID, ProductID, MovementType, Quantity,
                 ReferenceID, MovementDate, Reason, PerformedBy, CreatedAt)
            VALUES (?, ?, 'OUT', ?, ?, CONVERT(date, GETDATE()),
                    N'Bán hàng tại POS', ?, SYSDATETIME())
            """,
            movement_id,
            line["product_id"],
            line["quantity"],
            order_id,
            user_id,
        )

    def insert_order_activity(
        self,
        *,
        order_id: str,
        user: dict,
        subtotal,
        discount,
        total,
        promotion_id: str | None,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Sales', ?,
                    'CREATE_ORDER', 'SalesOrder', ?, ?)
            """,
            f"{user['Username']} đã thanh toán đơn {order_id}",
            int(user["UserID"]),
            order_id,
            json.dumps(
                {
                    "subtotal_value": int(subtotal),
                    "discount_value": int(discount),
                    "total_value": int(total),
                    "promotion_id": promotion_id,
                },
                ensure_ascii=False,
            ),
        )

    def order_response(self, order_id: str, *, duplicate: bool = False) -> dict:
        order = self.cursor.execute(
            """
            SELECT orders.OrderID, orders.CustomerID, customers.CustomerName,
                   orders.CreatedBy, users.FullName, orders.PaymentMethod,
                   COALESCE(orders.PaymentStatus, N'Paid') AS PaymentStatus,
                   COALESCE(orders.OrderStatus, N'Completed') AS OrderStatus,
                   COALESCE(orders.SubtotalValue, orders.TotalValue) AS SubtotalValue,
                   COALESCE(orders.DiscountValue, 0) AS DiscountValue,
                   orders.TotalValue, orders.PromotionID,
                   promotions.Title AS PromotionTitle,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                            CAST(orders.OrderDate AS datetime2)) AS PaidAt
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
            LEFT JOIN dbo.Promotions promotions ON promotions.PromotionID = orders.PromotionID
            WHERE orders.OrderID = ?
            """,
            order_id,
        ).fetchone()
        lines = self.cursor.execute(
            """
            SELECT items.ProductID,
                   COALESCE(items.ProductNameSnapshot, products.ProductName) AS ProductName,
                   items.Quantity, items.UnitPrice, items.SubTotal
            FROM dbo.SalesOrderItems items
            LEFT JOIN dbo.Products products ON products.ProductID = items.ProductID
            WHERE items.OrderID = ? ORDER BY items.ItemID
            """,
            order_id,
        ).fetchall()
        return {
            "order_id": order.OrderID,
            "customer_id": order.CustomerID,
            "customer_name": order.CustomerName,
            "seller_id": order.CreatedBy,
            "seller_name": order.FullName or "Không xác định",
            "payment_method": order.PaymentMethod or "Cash",
            "payment_status": order.PaymentStatus,
            "order_status": order.OrderStatus,
            "status": order.PaymentStatus,
            "subtotal_value": int(order.SubtotalValue),
            "discount_value": int(order.DiscountValue),
            "total_value": int(order.TotalValue),
            "promotion_id": order.PromotionID,
            "promotion_title": order.PromotionTitle,
            "paid_at": order.PaidAt.isoformat() if order.PaidAt else None,
            "duplicate": duplicate,
            "items": [
                {
                    "product_id": line.ProductID,
                    "name": line.ProductName,
                    "quantity": int(line.Quantity),
                    "unit_price": int(line.UnitPrice),
                    "subtotal": int(line.SubTotal),
                }
                for line in lines
            ],
        }

    def is_owned_order(self, order_id: str, user_id: int) -> bool:
        row = self.cursor.execute(
            "SELECT 1 FROM dbo.SalesOrders WHERE OrderID = ? AND CreatedBy = ?",
            order_id,
            user_id,
        ).fetchone()
        return row is not None

    def my_orders_summary(self, user_id: int):
        return self.cursor.execute(
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
            user_id,
        ).fetchone()

    def my_orders(self, user_id: int):
        return self.cursor.execute(
            """
            SELECT orders.OrderID AS order_id,
                   customers.CustomerName AS customer,
                   orders.TotalValue AS total_value,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaymentStatus, N'Paid') AS payment_status,
                   COALESCE(orders.OrderStatus, N'Completed') AS order_status,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                            CAST(orders.OrderDate AS datetime2)) AS paid_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            WHERE orders.CreatedBy = ?
              AND orders.Status IN (N'Paid', N'Completed', N'Hoàn thành')
            ORDER BY COALESCE(orders.PaidAt, orders.CreatedAt,
                              CAST(orders.OrderDate AS datetime2)) DESC
            """,
            user_id,
        ).fetchall()
