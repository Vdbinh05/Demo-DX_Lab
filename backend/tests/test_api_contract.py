# SPDX-License-Identifier: MIT
"""Protect the public API surface while backend modules are reorganized."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from main import app  # noqa: E402


EXPECTED_PATHS = {
    "/admin/activities",
    "/admin/customers",
    "/admin/customers/{customer_id}",
    "/admin/dashboard",
    "/admin/inventory",
    "/admin/inventory/adjustments",
    "/admin/inventory/movements",
    "/admin/inventory/purchase-requests",
    "/admin/notifications",
    "/admin/orders",
    "/admin/orders/{order_id}",
    "/admin/products",
    "/admin/products/{product_id}",
    "/admin/promotions",
    "/admin/promotions/{promotion_id}",
    "/admin/revenue",
    "/admin/search",
    "/admin/settings",
    "/admin/users",
    "/admin/users/{user_id}",
    "/catalog/customers",
    "/catalog/products",
    "/catalog/promotions",
    "/change-password",
    "/health",
    "/login",
    "/logout",
    "/me",
    "/orders",
    "/orders/preview",
    "/orders/my-orders",
    "/orders/my-orders/{order_id}",
    "/register",
}


class ApiContractTests(unittest.TestCase):
    def test_all_business_paths_remain_registered(self):
        actual_paths = set(app.openapi()["paths"])
        self.assertEqual(EXPECTED_PATHS, actual_paths)

    def test_product_update_cannot_overwrite_inventory(self):
        document = app.openapi()
        operation = document["paths"]["/admin/products/{product_id}"]["put"]
        schema = operation["requestBody"]["content"]["application/json"]["schema"]
        schema_name = schema["$ref"].rsplit("/", 1)[-1]
        request_schema = document["components"]["schemas"][schema_name]
        properties = request_schema["properties"]
        self.assertNotIn("stock", properties)
        self.assertFalse(request_schema["additionalProperties"])

    def test_admin_order_detail_has_an_explicit_response_contract(self):
        document = app.openapi()
        operation = document["paths"]["/admin/orders/{order_id}"]["get"]
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        schema_name = schema["$ref"].rsplit("/", 1)[-1]
        properties = document["components"]["schemas"][schema_name]["properties"]
        expected = {
            "subtotal_value",
            "discount_value",
            "total_value",
            "promotion_title",
            "payment_status",
            "order_status",
            "items",
        }
        self.assertTrue(expected.issubset(properties))

    def test_admin_can_only_assign_supported_roles(self):
        document = app.openapi()
        schema = document["components"]["schemas"]["AdminAccountPayload"]
        role_schema = schema["properties"]["role_id"]
        self.assertEqual({"Admin", "Sales", "Warehouse"}, set(role_schema["enum"]))


if __name__ == "__main__":
    unittest.main()
