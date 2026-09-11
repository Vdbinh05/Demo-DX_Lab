# SPDX-License-Identifier: MIT
"""Promotion management endpoints for administrators."""

import logging

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.admin_common import (
    admin_user,
    business_id as _business_id,
    clean as _clean,
    db_error as _db_error,
    rows as _rows,
)
from app.database.connection import get_connection
from app.schemas.admin import PromotionPayload


router = APIRouter()
logger = logging.getLogger(__name__)


def _validate_promotion(payload: PromotionPayload) -> None:
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="Ngày kết thúc không được trước ngày bắt đầu.")
    if payload.discount_type == "PERCENT" and payload.discount_value > 100:
        raise HTTPException(status_code=422, detail="Giảm theo phần trăm không được vượt quá 100%.")
    if payload.applied_product_id and payload.applied_category:
        raise HTTPException(
            status_code=422,
            detail="Chỉ chọn một sản phẩm hoặc một danh mục áp dụng.",
        )


def _write_values(payload: PromotionPayload) -> tuple:
    return (
        _clean(payload.title),
        _clean(payload.description),
        _clean(payload.tag),
        _clean(payload.customer_tier) or None,
        payload.discount_type,
        payload.discount_value,
        payload.min_order_value,
        payload.max_uses,
        _clean(payload.applied_product_id) or None,
        _clean(payload.applied_category) or None,
        payload.start_date,
        payload.end_date,
        payload.promotion_status,
        payload.color,
    )


@router.get("/promotions")
def list_promotions(
    q: str = Query(default="", max_length=100),
    include_inactive: bool = Query(default=True),
    _: dict = Depends(admin_user),
):
    query = _clean(q)
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT PromotionID AS promotion_id, Title AS title,
                   Description AS description, Tag AS tag,
                   CustomerTier AS customer_tier, DiscountType AS discount_type,
                   DiscountValue AS discount_value, MinOrderValue AS min_order_value,
                   MaxUses AS max_uses, UsedCount AS used_count,
                   AppliedProductID AS applied_product_id,
                   AppliedCategory AS applied_category, StartDate AS start_date,
                   EndDate AS end_date, Status AS promotion_status, Color AS color,
                   CreatedAt AS created_at, UpdatedAt AS updated_at
            FROM dbo.Promotions
            WHERE (? = 1 OR LOWER(Status) = N'active')
              AND (? = '' OR PromotionID LIKE '%' + ? + '%'
                   OR Title LIKE N'%' + ? + N'%'
                   OR Tag LIKE N'%' + ? + N'%')
            ORDER BY StartDate DESC, Title
            """,
            int(include_inactive), query, query, query, query,
        )
        return {"items": _rows(cursor)}
    except (pyodbc.Error, RuntimeError) as exc:
        _db_error(exc, "Could not list promotions")
    finally:
        if connection is not None: connection.close()


@router.post("/promotions", status_code=201)
def create_promotion(payload: PromotionPayload, user: dict = Depends(admin_user)):
    _validate_promotion(payload)
    promotion_id = _clean(payload.promotion_id) or _business_id("KM")
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.Promotions
                (PromotionID, Title, Description, Tag, CustomerTier,
                 DiscountType, DiscountValue, MinOrderValue, MaxUses,
                 AppliedProductID, AppliedCategory, StartDate, EndDate,
                 Status, Color, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    SYSDATETIME(), SYSDATETIME())
            """,
            promotion_id, *_write_values(payload),
        )
        cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Promotion', ?,
                    'CREATE', 'Promotion', ?, ?)
            """,
            f"{user['FullName']} đã tạo khuyến mãi {promotion_id}",
            user["UserID"], promotion_id, payload.model_dump_json(),
        )
        connection.commit()
        return {"success": True, "promotion_id": promotion_id}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Mã khuyến mãi hoặc sản phẩm áp dụng không hợp lệ.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not create promotion")
    finally:
        if connection is not None: connection.close()


@router.put("/promotions/{promotion_id}")
def update_promotion(
    promotion_id: str,
    payload: PromotionPayload,
    user: dict = Depends(admin_user),
):
    _validate_promotion(payload)
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE dbo.Promotions
            SET Title = ?, Description = ?, Tag = ?, CustomerTier = ?,
                DiscountType = ?, DiscountValue = ?, MinOrderValue = ?,
                MaxUses = ?, AppliedProductID = ?, AppliedCategory = ?,
                StartDate = ?, EndDate = ?, Status = ?, Color = ?,
                UpdatedAt = SYSDATETIME()
            WHERE PromotionID = ?
            """,
            *_write_values(payload), promotion_id,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy khuyến mãi.")
        cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Promotion', ?,
                    'UPDATE', 'Promotion', ?, ?)
            """,
            f"{user['FullName']} đã cập nhật khuyến mãi {promotion_id}",
            user["UserID"], promotion_id, payload.model_dump_json(),
        )
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except pyodbc.IntegrityError as exc:
        if connection is not None: connection.rollback()
        raise HTTPException(status_code=409, detail="Sản phẩm áp dụng không hợp lệ.") from exc
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not update promotion")
    finally:
        if connection is not None: connection.close()


@router.delete("/promotions/{promotion_id}")
def deactivate_promotion(promotion_id: str, user: dict = Depends(admin_user)):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE dbo.Promotions SET Status = N'Inactive', UpdatedAt = SYSDATETIME() WHERE PromotionID = ?",
            promotion_id,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy khuyến mãi.")
        cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Promotion', ?,
                    'DEACTIVATE', 'Promotion', ?)
            """,
            f"{user['FullName']} đã ngừng khuyến mãi {promotion_id}",
            user["UserID"], promotion_id,
        )
        connection.commit()
        return {"success": True}
    except HTTPException:
        if connection is not None: connection.rollback()
        raise
    except (pyodbc.Error, RuntimeError) as exc:
        if connection is not None: connection.rollback()
        _db_error(exc, "Could not deactivate promotion")
    finally:
        if connection is not None: connection.close()
