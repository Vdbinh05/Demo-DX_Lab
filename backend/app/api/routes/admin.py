# SPDX-License-Identifier: MIT
"""Aggregate administrator routes while preserving the `/admin` API prefix."""

from fastapi import APIRouter

from app.api.routes import (
    admin_customers,
    admin_dashboard,
    admin_inventory,
    admin_orders,
    admin_products,
    admin_promotions,
    admin_settings,
    admin_users,
)


router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(admin_dashboard.router)
router.include_router(admin_orders.router)
router.include_router(admin_products.router)
router.include_router(admin_promotions.router)
router.include_router(admin_customers.router)
router.include_router(admin_inventory.router)
router.include_router(admin_users.router)
router.include_router(admin_settings.router)
