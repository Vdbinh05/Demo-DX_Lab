# SPDX-License-Identifier: MIT
"""SQL Server persistence for stock and purchase-request administration."""

from datetime import date

from app.database.records import one, rows


class InventoryRepository:
    """Keep inventory SQL in a single persistence adapter."""

    def __init__(self, cursor):
        self.cursor = cursor

    def overview(self) -> dict:
        self.cursor.execute(
            """
            SELECT COUNT(*) AS total_products,
                   COALESCE(SUM(CASE WHEN Stock > ReorderLevel
                                     THEN 1 ELSE 0 END), 0) AS healthy_count,
                   COALESCE(SUM(CASE WHEN Stock > 0 AND Stock <= ReorderLevel
                                     THEN 1 ELSE 0 END), 0) AS low_count,
                   COALESCE(SUM(CASE WHEN Stock = 0
                                     THEN 1 ELSE 0 END), 0) AS out_count
            FROM dbo.Products
            """
        )
        summary = one(self.cursor)
        self.cursor.execute(
            """
            SELECT ProductID AS product_id, ProductName AS name,
                   Category AS category, Stock AS stock,
                   ReorderLevel AS reorder_level, Price AS price
            FROM dbo.Products
            WHERE Stock <= ReorderLevel
            ORDER BY CASE WHEN Stock = 0 THEN 0 ELSE 1 END, Stock
            """
        )
        return {"summary": summary, "alerts": rows(self.cursor)}

    def get_product_for_update(self, product_id: str):
        return self.cursor.execute(
            """
            SELECT ProductName, Stock
            FROM dbo.Products WITH (UPDLOCK, ROWLOCK)
            WHERE ProductID = ?
            """,
            product_id,
        ).fetchone()

    def set_stock(self, product_id: str, stock: int) -> None:
        self.cursor.execute(
            "UPDATE dbo.Products SET Stock = ? WHERE ProductID = ?",
            stock,
            product_id,
        )

    def insert_adjustment_movement(
        self,
        *,
        movement_id: str,
        product_id: str,
        quantity_change: int,
        reason: str,
        user_id: int,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.StockMovements
                (MovementID, ProductID, MovementType, Quantity, ReferenceID,
                 MovementDate, Reason, PerformedBy, CreatedAt)
            VALUES (?, ?, ?, ?, ?, CONVERT(date, GETDATE()), ?, ?, SYSDATETIME())
            """,
            movement_id,
            product_id,
            "IN" if quantity_change > 0 else "OUT",
            abs(quantity_change),
            "ADJUSTMENT",
            reason,
            user_id,
        )

    def insert_adjustment_activity(
        self,
        *,
        product_id: str,
        reason: str,
        user: dict,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Inventory')
            """,
            f"{user['FullName']} điều chỉnh {product_id}: {reason}",
        )

    def movement_history(
        self,
        *,
        product_id: str | None,
        movement_type: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> dict:
        filters = ["1 = 1"]
        parameters: list[object] = []
        if product_id:
            filters.append("movements.ProductID = ?")
            parameters.append(product_id.strip())
        if movement_type:
            filters.append("movements.MovementType = ?")
            parameters.append(movement_type)
        if start_date:
            filters.append("movements.MovementDate >= ?")
            parameters.append(start_date)
        if end_date:
            filters.append("movements.MovementDate <= ?")
            parameters.append(end_date)

        where_sql = " AND ".join(filters)
        total = int(
            self.cursor.execute(
                f"SELECT COUNT(*) FROM dbo.StockMovements movements WHERE {where_sql}",
                *parameters,
            ).fetchone()[0]
        )
        self.cursor.execute(
            f"""
            SELECT movements.MovementID AS movement_id,
                   movements.ProductID AS product_id,
                   products.ProductName AS product_name,
                   movements.MovementType AS movement_type,
                   movements.Quantity AS quantity,
                   movements.ReferenceID AS reference_id,
                   movements.MovementDate AS movement_date,
                   movements.Reason AS reason,
                   movements.CreatedAt AS created_at,
                   movements.PerformedBy AS performed_by,
                   users.FullName AS performed_by_name
            FROM dbo.StockMovements movements
            JOIN dbo.Products products ON products.ProductID = movements.ProductID
            LEFT JOIN dbo.Users users ON users.UserID = movements.PerformedBy
            WHERE {where_sql}
            ORDER BY movements.MovementDate DESC, movements.MovementID DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *parameters,
            (page - 1) * page_size,
            page_size,
        )
        return {
            "items": rows(self.cursor),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def list_purchase_requests(self, request_status: str | None) -> list[dict]:
        self.cursor.execute(
            """
            SELECT requests.RequestID AS request_id,
                   requests.ProductID AS product_id,
                   products.ProductName AS product_name,
                   requests.Quantity AS quantity,
                   requests.Reason AS reason,
                   requests.Requester AS requester,
                   requests.TotalValue AS total_value,
                   requests.Status AS request_status,
                   requests.CreatedAt AS created_at
            FROM dbo.PurchaseRequests requests
            JOIN dbo.Products products ON products.ProductID = requests.ProductID
            WHERE (? IS NULL OR LOWER(requests.Status) = LOWER(?))
            ORDER BY requests.CreatedAt DESC
            """,
            request_status,
            request_status,
        )
        return rows(self.cursor)

    def get_product_for_request(self, product_id: str):
        return self.cursor.execute(
            """
            SELECT ProductName, Price
            FROM dbo.Products
            WHERE ProductID = ?
            """,
            product_id,
        ).fetchone()

    def insert_purchase_request(
        self,
        *,
        request_id: str,
        product_id: str,
        quantity: int,
        reason: str,
        requester: str,
        total_value: int,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.PurchaseRequests
                (RequestID, ProductID, Quantity, Reason, Requester,
                 TotalValue, Status, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?, N'Pending approval', GETDATE())
            """,
            request_id,
            product_id,
            quantity,
            reason,
            requester,
            total_value,
        )

    def insert_purchase_request_activity(
        self,
        *,
        request_id: str,
        product_name: str,
        quantity: int,
        user: dict,
        new_values: str,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Inventory', ?,
                    'CREATE_REQUEST', 'PurchaseRequest', ?, ?)
            """,
            f"{user['FullName']} đề nghị nhập {quantity} {product_name}",
            int(user["UserID"]),
            request_id,
            new_values,
        )
