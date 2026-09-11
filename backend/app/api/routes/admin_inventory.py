# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

from datetime import date
from typing import Literal

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.admin_common import (
    admin_user,
    db_error as _db_error,
)
from app.database.connection import get_connection
from app.schemas.admin import InventoryAdjustment, PurchaseRequestPayload
from app.services.inventory import (
    InventoryRuleError,
    adjust_inventory as adjust_inventory_service,
    create_purchase_request as create_purchase_request_service,
    inventory_movements as inventory_movements_service,
    inventory_overview,
    list_purchase_requests as list_purchase_requests_service,
)


router = APIRouter()


@router.get("/inventory")
def inventory(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        return inventory_overview(connection)
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load inventory")
    finally:
        if connection is not None: connection.close()


@router.post("/inventory/adjustments")
def adjust_inventory(payload: InventoryAdjustment, user: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        result = adjust_inventory_service(connection, payload, user)
        connection.commit()
        return result
    except InventoryRuleError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not adjust inventory")
    finally:
        if connection is not None: connection.close()


@router.get("/inventory/movements")
def inventory_movements(
    product_id: str | None = Query(default=None, max_length=20),
    movement_type: Literal["IN", "OUT"] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    _: dict = Depends(admin_user),
):
    """Return paginated stock history using the currently available schema."""
    connection = None
    try:
        connection = get_connection()
        return inventory_movements_service(
            connection,
            product_id=product_id,
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
    except InventoryRuleError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load inventory movement history")
    finally:
        if connection is not None: connection.close()


@router.get("/inventory/purchase-requests")
def list_purchase_requests(
    request_status: str | None = Query(default=None, max_length=30),
    _: dict = Depends(admin_user),
):
    connection = None
    try:
        connection = get_connection()
        return list_purchase_requests_service(connection, request_status)
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list purchase requests")
    finally:
        if connection is not None: connection.close()


@router.post("/inventory/purchase-requests", status_code=201)
def create_purchase_request(
    payload: PurchaseRequestPayload,
    user: dict = Depends(admin_user),
):
    connection = None
    try:
        connection = get_connection()
        result = create_purchase_request_service(connection, payload, user)
        connection.commit()
        return result
    except InventoryRuleError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create purchase request")
    finally:
        if connection is not None: connection.close()
