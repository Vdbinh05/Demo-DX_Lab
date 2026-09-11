# SPDX-License-Identifier: MIT
"""SQL Server persistence for the product administration domain."""


from app.database.records import rows


class ProductRepository:
    """Keep product SQL out of services and FastAPI route handlers."""

    def __init__(self, cursor):
        self.cursor = cursor

    def list(self, query: str) -> list[dict]:
        self.cursor.execute(
            """
            SELECT products.ProductID AS product_id,
                   products.ProductName AS name,
                   products.Category AS category,
                   products.Price AS price,
                   products.Stock AS stock,
                   products.ReorderLevel AS reorder_level,
                   COALESCE(SUM(CASE
                       WHEN orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
                       THEN items.Quantity ELSE 0 END), 0) AS sold_quantity
            FROM dbo.Products products
            LEFT JOIN dbo.SalesOrderItems items
                ON items.ProductID = products.ProductID
            LEFT JOIN dbo.SalesOrders orders ON orders.OrderID = items.OrderID
            WHERE (? = '' OR products.ProductID LIKE '%' + ? + '%'
                OR products.ProductName LIKE N'%' + ? + N'%'
                OR products.Category LIKE N'%' + ? + N'%')
            GROUP BY products.ProductID, products.ProductName, products.Category,
                     products.Price, products.Stock, products.ReorderLevel
            ORDER BY products.ProductName
            """,
            query,
            query,
            query,
            query,
        )
        return rows(self.cursor)

    def insert(
        self,
        *,
        product_id: str,
        name: str,
        category: str,
        price: int,
        stock: int,
        reorder_level: int,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Products
                (ProductID, ProductName, Category, Price, Stock, ReorderLevel)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            product_id,
            name,
            category,
            price,
            stock,
            reorder_level,
        )

    def insert_initial_stock(
        self,
        *,
        movement_id: str,
        product_id: str,
        quantity: int,
        user_id: int,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.StockMovements
                (MovementID, ProductID, MovementType, Quantity, ReferenceID,
                 MovementDate, Reason, PerformedBy, CreatedAt)
            VALUES (?, ?, 'IN', ?, 'INITIAL_STOCK', CONVERT(date, GETDATE()),
                    N'Tồn kho ban đầu khi tạo sản phẩm', ?, SYSDATETIME())
            """,
            movement_id,
            product_id,
            quantity,
            user_id,
        )

    def insert_create_activity(
        self,
        *,
        product_id: str,
        user: dict,
        new_values: str,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Product', ?,
                    'CREATE_PRODUCT', 'Product', ?, ?)
            """,
            f"{user['FullName']} đã thêm sản phẩm {product_id}",
            int(user["UserID"]),
            product_id,
            new_values,
        )

    def get_for_update(self, product_id: str):
        return self.cursor.execute(
            """
            SELECT ProductName, Category, Price, ReorderLevel
            FROM dbo.Products WITH (UPDLOCK, ROWLOCK)
            WHERE ProductID = ?
            """,
            product_id,
        ).fetchone()

    def update(
        self,
        *,
        product_id: str,
        name: str,
        category: str,
        price: int,
        reorder_level: int,
    ) -> None:
        self.cursor.execute(
            """
            UPDATE dbo.Products
            SET ProductName = ?, Category = ?, Price = ?, ReorderLevel = ?
            WHERE ProductID = ?
            """,
            name,
            category,
            price,
            reorder_level,
            product_id,
        )

    def insert_update_activity(
        self,
        *,
        product_id: str,
        user: dict,
        old_values: str,
        new_values: str,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, OldValues, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Product', ?,
                    'UPDATE_PRODUCT', 'Product', ?, ?, ?)
            """,
            f"{user['FullName']} đã cập nhật sản phẩm {product_id}",
            int(user["UserID"]),
            product_id,
            old_values,
            new_values,
        )

    def delete(self, product_id: str) -> bool:
        self.cursor.execute(
            "DELETE FROM dbo.Products WHERE ProductID = ?",
            product_id,
        )
        return self.cursor.rowcount == 1
