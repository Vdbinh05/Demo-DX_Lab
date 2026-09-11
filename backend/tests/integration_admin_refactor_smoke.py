# SPDX-License-Identifier: MIT
"""Rollback-only SQL smoke test for refactored administrator services."""

from __future__ import annotations

import uuid
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database.connection import get_connection
from app.schemas.admin import (
    InventoryAdjustment,
    ProductCreatePayload,
    ProductUpdatePayload,
    PurchaseRequestPayload,
)
from app.services.inventory import adjust_inventory, create_purchase_request
from app.services.products import create_product, update_product
from app.services.users import NewUser, UserChange, create_user, update_user


def main() -> None:
    connection = get_connection()
    try:
        actor_row = connection.cursor().execute(
            """
            SELECT TOP 1 UserID, FullName
            FROM dbo.Users
            WHERE RoleID = 'Admin' AND Status = 'Active'
            ORDER BY UserID
            """
        ).fetchone()
        if actor_row is None:
            raise RuntimeError("Smoke test requires one active Admin account.")
        actor = {"UserID": int(actor_row.UserID), "FullName": actor_row.FullName}

        suffix = uuid.uuid4().hex[:8]
        product_id = f"SMOKE-{suffix.upper()}"
        create_product(
            connection,
            ProductCreatePayload(
                product_id=product_id,
                name="Sản phẩm smoke test",
                category="Kiểm thử",
                price=10_000,
                stock=0,
                reorder_level=2,
            ),
            actor,
        )
        update_product(
            connection,
            product_id,
            ProductUpdatePayload(
                name="Sản phẩm smoke test đã sửa",
                category="Kiểm thử",
                price=12_000,
                reorder_level=3,
            ),
            actor,
        )
        adjustment = adjust_inventory(
            connection,
            InventoryAdjustment(
                product_id=product_id,
                quantity_change=5,
                reason="Kiểm tra transaction tái cấu trúc",
            ),
            actor,
        )
        purchase_request = create_purchase_request(
            connection,
            PurchaseRequestPayload(
                product_id=product_id,
                quantity=4,
                reason="Kiểm tra phiếu nhập sau tái cấu trúc",
            ),
            actor,
        )

        user_result = create_user(
            connection,
            NewUser(
                full_name="Tài khoản smoke test",
                username=f"smoke.{suffix}",
                password_hash="smoke-test-hash-not-committed",
                role_id="Sales",
            ),
            actor,
        )
        user_change = update_user(
            connection,
            user_result["user_id"],
            UserChange(role_id="Warehouse", account_status=None),
            actor,
        )

        if adjustment["stock"] != 5:
            raise AssertionError("Inventory adjustment returned the wrong stock.")
        if purchase_request["total_value"] != 48_000:
            raise AssertionError("Purchase request used the wrong current price.")
        if not user_change["session_revoked"]:
            raise AssertionError("Role change did not revoke active sessions.")
        print(
            "PASS: product, inventory, purchase request and account writes "
            "ran successfully; transaction will be rolled back."
        )
    finally:
        connection.rollback()
        connection.close()


if __name__ == "__main__":
    main()
