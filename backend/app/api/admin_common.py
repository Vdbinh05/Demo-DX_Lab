# SPDX-License-Identifier: MIT
"""Shared HTTP dependencies and compatibility helpers for administrator routes."""

import logging

from fastapi import Depends, HTTPException, status

from app.api.dependencies import current_user, require_admin
from app.core.identifiers import business_id
from app.database.records import one, rows


logger = logging.getLogger(__name__)


def admin_user(user: dict = Depends(current_user)) -> dict:
    return require_admin(user)


def db_error(exc: Exception, message: str):
    logger.exception(message)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Không thể đọc hoặc cập nhật dữ liệu SQL Server.",
    ) from exc


def clean(value: str | None) -> str:
    return (value or "").strip()
