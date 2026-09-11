# SPDX-License-Identifier: MIT
"""Validated payloads for transactional sales orders."""

from typing import Literal

from pydantic import BaseModel, Field


class OrderItemPayload(BaseModel):
    product_id: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=1, le=999)


class OrderQuotePayload(BaseModel):
    customer_id: str = Field(min_length=1, max_length=20)
    items: list[OrderItemPayload] = Field(min_length=1, max_length=100)
    promotion_id: str | None = Field(default=None, max_length=20)


class CreateOrderPayload(OrderQuotePayload):
    payment_method: Literal["Cash", "BankTransfer"] = "Cash"
    idempotency_key: str = Field(min_length=8, max_length=64)
    expected_total_value: int = Field(ge=0)
