"""Shared product catalogue APIs for authenticated workspaces."""

import logging
from decimal import Decimal

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query, status

from core import current_user, get_connection


router = APIRouter(prefix="/catalog", tags=["catalog"])
logger = logging.getLogger(__name__)


def _json_number(value):
    return int(value) if isinstance(value, Decimal) else value


@router.get("/products")
def list_products(
    q: str = Query(default="", max_length=100),
    _: dict = Depends(current_user),
):
    """Return the live SQL Server catalogue to both Admin and Sales users."""
    connection = None
    query = q.strip()
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT ProductID AS product_id,
                   ProductName AS name,
                   Category AS category,
                   Price AS price,
                   Stock AS stock,
                   ReorderLevel AS reorder_level
            FROM dbo.Products
            WHERE (? = '' OR ProductID LIKE '%' + ? + '%'
                OR ProductName LIKE N'%' + ? + N'%'
                OR Category LIKE N'%' + ? + N'%')
            ORDER BY ProductName
            """,
            query, query, query, query,
        )
        columns = [column[0] for column in cursor.description]
        items = [
            {
                columns[index]: _json_number(value)
                for index, value in enumerate(row)
            }
            for row in cursor.fetchall()
        ]
        return {"items": items, "total": len(items)}
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not load shared product catalogue")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải danh mục sản phẩm từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@router.get("/customers")
def list_customers(
    q: str = Query(default="", max_length=100),
    _: dict = Depends(current_user),
):
    """Return active customers for POS selection and Sales lookup."""
    connection = None
    query = q.strip()
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT CustomerID AS customer_id,
                   CustomerName AS name,
                   ContactName AS contact_name,
                   Phone AS phone,
                   Tier AS tier,
                   Status AS customer_status
            FROM dbo.Customers
            WHERE LOWER(COALESCE(Status, N'Active')) = N'active'
              AND (? = '' OR CustomerID LIKE '%' + ? + '%'
                OR CustomerName LIKE N'%' + ? + N'%'
                OR ContactName LIKE N'%' + ? + N'%'
                OR Phone LIKE '%' + ? + '%')
            ORDER BY CustomerName
            """,
            query, query, query, query, query,
        )
        columns = [column[0] for column in cursor.description]
        items = [
            {columns[index]: value for index, value in enumerate(row)}
            for row in cursor.fetchall()
        ]
        return {"items": items, "total": len(items)}
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not load shared customer catalogue")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải danh sách khách hàng từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@router.get("/promotions")
def list_promotions(_: dict = Depends(current_user)):
    """Return currently active promotions from SQL Server."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT PromotionID AS promotion_id,
                   Title AS title,
                   Description AS description,
                   Tag AS tag,
                   CustomerTier AS customer_tier,
                   StartDate AS start_date,
                   EndDate AS end_date,
                   Color AS color
            FROM dbo.Promotions
            WHERE LOWER(Status) = N'active'
              AND StartDate <= CONVERT(date, GETDATE())
              AND EndDate >= CONVERT(date, GETDATE())
            ORDER BY EndDate, Title
            """
        )
        items = [
            {
                "promotion_id": row.promotion_id,
                "title": row.title,
                "description": row.description,
                "tag": row.tag,
                "customer_tier": row.customer_tier,
                "start_date": row.start_date.isoformat(),
                "end_date": row.end_date.isoformat(),
                "color": row.color,
            }
            for row in cursor.fetchall()
        ]
        return {"items": items, "total": len(items)}
    except (pyodbc.Error, RuntimeError) as exc:
        logger.exception("Could not load promotions")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải chương trình khuyến mãi từ SQL Server.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()
