# SPDX-License-Identifier: MIT
"""Unit checks for safe, repeatable SQL Server setup helpers."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database.connection import REQUIRED_SCHEMA  # noqa: E402
from database.init_database import configured_database_name, split_batches  # noqa: E402


class DatabaseSetupTests(unittest.TestCase):
    def test_go_batches_are_split_without_executing_comments(self):
        batches = split_batches("SELECT 1;\nGO\nSELECT 2;\nGO -- next batch\n")
        self.assertEqual(["SELECT 1;", "SELECT 2;"], batches)

    def test_database_name_is_validated_before_sql_substitution(self):
        with patch.dict(os.environ, {"DXLAB_SQL_DATABASE": "DXLabCore_Test"}):
            self.assertEqual("DXLabCore_Test", configured_database_name())
        with patch.dict(os.environ, {"DXLAB_SQL_DATABASE": "bad]; DROP DATABASE master;--"}):
            with self.assertRaises(RuntimeError):
                configured_database_name()

    def test_startup_contract_covers_all_used_business_tables(self):
        expected = {
            "Roles", "Users", "UserSessions", "Products", "Customers",
            "Promotions", "SalesOrders", "SalesOrderItems", "StockMovements",
            "PurchaseRequests", "Activities", "SystemSettings",
        }
        self.assertEqual(expected, set(REQUIRED_SCHEMA))


if __name__ == "__main__":
    unittest.main()
