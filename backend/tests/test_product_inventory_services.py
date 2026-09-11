# SPDX-License-Identifier: MIT
"""Unit tests for product and inventory business rules after refactoring."""

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.schemas.admin import (
    InventoryAdjustment,
    ProductCreatePayload,
    ProductUpdatePayload,
    PurchaseRequestPayload,
)
from app.services.inventory import (
    InventoryRuleError,
    adjust_inventory,
    create_purchase_request,
    inventory_movements,
)
from app.services.products import (
    ProductRuleError,
    create_product,
    update_product,
)


CONNECTION = SimpleNamespace(cursor=lambda: object())
ADMIN = {"UserID": 7, "FullName": "Admin Demo"}


class ProductServiceTests(unittest.TestCase):
    @patch("app.services.products.business_id")
    @patch("app.services.products.ProductRepository")
    def test_create_product_trims_values_and_records_initial_stock(
        self,
        repository_type,
        business_id,
    ):
        repository = repository_type.return_value
        business_id.side_effect = ["SP-001", "SM-001"]
        payload = ProductCreatePayload(
            name="  Bàn phím cơ  ",
            category="  Phụ kiện  ",
            price=1_890_000,
            stock=7,
            reorder_level=2,
        )

        result = create_product(CONNECTION, payload, ADMIN)

        self.assertEqual(result, {"success": True, "product_id": "SP-001"})
        repository.insert.assert_called_once_with(
            product_id="SP-001",
            name="Bàn phím cơ",
            category="Phụ kiện",
            price=1_890_000,
            stock=7,
            reorder_level=2,
        )
        repository.insert_initial_stock.assert_called_once()
        repository.insert_create_activity.assert_called_once()

    @patch("app.services.products.ProductRepository")
    def test_update_product_rejects_unknown_product(self, repository_type):
        repository_type.return_value.get_for_update.return_value = None
        payload = ProductUpdatePayload(
            name="Bàn phím cơ",
            category="Phụ kiện",
            price=1_890_000,
            reorder_level=2,
        )

        with self.assertRaises(ProductRuleError) as context:
            update_product(CONNECTION, "SP-MISSING", payload, ADMIN)

        self.assertEqual(context.exception.status_code, 404)
        repository_type.return_value.update.assert_not_called()


class InventoryServiceTests(unittest.TestCase):
    def test_adjust_inventory_rejects_zero_change(self):
        payload = InventoryAdjustment(
            product_id="SP-001",
            quantity_change=0,
            reason="Kiểm kê",
        )

        with self.assertRaises(InventoryRuleError) as context:
            adjust_inventory(CONNECTION, payload, ADMIN)

        self.assertEqual(context.exception.status_code, 400)

    @patch("app.services.inventory.InventoryRepository")
    def test_adjust_inventory_never_allows_negative_stock(self, repository_type):
        repository = repository_type.return_value
        repository.get_product_for_update.return_value = SimpleNamespace(
            ProductName="Bàn phím cơ",
            Stock=3,
        )
        payload = InventoryAdjustment(
            product_id="SP-001",
            quantity_change=-4,
            reason="Kiểm kê thiếu",
        )

        with self.assertRaises(InventoryRuleError) as context:
            adjust_inventory(CONNECTION, payload, ADMIN)

        self.assertEqual(context.exception.status_code, 400)
        repository.set_stock.assert_not_called()

    def test_movement_history_rejects_reversed_date_range(self):
        with self.assertRaises(InventoryRuleError) as context:
            inventory_movements(
                CONNECTION,
                product_id=None,
                movement_type=None,
                start_date=date(2026, 9, 12),
                end_date=date(2026, 9, 1),
                page=1,
                page_size=30,
            )

        self.assertEqual(context.exception.status_code, 422)

    @patch("app.services.inventory.InventoryRepository")
    def test_purchase_request_rejects_unknown_product(self, repository_type):
        repository_type.return_value.get_product_for_request.return_value = None
        payload = PurchaseRequestPayload(
            product_id="SP-MISSING",
            quantity=5,
            reason="Bổ sung hàng",
        )

        with self.assertRaises(InventoryRuleError) as context:
            create_purchase_request(CONNECTION, payload, ADMIN)

        self.assertEqual(context.exception.status_code, 404)
        repository_type.return_value.insert_purchase_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
