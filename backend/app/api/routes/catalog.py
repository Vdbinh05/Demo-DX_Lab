# SPDX-License-Identifier: MIT
"""Shared product catalogue APIs for authenticated workspaces."""

import logging
from decimal import Decimal
from typing import Literal

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import require_roles
from app.database.connection import get_connection


router = APIRouter(prefix="/catalog", tags=["catalog"])
logger = logging.getLogger(__name__)
product_catalog_user = require_roles("Sales", "Warehouse")
sales_catalog_user = require_roles("Sales")


def _json_number(value):
    return int(value) if isinstance(value, Decimal) else value


@router.get("/products")
def list_products(
    q: str = Query(default="", max_length=100),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    category: str | None = Query(default=None, max_length=50),
    in_stock: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    sort_by: Literal["name", "price", "stock"] = "name",
    sort_order: Literal["asc", "desc"] = "asc",
    _: dict = Depends(product_catalog_user),
):
    """Return a filtered, sorted and paginated live product catalogue."""
    connection = None
    query = q.strip()
    selected_category = (category or "").strip()
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Giá thấp nhất không được lớn hơn giá cao nhất.",
        )

    filters = [
        "(? = '' OR ProductID LIKE '%' + ? + '%' "
        "OR ProductName LIKE N'%' + ? + N'%' "
        "OR Category LIKE N'%' + ? + N'%')"
    ]
    parameters: list[object] = [query, query, query, query]
    if min_price is not None:
        filters.append("Price >= ?")
        parameters.append(min_price)
    if max_price is not None:
        filters.append("Price <= ?")
        parameters.append(max_price)
    if selected_category:
        filters.append("LOWER(Category) = LOWER(?)")
        parameters.append(selected_category)
    if in_stock is True:
        filters.append("Stock > 0")
    elif in_stock is False:
        filters.append("Stock <= 0")

    order_columns = {"name": "ProductName", "price": "Price", "stock": "Stock"}
    order_column = order_columns[sort_by]
    order_direction = sort_order.upper()
    where_sql = " AND ".join(filters)
    offset = (page - 1) * page_size
    try:
        connection = get_connection()
        cursor = connection.cursor()
        total = int(
            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.Products WHERE {where_sql}",
                *parameters,
            ).fetchone()[0]
        )
        cursor.execute(
            f"""
            SELECT ProductID AS product_id,
                   ProductName AS name,
                   Category AS category,
                   Price AS price,
                   Stock AS stock,
                   ReorderLevel AS reorder_level
            FROM dbo.Products
            WHERE {where_sql}
            ORDER BY {order_column} {order_direction}, ProductID ASC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *parameters, offset, page_size,
        )
        columns = [column[0] for column in cursor.description]
        items = [
            {
                columns[index]: _json_number(value)
                for index, value in enumerate(row)
            }
            for row in cursor.fetchall()
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
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
    _: dict = Depends(sales_catalog_user),
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
def list_promotions(_: dict = Depends(sales_catalog_user)):
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
                   DiscountType AS discount_type,
                   DiscountValue AS discount_value,
                   MinOrderValue AS min_order_value,
                   MaxUses AS max_uses,
                   UsedCount AS used_count,
                   AppliedProductID AS applied_product_id,
                   AppliedCategory AS applied_category,
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
                "discount_type": row.discount_type,
                "discount_value": int(row.discount_value),
                "min_order_value": int(row.min_order_value),
                "max_uses": row.max_uses,
                "used_count": int(row.used_count),
                "applied_product_id": row.applied_product_id,
                "applied_category": row.applied_category,
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
