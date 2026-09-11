# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

import pyodbc
from fastapi import APIRouter, Depends, HTTPException

from app.api.admin_common import (
    admin_user,
    db_error as _db_error,
)
from app.database.connection import get_connection
from app.schemas.admin import AccountPatch, AdminAccountPayload
from app.services.users import (
    UserRuleError,
    create_user as create_user_service,
    list_users as list_users_service,
    prepare_new_user,
    prepare_user_change,
    update_user as update_user_service,
)


router = APIRouter()


@router.get("/users")
def list_users(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        return list_users_service(connection)
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list users")
    finally:
        if connection is not None: connection.close()


@router.post("/users", status_code=201)
def create_user(payload: AdminAccountPayload, user: dict = Depends(admin_user)):
    connection = None
    try:
        new_user = prepare_new_user(payload)
        connection = get_connection()
        result = create_user_service(connection, new_user, user)
        connection.commit()
        return result
    except UserRuleError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create user")
    finally:
        if connection is not None: connection.close()


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: AccountPatch, user: dict = Depends(admin_user)):
    connection = None
    try:
        change = prepare_user_change(user_id, payload, user)
        connection = get_connection()
        result = update_user_service(connection, user_id, change, user)
        connection.commit()
        return result
    except UserRuleError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update user")
    finally:
        if connection is not None: connection.close()
