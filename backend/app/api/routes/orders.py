# SPDX-License-Identifier: MIT
"""HTTP adapters for employee sales-order operations."""

import logging

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import require_roles
from app.database.connection import get_connection
from app.schemas.orders import CreateOrderPayload, OrderQuotePayload
from app.services.orders import (
    OrderRuleError,
    create_order as create_order_service,
    list_my_orders as list_my_orders_service,
    order_detail as order_detail_service,
    preview_order as preview_order_service,
)


router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)
sales_user = require_roles("Sales")


def _business_error(exc: OrderRuleError) -> HTTPException:
    return HTTPException(status_code=int(exc.status_code), detail=exc.detail)


@router.post("/preview")
def preview_order(payload: OrderQuotePayload, _: dict = Depends(sales_user)):
    """Return the authoritative price without creating an order."""
    connection = None
    try:
        connection = get_connection()
        return preview_order_service(connection, payload)
    except OrderRuleError as exc:
        raise _business_error(exc) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not preview sales order")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tính trước đơn hàng từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: CreateOrderPayload, user: dict = Depends(sales_user)):
    """Create a paid POS order and reduce stock in one SQL transaction."""
    connection = None
    try:
        connection = get_connection()
        result = create_order_service(connection, payload, user)
        connection.commit()
        return result
    except OrderRuleError as exc:
        if connection is not None:
            connection.rollback()
        raise _business_error(exc) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None:
            connection.rollback()
        logger.exception("Could not create sales order")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tạo đơn hàng trong SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@router.get("/my-orders/{order_id}")
def my_order_detail(order_id: str, user: dict = Depends(sales_user)):
    """Return an order only when it belongs to the signed-in employee."""
    connection = None
    try:
        connection = get_connection()
        return order_detail_service(connection, order_id, int(user["UserID"]))
    except OrderRuleError as exc:
        raise _business_error(exc) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not load employee order detail")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải chi tiết đơn hàng từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@router.get("/my-orders")
def my_orders(user: dict = Depends(sales_user)):
    connection = None
    try:
        connection = get_connection()
        return list_my_orders_service(connection, int(user["UserID"]))
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not list employee orders")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải đơn hàng của nhân viên từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()
