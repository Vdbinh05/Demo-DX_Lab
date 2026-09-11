# SPDX-License-Identifier: MIT
"""Unit tests for role enforcement and server-side order quotations."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.api.dependencies import require_roles  # noqa: E402
from app.api.routes.catalog import product_catalog_user, sales_catalog_user  # noqa: E402
from app.schemas.orders import OrderItemPayload, OrderQuotePayload  # noqa: E402
from app.services.orders import OrderRuleError, build_quote, ensure_confirmed_total  # noqa: E402


class FakeOrderRepository:
    def __init__(self, *, stock: int = 10, tier: str = "Standard"):
        self.stock = stock
        self.tier = tier

    def get_customer(self, customer_id: str, *, lock: bool = False):
        return SimpleNamespace(CustomerID=customer_id, CustomerName="Khách test", Tier=self.tier)

    def get_product(self, product_id: str, *, lock: bool = False):
        return SimpleNamespace(
            ProductID=product_id,
            ProductName="Sản phẩm test",
            Category="Phụ kiện",
            Price=200_000,
            Stock=self.stock,
        )

    def get_active_promotion(self, promotion_id: str, *, lock: bool = False):
        return SimpleNamespace(
            PromotionID=promotion_id,
            Title="Giảm 10%",
            CustomerTier=None,
            DiscountType="PERCENT",
            DiscountValue=10,
            MinOrderValue=0,
            MaxUses=100,
            UsedCount=0,
            AppliedProductID=None,
            AppliedCategory=None,
        )


class AuthorizationTests(unittest.TestCase):
    def test_sales_role_is_accepted(self):
        dependency = require_roles("Sales")
        user = {"RoleID": "Sales"}
        self.assertIs(dependency(user), user)

    def test_warehouse_role_cannot_create_sales_order(self):
        dependency = require_roles("Sales")
        with self.assertRaises(HTTPException) as context:
            dependency({"RoleID": "Warehouse"})
        self.assertEqual(context.exception.status_code, 403)

    def test_warehouse_can_only_read_the_product_catalog(self):
        user = {"RoleID": "Warehouse"}
        self.assertIs(product_catalog_user(user), user)
        with self.assertRaises(HTTPException) as context:
            sales_catalog_user(user)
        self.assertEqual(context.exception.status_code, 403)


class OrderQuoteTests(unittest.TestCase):
    def test_quote_uses_server_price_and_promotion_rule(self):
        payload = OrderQuotePayload(
            customer_id="CUS-1",
            promotion_id="PROMO-10",
            items=[OrderItemPayload(product_id="SP-1", quantity=2)],
        )
        quote = build_quote(FakeOrderRepository(), payload, lock=False)
        self.assertEqual(int(quote["subtotal_value"]), 400_000)
        self.assertEqual(int(quote["discount_value"]), 40_000)
        self.assertEqual(int(quote["total_value"]), 360_000)

    def test_quote_rejects_insufficient_stock(self):
        payload = OrderQuotePayload(
            customer_id="CUS-1",
            items=[OrderItemPayload(product_id="SP-1", quantity=2)],
        )
        with self.assertRaises(OrderRuleError) as context:
            build_quote(FakeOrderRepository(stock=1), payload, lock=False)
        self.assertEqual(int(context.exception.status_code), 409)

    def test_checkout_rejects_a_total_that_changed_after_preview(self):
        with self.assertRaises(OrderRuleError) as context:
            ensure_confirmed_total(350_000, 360_000)
        self.assertEqual(int(context.exception.status_code), 409)
        ensure_confirmed_total(360_000, 360_000)


if __name__ == "__main__":
    unittest.main()
