# SPDX-License-Identifier: MIT
"""Validated payloads accepted by administrator endpoints."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductBasePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=50)
    price: int = Field(ge=0)
    reorder_level: int = Field(ge=0)


class ProductCreatePayload(ProductBasePayload):
    product_id: str | None = Field(default=None, max_length=20)
    stock: int = Field(ge=0)


class ProductUpdatePayload(ProductBasePayload):
    """Editable product metadata; inventory changes use the inventory API."""


class AdminOrderItemResponse(BaseModel):
    product_id: str
    name: str
    quantity: int
    unit_price: int
    subtotal: int


class AdminOrderDetailResponse(BaseModel):
    order_id: str
    customer_id: str
    customer: str
    contact_name: str | None = None
    phone: str | None = None
    seller: str
    subtotal_value: int
    discount_value: int
    total_value: int
    promotion_id: str | None = None
    promotion_title: str | None = None
    payment_method: str | None = None
    payment_status: str
    order_status: str
    created_at: datetime
    items: list[AdminOrderItemResponse]


class CustomerPayload(BaseModel):
    customer_id: str | None = Field(default=None, max_length=20)
    name: str = Field(min_length=2, max_length=255)
    contact_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    tier: str = Field(default="Standard", max_length=30)
    customer_status: str = Field(default="Active", max_length=20)


class InventoryAdjustment(BaseModel):
    product_id: str
    quantity_change: int
    reason: str = Field(min_length=3, max_length=255)


class PurchaseRequestPayload(BaseModel):
    product_id: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=1, le=100000)
    reason: str = Field(min_length=3, max_length=255)


class AdminAccountPayload(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role_id: Literal["Admin", "Sales", "Warehouse"] = "Sales"


class AccountPatch(BaseModel):
    role_id: Literal["Admin", "Sales", "Warehouse"] | None = None
    account_status: Literal["Active", "Locked"] | None = None

    @model_validator(mode="after")
    def require_at_least_one_change(self):
        if self.role_id is None and self.account_status is None:
            raise ValueError("Phải gửi vai trò hoặc trạng thái cần cập nhật.")
        return self


class SettingsPayload(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    company_phone: str = Field(default="", max_length=50)
    company_address: str = Field(default="", max_length=500)
    tax_code: str = Field(default="", max_length=50)


class PromotionPayload(BaseModel):
    promotion_id: str | None = Field(default=None, max_length=20)
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=2, max_length=1000)
    tag: str = Field(min_length=1, max_length=30)
    customer_tier: str | None = Field(default=None, max_length=30)
    discount_type: Literal["PERCENT", "FIXED"]
    discount_value: int = Field(ge=0)
    min_order_value: int = Field(default=0, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    applied_product_id: str | None = Field(default=None, max_length=20)
    applied_category: str | None = Field(default=None, max_length=50)
    start_date: date
    end_date: date
    promotion_status: Literal["Active", "Inactive"] = "Active"
    color: Literal["violet", "blue", "orange"] = "blue"
