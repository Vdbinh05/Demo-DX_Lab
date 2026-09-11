# SPDX-License-Identifier: MIT
"""Non-destructive smoke test for the paid POS order workflow.

Run while the local API is listening on port 8000. The script creates one
temporary order, verifies idempotency and Admin visibility, then removes the
order and restores stock even when an assertion fails.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database.connection import get_connection  # noqa: E402


API_URL = os.getenv("DXLAB_TEST_API_URL", "http://127.0.0.1:8000").rstrip("/")


def request_json(path: str, *, method: str = "GET", body=None, token=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{API_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read().decode("utf-8"))
        raise AssertionError(f"{method} {path} -> {error.code}: {payload}") from error


def login(username: str, password: str, portal: str) -> str:
    status, payload = request_json(
        "/login",
        method="POST",
        body={"username": username, "password": password, "portal": portal},
    )
    assert status == 200
    return payload["access_token"]


def cleanup_order(order_id: str) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        promotion = cursor.execute(
            "SELECT PromotionID FROM dbo.SalesOrders WHERE OrderID = ?", order_id
        ).fetchone()
        lines = cursor.execute(
            "SELECT ProductID, Quantity FROM dbo.SalesOrderItems WHERE OrderID = ?",
            order_id,
        ).fetchall()
        for line in lines:
            cursor.execute(
                "UPDATE dbo.Products SET Stock = Stock + ? WHERE ProductID = ?",
                int(line.Quantity),
                line.ProductID,
            )
        cursor.execute("DELETE FROM dbo.StockMovements WHERE ReferenceID = ?", order_id)
        cursor.execute(
            "DELETE FROM dbo.Activities WHERE Description LIKE ?", f"%{order_id}%"
        )
        cursor.execute("DELETE FROM dbo.SalesOrders WHERE OrderID = ?", order_id)
        if promotion and promotion.PromotionID:
            cursor.execute(
                "UPDATE dbo.Promotions SET UsedCount = CASE WHEN UsedCount > 0 THEN UsedCount - 1 ELSE 0 END WHERE PromotionID = ?",
                promotion.PromotionID,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> int:
    order_id = ""
    sales_token = ""
    admin_token = ""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        product = cursor.execute(
            """
            SELECT TOP 1 products.ProductID, products.Stock,
                   promotions.PromotionID, promotions.DiscountValue
            FROM dbo.Products products
            JOIN dbo.Promotions promotions
              ON LOWER(promotions.AppliedCategory) = LOWER(products.Category)
            WHERE products.Stock > 0
              AND LOWER(promotions.Status) = N'active'
              AND promotions.DiscountType = 'PERCENT'
              AND promotions.DiscountValue > 0
              AND promotions.StartDate <= CONVERT(date, GETDATE())
              AND promotions.EndDate >= CONVERT(date, GETDATE())
            ORDER BY products.ProductID
            """
        ).fetchone()
        assert product is not None
        customer = cursor.execute(
            """
            SELECT TOP 1 customers.CustomerID
            FROM dbo.Customers customers
            JOIN dbo.Promotions promotions
              ON LOWER(promotions.CustomerTier) = LOWER(customers.Tier)
            WHERE promotions.PromotionID = ?
              AND LOWER(COALESCE(customers.Status, N'Active')) = N'active'
            ORDER BY customers.CustomerID
            """,
            product.PromotionID,
        ).fetchone()
        assert customer is not None
        product_id = str(product.ProductID)
        customer_id = str(customer.CustomerID)
        initial_stock = int(product.Stock)
        promotion_id = str(product.PromotionID)
    finally:
        connection.close()

    try:
        sales_token = login("sales.demo", "Sales@123", "employee")
        admin_token = login("admin.demo", "Admin@123", "admin")
        key = f"smoke-{uuid.uuid4()}"
        payload = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1}],
            "payment_method": "Cash",
            "idempotency_key": key,
            "promotion_id": promotion_id,
        }

        status, preview = request_json(
            "/orders/preview",
            method="POST",
            body={
                "customer_id": customer_id,
                "items": payload["items"],
                "promotion_id": promotion_id,
            },
            token=sales_token,
        )
        assert status == 200
        assert preview["discount_value"] > 0
        assert preview["subtotal_value"] > preview["total_value"]
        payload["expected_total_value"] = preview["total_value"]

        status, created = request_json(
            "/orders", method="POST", body=payload, token=sales_token
        )
        if status == 201:
            order_id = str(created.get("order_id") or "")
        assert status == 201 and created["duplicate"] is False
        assert created["payment_status"] == "Paid"
        assert created["order_status"] == "Completed"
        assert created["discount_value"] > 0
        assert created["subtotal_value"] > created["total_value"]
        assert created["promotion_id"] == promotion_id
        assert created["subtotal_value"] == preview["subtotal_value"]
        assert created["discount_value"] == preview["discount_value"]
        assert created["total_value"] == preview["total_value"]
        assert order_id

        status, repeated = request_json(
            "/orders", method="POST", body=payload, token=sales_token
        )
        assert status == 201 and repeated["duplicate"] is True
        assert repeated["order_id"] == order_id

        conflicting_payload = {
            **payload,
            "items": [{"product_id": product_id, "quantity": 2}],
        }
        try:
            request_json(
                "/orders",
                method="POST",
                body=conflicting_payload,
                token=sales_token,
            )
        except AssertionError as error:
            assert "409" in str(error)
        else:
            raise AssertionError("A changed request reused an idempotency key without 409")

        status, detail = request_json(
            f"/admin/orders/{order_id}", token=admin_token
        )
        assert status == 200 and detail["order_id"] == order_id
        assert detail["items"][0]["product_id"] == product_id

        connection = get_connection()
        try:
            cursor = connection.cursor()
            stock = cursor.execute(
                "SELECT Stock FROM dbo.Products WHERE ProductID = ?", product_id
            ).fetchone()
            order_count = cursor.execute(
                "SELECT COUNT(*) FROM dbo.SalesOrders WHERE IdempotencyKey = ?", key
            ).fetchone()[0]
            movement_count = cursor.execute(
                "SELECT COUNT(*) FROM dbo.StockMovements WHERE ReferenceID = ?", order_id
            ).fetchone()[0]
            assert int(stock.Stock) == initial_stock - 1
            assert int(order_count) == 1
            assert int(movement_count) == 1
        finally:
            connection.close()

        print(
            "PASS: paid order, promotion discount, stock reduction, Admin detail "
            "and idempotent retry were verified."
        )
        return 0
    finally:
        if order_id:
            cleanup_order(order_id)
            print(f"CLEANUP: removed temporary order {order_id} and restored stock.")
        for token in (sales_token, admin_token):
            if token:
                try:
                    request_json("/logout", method="POST", token=token)
                except AssertionError:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
