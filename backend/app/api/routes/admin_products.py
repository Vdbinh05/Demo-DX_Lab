# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.admin_common import (
    admin_user,
    db_error as _db_error,
)
from app.database.connection import get_connection
from app.schemas.admin import ProductCreatePayload, ProductUpdatePayload
from app.services.products import (
    ProductRuleError,
    create_product as create_product_service,
    delete_product as delete_product_service,
    list_products as list_products_service,
    update_product as update_product_service,
)


router = APIRouter()


@router.get("/products")
def list_products(q: str = Query(default="", max_length=100), _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        return list_products_service(connection, q)
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list products")
    finally:
        if connection is not None:
            connection.close()


@router.post("/products", status_code=201)
def create_product(payload: ProductCreatePayload, user: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        result = create_product_service(connection, payload, user)
        connection.commit()
        return result
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Mã sản phẩm đã tồn tại.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create product")
    finally:
        if connection is not None: connection.close()


@router.put("/products/{product_id}")
def update_product(
    product_id: str,
    payload: ProductUpdatePayload,
    user: dict = Depends(admin_user),
):
    connection = None
    try:
        connection = get_connection()
        result = update_product_service(connection, product_id, payload, user)
        connection.commit()
        return result
    except ProductRuleError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update product")
    finally:
        if connection is not None: connection.close()


@router.delete("/products/{product_id}")
def delete_product(product_id: str, _: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        result = delete_product_service(connection, product_id)
        connection.commit()
        return result
    except ProductRuleError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Sản phẩm đã phát sinh giao dịch nên không thể xóa lịch sử.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not delete product")
    finally:
        if connection is not None: connection.close()
