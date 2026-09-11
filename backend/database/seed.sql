/* SPDX-License-Identifier: MIT

    DX-Lab Core - safe demonstration data

    This file contains no SQL Server password and no real customer data.
    It is idempotent: existing rows with the same business key are preserved.

    Development-only web accounts:
      admin.demo / Admin@123  (Admin portal)
      sales.demo / Sales@123  (Employee portal)

    Change or remove these accounts before any public deployment.
*/

USE [DXLabCore];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    INSERT INTO dbo.Roles (RoleID, RoleName)
    SELECT source.RoleID, source.RoleName
    FROM
    (
        VALUES
            ('Admin', N'Quản trị viên'),
            ('CEO', N'Tổng Giám Đốc'),
            ('Manager', N'Quản lý'),
            ('Sales', N'Nhân viên kinh doanh'),
            ('Warehouse', N'Thủ kho')
    ) AS source (RoleID, RoleName)
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.Roles target WHERE target.RoleID = source.RoleID
    );

    INSERT INTO dbo.Users (Username, PasswordHash, FullName, RoleID, Status)
    SELECT source.Username, source.PasswordHash, source.FullName, source.RoleID, N'Active'
    FROM
    (
        VALUES
            (
                'admin.demo',
                'pbkdf2_sha256$600000$zeyQitX6eF-I1goFH68aVQ==$FqP79NRR48tI_G5-7Y2M87KWnj98OxB2Z27FGPKH2wY=',
                N'Quản trị viên Demo',
                'Admin'
            ),
            (
                'sales.demo',
                'pbkdf2_sha256$600000$mVWYQ-b05tec64TPfqS69g==$_vHsF2MFlXDHeGSfSqXjV4t8XeGNkrVMgxffjLpYF1o=',
                N'Nhân viên Demo',
                'Sales'
            )
    ) AS source (Username, PasswordHash, FullName, RoleID)
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.Users target WHERE target.Username = source.Username
    );

    INSERT INTO dbo.Customers
        (CustomerID, CustomerName, ContactName, Phone, Tier, Status)
    SELECT source.CustomerID, source.CustomerName, source.ContactName,
           source.Phone, source.Tier, N'Active'
    FROM
    (
        VALUES
            ('CUS-DEMO-001', N'Công ty Demo Alpha', N'Nguyễn An', '0900000001', N'VIP'),
            ('CUS-DEMO-002', N'Cửa hàng Demo Beta', N'Trần Bình', '0900000002', N'Standard'),
            ('CUS-DEMO-003', N'Khách hàng bán lẻ Demo', N'Lê Chi', '0900000003', N'Standard')
    ) AS source (CustomerID, CustomerName, ContactName, Phone, Tier)
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.Customers target WHERE target.CustomerID = source.CustomerID
    );

    INSERT INTO dbo.Products
        (ProductID, ProductName, Category, Price, Stock, ReorderLevel)
    SELECT source.ProductID, source.ProductName, source.Category,
           source.Price, source.Stock, source.ReorderLevel
    FROM
    (
        VALUES
            ('SP-DEMO-001', N'Laptop Demo 14', N'Laptop', CAST(18900000 AS decimal(18, 0)), 12, 5),
            ('SP-DEMO-002', N'Màn hình Demo 27 inch', N'Màn hình', CAST(5290000 AS decimal(18, 0)), 25, 8),
            ('SP-DEMO-003', N'Bàn phím cơ Demo', N'Phụ kiện', CAST(1290000 AS decimal(18, 0)), 40, 10)
    ) AS source (ProductID, ProductName, Category, Price, Stock, ReorderLevel)
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.Products target WHERE target.ProductID = source.ProductID
    );

    INSERT INTO dbo.Quotations
        (QuoteID, CustomerID, TotalValue, Status, CreatedDate)
    SELECT 'QT-DEMO-001', 'CUS-DEMO-001', 24190000, N'Draft', CONVERT(date, GETDATE())
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.Quotations WHERE QuoteID = 'QT-DEMO-001'
    );

    INSERT INTO dbo.Promotions
        (PromotionID, Title, Description, Tag, CustomerTier,
         StartDate, EndDate, Status, Color)
    SELECT source.PromotionID, source.Title, source.Description, source.Tag,
           source.CustomerTier, CONVERT(date, GETDATE()),
           DATEADD(day, source.DurationDays, CONVERT(date, GETDATE())),
           N'Active', source.Color
    FROM
    (
        VALUES
            ('KM-DEMO-01', N'Tuần lễ phụ kiện',
             N'Giảm 15% bàn phím, chuột và tai nghe.', N'-15%', N'Standard', 5, 'violet'),
            ('KM-DEMO-02', N'Combo văn phòng',
             N'Mua máy tính kèm màn hình với mức giá ưu đãi theo chương trình.', N'COMBO', N'Doanh nghiệp', 21, 'blue'),
            ('KM-DEMO-03', N'Khách hàng VIP',
             N'Tặng gói bảo hành mở rộng cho đơn hàng đủ điều kiện.', N'VIP', N'VIP', 30, 'orange')
    ) AS source
        (PromotionID, Title, Description, Tag, CustomerTier, DurationDays, Color)
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.Promotions target
        WHERE target.PromotionID = source.PromotionID
    );

    UPDATE dbo.Promotions
    SET DiscountType = 'PERCENT', DiscountValue = 15,
        MinOrderValue = 0, AppliedCategory = N'Phụ kiện'
    WHERE PromotionID = 'KM-DEMO-01' AND DiscountValue = 0;

    UPDATE dbo.Promotions
    SET DiscountType = 'FIXED', DiscountValue = 1200000,
        MinOrderValue = 10000000
    WHERE PromotionID = 'KM-DEMO-02' AND DiscountValue = 0;

    INSERT INTO dbo.SalesOrders
        (OrderID, CustomerID, CreatedBy, TotalValue, Status, OrderDate,
         PaymentMethod, CreatedAt, PaidAt)
    SELECT 'SO-DEMO-001', 'CUS-DEMO-001', user_data.UserID,
           24190000, N'Paid', CONVERT(date, GETDATE()), N'Cash',
           SYSDATETIME(), SYSDATETIME()
    FROM dbo.Users user_data
    WHERE user_data.Username = 'sales.demo'
      AND NOT EXISTS
      (
          SELECT 1 FROM dbo.SalesOrders WHERE OrderID = 'SO-DEMO-001'
      );

    INSERT INTO dbo.SalesOrderItems (OrderID, ProductID, Quantity, UnitPrice)
    SELECT source.OrderID, source.ProductID, source.Quantity, source.UnitPrice
    FROM
    (
        VALUES
            ('SO-DEMO-001', 'SP-DEMO-001', 1, CAST(18900000 AS decimal(18, 0))),
            ('SO-DEMO-001', 'SP-DEMO-002', 1, CAST(5290000 AS decimal(18, 0)))
    ) AS source (OrderID, ProductID, Quantity, UnitPrice)
    WHERE EXISTS
    (
        SELECT 1 FROM dbo.SalesOrders orders WHERE orders.OrderID = source.OrderID
    )
      AND NOT EXISTS
      (
          SELECT 1
          FROM dbo.SalesOrderItems target
          WHERE target.OrderID = source.OrderID
            AND target.ProductID = source.ProductID
      );

    INSERT INTO dbo.StockMovements
        (MovementID, ProductID, MovementType, Quantity, ReferenceID, MovementDate)
    SELECT 'SM-DEMO-001', 'SP-DEMO-001', 'OUT', 1,
           'SO-DEMO-001', CONVERT(date, GETDATE())
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.StockMovements WHERE MovementID = 'SM-DEMO-001'
    );

    INSERT INTO dbo.PurchaseRequests
        (RequestID, ProductID, Quantity, Reason, Requester, TotalValue, Status)
    SELECT 'PR-DEMO-001', 'SP-DEMO-001', 5,
           N'Bổ sung tồn kho phục vụ bản demo', N'Nhân viên Demo',
           94500000, N'Pending approval'
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.PurchaseRequests WHERE RequestID = 'PR-DEMO-001'
    );

    IF NOT EXISTS
    (
        SELECT 1 FROM dbo.Activities WHERE Description = N'Khởi tạo dữ liệu demo DX-Lab Core'
    )
    BEGIN
        INSERT INTO dbo.Activities (ActivityTime, Description, Category)
        VALUES
            (CONVERT(varchar(5), GETDATE(), 108), N'Khởi tạo dữ liệu demo DX-Lab Core', N'System');
    END;

    INSERT INTO dbo.SystemSettings (SettingKey, SettingValue)
    SELECT source.SettingKey, source.SettingValue
    FROM
    (
        VALUES
            ('company_name', N'DX-Lab Core'),
            ('company_phone', N''),
            ('company_address', N''),
            ('tax_code', N'')
    ) AS source (SettingKey, SettingValue)
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.SystemSettings target
        WHERE target.SettingKey = source.SettingKey
    );

    COMMIT TRANSACTION;
    PRINT N'DXLabCore demonstration data is ready.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
