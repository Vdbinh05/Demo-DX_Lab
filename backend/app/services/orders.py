# SPDX-License-Identifier: MIT
"""Sales-order business rules shared by preview and checkout endpoints."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from http import HTTPStatus

from app.repositories.orders import OrderRepository
from app.schemas.orders import CreateOrderPayload, OrderQuotePayload


@dataclass(slots=True)
class OrderRuleError(Exception):
    """A safe business error that an HTTP adapter can expose to clients."""

    status_code: int
    detail: str


def _order_id() -> str:
    return f"SO-{datetime.now():%y%m%d-%H%M%S}-{uuid.uuid4().hex[:5].upper()}"


def _movement_id() -> str:
    return f"SM-{datetime.now():%y%m%d}-{uuid.uuid4().hex[:8].upper()}"


def _quantities(payload: OrderQuotePayload) -> dict[str, int]:
    quantities: dict[str, int] = {}
    for item in payload.items:
        product_id = item.product_id.strip()
        quantities[product_id] = quantities.get(product_id, 0) + item.quantity
    return quantities


def _request_fingerprint(payload: CreateOrderPayload) -> str:
    canonical = {
        "customer_id": payload.customer_id.strip(),
        "payment_method": payload.payment_method,
        "promotion_id": (payload.promotion_id or "").strip() or None,
        "items": sorted(_quantities(payload).items()),
    }
    serialized = json.dumps(canonical, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_quote(
    repository: OrderRepository,
    payload: OrderQuotePayload,
    *,
    lock: bool,
) -> dict:
    """Recalculate customer, stock, current prices and promotion on the server."""
    customer_id = payload.customer_id.strip()
    customer = repository.get_customer(customer_id, lock=lock)
    if customer is None:
        raise OrderRuleError(
            HTTPStatus.BAD_REQUEST,
            "Khách hàng không tồn tại hoặc đã ngừng hoạt động.",
        )

    order_lines = []
    subtotal = Decimal(0)
    for product_id, quantity in sorted(_quantities(payload).items()):
        product = repository.get_product(product_id, lock=lock)
        if product is None:
            raise OrderRuleError(
                HTTPStatus.BAD_REQUEST,
                f"Sản phẩm {product_id} không tồn tại.",
            )
        if int(product.Stock) < quantity:
            raise OrderRuleError(
                HTTPStatus.CONFLICT,
                f"{product.ProductName} chỉ còn {product.Stock} sản phẩm; không đủ để bán {quantity}.",
            )

        unit_price = Decimal(product.Price)
        line_subtotal = unit_price * quantity
        subtotal += line_subtotal
        order_lines.append(
            {
                "product_id": product.ProductID,
                "name": product.ProductName,
                "category": product.Category,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": line_subtotal,
            }
        )

    discount = Decimal(0)
    promotion_id = (payload.promotion_id or "").strip() or None
    promotion_title = None
    if promotion_id:
        promotion = repository.get_active_promotion(promotion_id, lock=lock)
        invalid_promotion = (
            promotion is None
            or (
                promotion.CustomerTier
                and str(promotion.CustomerTier).strip().lower()
                != str(customer.Tier or "Standard").strip().lower()
            )
            or subtotal < Decimal(promotion.MinOrderValue or 0)
            or (
                promotion.MaxUses is not None
                and int(promotion.UsedCount) >= int(promotion.MaxUses)
            )
        )
        if invalid_promotion:
            raise OrderRuleError(
                HTTPStatus.BAD_REQUEST,
                "Khuyến mãi không hợp lệ hoặc chưa đủ điều kiện áp dụng.",
            )

        eligible_total = subtotal
        if promotion.AppliedProductID:
            eligible_total = sum(
                line["subtotal"]
                for line in order_lines
                if line["product_id"] == promotion.AppliedProductID
            )
        elif promotion.AppliedCategory:
            eligible_total = sum(
                line["subtotal"]
                for line in order_lines
                if str(line["category"]).strip().lower()
                == str(promotion.AppliedCategory).strip().lower()
            )
        if eligible_total <= 0:
            raise OrderRuleError(
                HTTPStatus.BAD_REQUEST,
                "Đơn hàng không có sản phẩm thuộc phạm vi khuyến mãi.",
            )

        discount_value = Decimal(promotion.DiscountValue)
        if promotion.DiscountType == "PERCENT":
            discount = (eligible_total * discount_value / Decimal(100)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        else:
            discount = min(eligible_total, discount_value)
        discount = min(subtotal, max(Decimal(0), discount))
        promotion_title = promotion.Title

    total = subtotal - discount
    return {
        "customer_id": customer.CustomerID,
        "customer_name": customer.CustomerName,
        "subtotal_value": subtotal,
        "discount_value": discount,
        "total_value": total,
        "promotion_id": promotion_id,
        "promotion_title": promotion_title,
        "items": order_lines,
    }


def preview_order(connection, payload: OrderQuotePayload) -> dict:
    quote = build_quote(OrderRepository(connection.cursor()), payload, lock=False)
    return {
        **quote,
        "subtotal_value": int(quote["subtotal_value"]),
        "discount_value": int(quote["discount_value"]),
        "total_value": int(quote["total_value"]),
        "items": [
            {
                **line,
                "unit_price": int(line["unit_price"]),
                "subtotal": int(line["subtotal"]),
            }
            for line in quote["items"]
        ],
    }


def ensure_confirmed_total(expected_total_value: int, actual_total_value: Decimal) -> None:
    """Reject checkout when the authoritative price changed after preview."""
    if Decimal(expected_total_value) != actual_total_value:
        raise OrderRuleError(
            HTTPStatus.CONFLICT,
            "Giá hoặc khuyến mãi vừa thay đổi. Vui lòng kiểm tra tổng tiền mới rồi thanh toán lại.",
        )


def create_order(connection, payload: CreateOrderPayload, user: dict) -> dict:
    repository = OrderRepository(connection.cursor())
    fingerprint = _request_fingerprint(payload)
    existing = repository.find_by_idempotency_key(payload.idempotency_key)
    if existing is not None:
        if int(existing.CreatedBy) != int(user["UserID"]):
            raise OrderRuleError(
                HTTPStatus.CONFLICT,
                "Mã chống trùng đã được sử dụng bởi một giao dịch khác.",
            )
        if existing.RequestFingerprint and existing.RequestFingerprint != fingerprint:
            raise OrderRuleError(
                HTTPStatus.CONFLICT,
                "Nội dung giao dịch không khớp với lần thanh toán trước.",
            )
        return repository.order_response(existing.OrderID, duplicate=True)

    quote = build_quote(repository, payload, lock=True)
    ensure_confirmed_total(payload.expected_total_value, quote["total_value"])
    order_id = _order_id()
    repository.insert_order(
        order_id=order_id,
        customer_id=quote["customer_id"],
        user_id=int(user["UserID"]),
        total=quote["total_value"],
        payment_method=payload.payment_method,
        idempotency_key=payload.idempotency_key,
        request_fingerprint=fingerprint,
        subtotal=quote["subtotal_value"],
        discount=quote["discount_value"],
        promotion_id=quote["promotion_id"],
    )
    if quote["promotion_id"]:
        repository.increment_promotion_usage(quote["promotion_id"])

    for line in quote["items"]:
        repository.insert_order_item(order_id, line)
        if not repository.decrement_stock(line):
            raise OrderRuleError(
                HTTPStatus.CONFLICT,
                f"Tồn kho {line['name']} vừa thay đổi. Vui lòng thử lại.",
            )
        repository.insert_stock_movement(
            movement_id=_movement_id(),
            order_id=order_id,
            line=line,
            user_id=int(user["UserID"]),
        )

    repository.insert_order_activity(
        order_id=order_id,
        user=user,
        subtotal=quote["subtotal_value"],
        discount=quote["discount_value"],
        total=quote["total_value"],
        promotion_id=quote["promotion_id"],
    )
    return repository.order_response(order_id)


def order_detail(connection, order_id: str, user_id: int) -> dict:
    repository = OrderRepository(connection.cursor())
    if not repository.is_owned_order(order_id, user_id):
        raise OrderRuleError(HTTPStatus.NOT_FOUND, "Không tìm thấy đơn hàng.")
    return repository.order_response(order_id)


def list_my_orders(connection, user_id: int) -> dict:
    repository = OrderRepository(connection.cursor())
    summary = repository.my_orders_summary(user_id)
    rows = repository.my_orders(user_id)
    return {
        "summary": {
            "total_orders": int(summary.total_orders),
            "total_revenue": int(summary.total_revenue),
            "today_orders": int(summary.today_orders),
            "today_revenue": int(summary.today_revenue),
        },
        "items": [
            {
                "order_id": row.order_id,
                "customer": row.customer,
                "total_value": int(row.total_value),
                "payment_method": row.payment_method or "Cash",
                "payment_status": row.payment_status,
                "order_status": row.order_status,
                "paid_at": row.paid_at.isoformat() if row.paid_at else None,
            }
            for row in rows
        ],
    }
