# SPDX-License-Identifier: MIT
"""Aggregate domain routers in one discoverable location.

Adapted from the router composition used by the MIT-licensed Full Stack
FastAPI Template, commit cb740b656d7a0a6c5e12c7bf8e50343ec94ee9c7.
"""

from fastapi import APIRouter

from app.api.routes import admin, auth, catalog, orders, system


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(orders.router)
api_router.include_router(admin.router)
