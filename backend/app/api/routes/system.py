# SPDX-License-Identifier: MIT
"""Operational endpoints that do not belong to a business domain."""

import pyodbc
from fastapi import APIRouter, HTTPException, status

from app.database.connection import check_database, database_error_message


router = APIRouter(tags=["system"])


@router.get("/health")
def health_check():
    try:
        return check_database()
    except (pyodbc.Error, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=database_error_message(exc) if isinstance(exc, pyodbc.Error) else str(exc),
        ) from exc
