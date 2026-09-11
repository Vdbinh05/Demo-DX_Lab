# SPDX-License-Identifier: MIT
"""Business operations for administrator product management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus

from app.core.identifiers import business_id
from app.repositories.products import ProductRepository
from app.schemas.admin import ProductCreatePayload, ProductUpdatePayload


@dataclass(slots=True)
class ProductRuleError(Exception):
    status_code: int
    detail: str


def _clean(value: str | None) -> str:
    return (value or "").strip()


def list_products(connection, query: str) -> dict:
    repository = ProductRepository(connection.cursor())
    return {"items": repository.list(_clean(query))}


def create_product(
    connection,
    payload: ProductCreatePayload,
    user: dict,
) -> dict:
    repository = ProductRepository(connection.cursor())
    product_id = _clean(payload.product_id) or business_id("SP")
    product = {
        "product_id": product_id,
        "name": _clean(payload.name),
        "category": _clean(payload.category),
        "price": payload.price,
        "stock": payload.stock,
        "reorder_level": payload.reorder_level,
    }
    repository.insert(**product)
    if payload.stock > 0:
        repository.insert_initial_stock(
            movement_id=business_id("SM"),
            product_id=product_id,
            quantity=payload.stock,
            user_id=int(user["UserID"]),
        )
    repository.insert_create_activity(
        product_id=product_id,
        user=user,
        new_values=json.dumps(product, ensure_ascii=False),
    )
    return {"success": True, "product_id": product_id}


def update_product(
    connection,
    product_id: str,
    payload: ProductUpdatePayload,
    user: dict,
) -> dict:
    repository = ProductRepository(connection.cursor())
    current = repository.get_for_update(product_id)
    if current is None:
        raise ProductRuleError(HTTPStatus.NOT_FOUND, "Không tìm thấy sản phẩm.")

    updated = {
        "name": _clean(payload.name),
        "category": _clean(payload.category),
        "price": payload.price,
        "reorder_level": payload.reorder_level,
    }
    repository.update(product_id=product_id, **updated)
    repository.insert_update_activity(
        product_id=product_id,
        user=user,
        old_values=json.dumps(
            {
                "name": current.ProductName,
                "category": current.Category,
                "price": int(current.Price),
                "reorder_level": int(current.ReorderLevel),
            },
            ensure_ascii=False,
        ),
        new_values=json.dumps(updated, ensure_ascii=False),
    )
    return {"success": True}


def delete_product(connection, product_id: str) -> dict:
    repository = ProductRepository(connection.cursor())
    if not repository.delete(product_id):
        raise ProductRuleError(HTTPStatus.NOT_FOUND, "Không tìm thấy sản phẩm.")
    return {"success": True}
