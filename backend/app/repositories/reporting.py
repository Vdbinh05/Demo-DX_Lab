# SPDX-License-Identifier: MIT
"""SQL Server queries for administrator dashboards and revenue reports."""

from app.database.records import one, rows


class ReportingRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def dashboard_metrics(self) -> dict:
        self.cursor.execute(
            """
            SELECT
                COALESCE(SUM(CASE
                    WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                     AND OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
                    THEN TotalValue ELSE 0 END), 0) AS month_revenue,
                SUM(CASE
                    WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                     AND OrderDate = CONVERT(date, GETDATE())
                    THEN 1 ELSE 0 END) AS today_orders,
                COALESCE(SUM(CASE
                    WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                     AND OrderDate = CONVERT(date, GETDATE())
                    THEN TotalValue ELSE 0 END), 0) AS today_revenue,
                SUM(CASE
                    WHEN Status IN (N'Completed', N'Paid', N'Hoàn thành')
                     AND OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
                    THEN 1 ELSE 0 END) AS month_orders
            FROM dbo.SalesOrders
            """
        )
        metrics = one(self.cursor)
        self.cursor.execute("SELECT COUNT(*) AS customer_count FROM dbo.Customers")
        metrics.update(one(self.cursor))
        self.cursor.execute("SELECT COUNT(*) AS account_count FROM dbo.Users")
        metrics.update(one(self.cursor))
        self.cursor.execute(
            """
            SELECT COUNT(*) AS low_stock_count
            FROM dbo.Products
            WHERE Stock <= ReorderLevel
            """
        )
        metrics.update(one(self.cursor))
        return metrics

    def monthly_revenue(self, *, include_order_count: bool = False) -> list[dict]:
        order_count_column = (
            ", COUNT(orders.OrderID) AS order_count"
            if include_order_count
            else ""
        )
        self.cursor.execute(
            f"""
            WITH month_series AS
            (
                SELECT 0 AS offset_number UNION ALL SELECT 1 UNION ALL SELECT 2
                UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ), months AS
            (
                SELECT DATEADD(month, -offset_number,
                    DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS month_start
                FROM month_series
            )
            SELECT YEAR(months.month_start) AS [year],
                   MONTH(months.month_start) AS [month],
                   COALESCE(SUM(orders.TotalValue), 0) AS revenue
                   {order_count_column}
            FROM months
            LEFT JOIN dbo.SalesOrders orders
              ON orders.OrderDate >= months.month_start
             AND orders.OrderDate < DATEADD(month, 1, months.month_start)
             AND orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
            GROUP BY months.month_start
            ORDER BY months.month_start
            """
        )
        return rows(self.cursor)

    def top_products(self) -> list[dict]:
        self.cursor.execute(
            """
            SELECT TOP 5 products.ProductID AS product_id,
                   products.ProductName AS name,
                   products.Category AS category,
                   SUM(items.Quantity) AS sold_quantity,
                   CAST(ROUND(COALESCE(SUM(
                       CASE
                           WHEN COALESCE(orders.SubtotalValue, orders.TotalValue) > 0
                           THEN CAST(items.SubTotal AS decimal(28, 4))
                                * CAST(orders.TotalValue AS decimal(28, 4))
                                / NULLIF(CAST(COALESCE(
                                    orders.SubtotalValue, orders.TotalValue
                                ) AS decimal(28, 4)), 0)
                           ELSE 0
                       END
                   ), 0), 0) AS decimal(18, 0)) AS revenue
            FROM dbo.SalesOrderItems items
            JOIN dbo.Products products ON products.ProductID = items.ProductID
            JOIN dbo.SalesOrders orders ON orders.OrderID = items.OrderID
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND orders.OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            GROUP BY products.ProductID, products.ProductName, products.Category
            ORDER BY sold_quantity DESC, revenue DESC
            """
        )
        return rows(self.cursor)

    def recent_orders(self) -> list[dict]:
        self.cursor.execute(
            """
            SELECT TOP 6 orders.OrderID AS order_id,
                   customers.CustomerName AS customer,
                   COALESCE(users.FullName, N'Không xác định') AS seller,
                   orders.TotalValue AS total_value,
                   orders.Status AS order_status,
                   orders.PaymentMethod AS payment_method,
                   COALESCE(orders.PaidAt, orders.CreatedAt,
                       CAST(orders.OrderDate AS datetime2)) AS created_at
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            LEFT JOIN dbo.Users users ON users.UserID = orders.CreatedBy
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
            ORDER BY COALESCE(orders.PaidAt, orders.CreatedAt,
                CAST(orders.OrderDate AS datetime2)) DESC
            """
        )
        return rows(self.cursor)

    def today_customers(self) -> list[dict]:
        self.cursor.execute(
            """
            SELECT DISTINCT customers.CustomerID AS customer_id,
                   customers.CustomerName AS name,
                   customers.ContactName AS contact_name,
                   customers.Phone AS phone
            FROM dbo.SalesOrders orders
            JOIN dbo.Customers customers ON customers.CustomerID = orders.CustomerID
            WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND orders.OrderDate = CONVERT(date, GETDATE())
            ORDER BY customers.CustomerName
            """
        )
        return rows(self.cursor)

    def revenue_summary(self) -> dict:
        self.cursor.execute(
            """
            SELECT COALESCE(SUM(TotalValue), 0) AS month_revenue,
                   COUNT(*) AS paid_orders,
                   COALESCE(AVG(CAST(TotalValue AS decimal(18, 2))), 0)
                       AS average_order,
                   COUNT(DISTINCT CustomerID) AS purchasing_customers
            FROM dbo.SalesOrders
            WHERE Status IN (N'Completed', N'Paid', N'Hoàn thành')
              AND OrderDate >= DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
            """
        )
        return one(self.cursor)

    def revenue_by_category(self) -> list[dict]:
        self.cursor.execute(
            """
            WITH revenue_lines AS
            (
                SELECT products.Category AS category,
                       CASE
                           WHEN COALESCE(orders.SubtotalValue, orders.TotalValue) > 0
                           THEN CAST(items.SubTotal AS decimal(28, 4))
                                * CAST(orders.TotalValue AS decimal(28, 4))
                                / NULLIF(CAST(COALESCE(
                                    orders.SubtotalValue, orders.TotalValue
                                ) AS decimal(28, 4)), 0)
                           ELSE 0
                       END AS revenue,
                       items.Quantity AS quantity
                FROM dbo.SalesOrderItems items
                JOIN dbo.Products products ON products.ProductID = items.ProductID
                JOIN dbo.SalesOrders orders ON orders.OrderID = items.OrderID
                WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
                  AND orders.OrderDate >= DATEFROMPARTS(
                      YEAR(GETDATE()), MONTH(GETDATE()), 1
                  )

                UNION ALL

                SELECT N'Chưa phân loại' AS category,
                       CAST(orders.TotalValue AS decimal(28, 4)) AS revenue,
                       0 AS quantity
                FROM dbo.SalesOrders orders
                WHERE orders.Status IN (N'Completed', N'Paid', N'Hoàn thành')
                  AND orders.OrderDate >= DATEFROMPARTS(
                      YEAR(GETDATE()), MONTH(GETDATE()), 1
                  )
                  AND NOT EXISTS
                  (
                      SELECT 1
                      FROM dbo.SalesOrderItems items
                      WHERE items.OrderID = orders.OrderID
                  )
            )
            SELECT category,
                   CAST(ROUND(COALESCE(SUM(revenue), 0), 0)
                       AS decimal(18, 0)) AS revenue,
                   SUM(quantity) AS quantity
            FROM revenue_lines
            GROUP BY category
            ORDER BY revenue DESC
            """
        )
        return rows(self.cursor)
