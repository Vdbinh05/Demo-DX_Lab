# SPDX-License-Identifier: MIT
"""Business operations for stock and purchase-request administration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from http import HTTPStatus

from app.core.identifiers import business_id
from app.repositories.inventory import InventoryRepository
from app.schemas.admin import InventoryAdjustment, PurchaseRequestPayload


@dataclass(slots=True)
class InventoryRuleError(Exception):
    status_code: int
    detail: str


def inventory_overview(connection) -> dict:
    return InventoryRepository(connection.cursor()).overview()


def adjust_inventory(
    connection,
    payload: InventoryAdjustment,
    user: dict,
) -> dict:
    if payload.quantity_change == 0:
        raise InventoryRuleError(
            HTTPStatus.BAD_REQUEST,
            "Số lượng điều chỉnh phải khác 0.",
        )

    repository = InventoryRepository(connection.cursor())
    product = repository.get_product_for_update(payload.product_id)
    if product is None:
        raise InventoryRuleError(HTTPStatus.NOT_FOUND, "Không tìm thấy sản phẩm.")

    new_stock = int(product.Stock) + payload.quantity_change
    if new_stock < 0:
        raise InventoryRuleError(
            HTTPStatus.BAD_REQUEST,
            "Tồn kho không thể nhỏ hơn 0.",
        )

    repository.set_stock(payload.product_id, new_stock)
    repository.insert_adjustment_movement(
        movement_id=business_id("SM"),
        product_id=payload.product_id,
        quantity_change=payload.quantity_change,
        reason=payload.reason,
        user_id=int(user["UserID"]),
    )
    repository.insert_adjustment_activity(
        product_id=payload.product_id,
        reason=payload.reason,
        user=user,
    )
    return {"success": True, "stock": new_stock}


def inventory_movements(
    connection,
    *,
    product_id: str | None,
    movement_type: str | None,
    start_date: date | None,
    end_date: date | None,
    page: int,
    page_size: int,
) -> dict:
    if start_date and end_date and start_date > end_date:
        raise InventoryRuleError(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Ngày bắt đầu không được sau ngày kết thúc.",
        )
    return InventoryRepository(connection.cursor()).movement_history(
        product_id=product_id,
        movement_type=movement_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


def list_purchase_requests(connection, request_status: str | None) -> dict:
    repository = InventoryRepository(connection.cursor())
    return {"items": repository.list_purchase_requests(request_status)}


def create_purchase_request(
    connection,
    payload: PurchaseRequestPayload,
    user: dict,
) -> dict:
    repository = InventoryRepository(connection.cursor())
    product = repository.get_product_for_request(payload.product_id)
    if product is None:
        raise InventoryRuleError(HTTPStatus.NOT_FOUND, "Không tìm thấy sản phẩm.")

    request_id = business_id("PR")
    total_value = int(product.Price) * payload.quantity
    repository.insert_purchase_request(
        request_id=request_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        reason=payload.reason,
        requester=user["FullName"],
        total_value=total_value,
    )
    repository.insert_purchase_request_activity(
        request_id=request_id,
        product_name=product.ProductName,
        quantity=payload.quantity,
        user=user,
        new_values=payload.model_dump_json(),
    )
    return {
        "success": True,
        "request_id": request_id,
        "total_value": total_value,
    }
