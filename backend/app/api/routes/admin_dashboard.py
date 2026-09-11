# SPDX-License-Identifier: MIT
"""Administrator endpoints split by business capability."""

import pyodbc
from fastapi import APIRouter, Depends

from app.api.admin_common import (
    admin_user,
    db_error as _db_error,
)
from app.database.connection import get_connection
from app.services.reporting import dashboard as dashboard_service
from app.services.reporting import revenue as revenue_service


router = APIRouter()


@router.get("/dashboard")
def dashboard(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        return dashboard_service(connection)
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not build admin dashboard")
    finally:
        if connection is not None:
            connection.close()


@router.get("/revenue")
def revenue(_: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        return revenue_service(connection)
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not load revenue report")
    finally:
        if connection is not None:
            connection.close()
