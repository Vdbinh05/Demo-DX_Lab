# SPDX-License-Identifier: MIT
"""Regression tests for administrator input and inventory boundaries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi import HTTPException
from pydantic import ValidationError


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes.admin_users import create_user  # noqa: E402
from app.schemas.admin import AdminAccountPayload, ProductUpdatePayload  # noqa: E402


class AdminValidationTests(unittest.TestCase):
    def test_product_metadata_update_rejects_stock(self):
        with self.assertRaises(ValidationError):
            ProductUpdatePayload.model_validate(
                {
                    "name": "Bàn phím cơ",
                    "category": "Phụ kiện",
                    "price": 1_890_000,
                    "reorder_level": 10,
                    "stock": 999,
                }
            )

    def test_admin_account_uses_the_shared_password_policy(self):
        payload = AdminAccountPayload(
            full_name="Nhân viên thử",
            username="sales.test",
            password="alllowercase1@",
            role_id="Sales",
        )
        with self.assertRaises(HTTPException) as context:
            create_user(payload, {"UserID": 1, "FullName": "Admin"})
        self.assertEqual(422, context.exception.status_code)

    def test_admin_account_rejects_unsafe_username_before_database_access(self):
        payload = AdminAccountPayload(
            full_name="Nhân viên thử",
            username="bad name",
            password="Strong@123",
            role_id="Sales",
        )
        with self.assertRaises(HTTPException) as context:
            create_user(payload, {"UserID": 1, "FullName": "Admin"})
        self.assertEqual(422, context.exception.status_code)


if __name__ == "__main__":
    unittest.main()
