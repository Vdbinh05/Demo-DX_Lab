/* SPDX-License-Identifier: MIT

    DX-Lab Core - SQL Server schema

    This script is safe to run more than once. It creates the DXLabCore
    database and any missing tables without deleting existing data.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF DB_ID(N'DXLabCore') IS NULL
BEGIN
    PRINT N'Creating database DXLabCore...';
    EXEC(N'CREATE DATABASE [DXLabCore]');
END;
GO

USE [DXLabCore];
GO

IF OBJECT_ID(N'dbo.Roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Roles
    (
        RoleID varchar(20) NOT NULL,
        RoleName nvarchar(50) NOT NULL,
        CONSTRAINT PK_Roles PRIMARY KEY CLUSTERED (RoleID)
    );
END;
GO

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users
    (
        UserID int IDENTITY(1, 1) NOT NULL,
        Username varchar(50) NOT NULL,
        PasswordHash varchar(255) NOT NULL,
        FullName nvarchar(100) NOT NULL,
        RoleID varchar(20) NOT NULL,
        Status nvarchar(20) NULL
            CONSTRAINT DF_Users_Status DEFAULT N'Active',
        CreatedAt datetime NULL
            CONSTRAINT DF_Users_CreatedAt DEFAULT GETDATE(),
        CONSTRAINT PK_Users PRIMARY KEY CLUSTERED (UserID),
        CONSTRAINT UQ_Users_Username UNIQUE (Username),
        CONSTRAINT FK_Users_Roles FOREIGN KEY (RoleID)
            REFERENCES dbo.Roles (RoleID)
    );
END;
GO

IF COL_LENGTH(N'dbo.Users', N'LastLoginAt') IS NULL
BEGIN
    ALTER TABLE dbo.Users ADD LastLoginAt datetime2 NULL;
END;
GO

IF OBJECT_ID(N'dbo.UserSessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.UserSessions
    (
        TokenID char(32) NOT NULL,
        UserID int NOT NULL,
        CreatedAt datetime2 NOT NULL
            CONSTRAINT DF_UserSessions_CreatedAt DEFAULT SYSDATETIME(),
        ExpiresAt datetime2 NOT NULL,
        RevokedAt datetime2 NULL,
        CONSTRAINT PK_UserSessions PRIMARY KEY CLUSTERED (TokenID),
        CONSTRAINT FK_UserSessions_Users FOREIGN KEY (UserID)
            REFERENCES dbo.Users (UserID) ON DELETE CASCADE
    );
END;
GO

IF OBJECT_ID(N'dbo.Customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Customers
    (
        CustomerID varchar(20) NOT NULL,
        CustomerName nvarchar(255) NOT NULL,
        ContactName nvarchar(100) NULL,
        Phone varchar(20) NULL,
        Tier nvarchar(30) NULL
            CONSTRAINT DF_Customers_Tier DEFAULT N'Standard',
        Status nvarchar(20) NULL
            CONSTRAINT DF_Customers_Status DEFAULT N'Active',
        CONSTRAINT PK_Customers PRIMARY KEY CLUSTERED (CustomerID)
    );
END;
GO

IF COL_LENGTH(N'dbo.Customers', N'CreatedAt') IS NULL
BEGIN
    ALTER TABLE dbo.Customers ADD CreatedAt datetime2 NULL
        CONSTRAINT DF_Customers_CreatedAt DEFAULT SYSDATETIME();
END;
GO

IF OBJECT_ID(N'dbo.Products', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Products
    (
        ProductID varchar(20) NOT NULL,
        ProductName nvarchar(255) NOT NULL,
        Category nvarchar(50) NOT NULL,
        Price decimal(18, 0) NOT NULL,
        Stock int NOT NULL
            CONSTRAINT DF_Products_Stock DEFAULT 0,
        ReorderLevel int NOT NULL
            CONSTRAINT DF_Products_ReorderLevel DEFAULT 10,
        CONSTRAINT PK_Products PRIMARY KEY CLUSTERED (ProductID)
    );
END;
GO

IF OBJECT_ID(N'dbo.Promotions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Promotions
    (
        PromotionID varchar(20) NOT NULL,
        Title nvarchar(255) NOT NULL,
        Description nvarchar(1000) NOT NULL,
        Tag nvarchar(30) NOT NULL,
        CustomerTier nvarchar(30) NULL,
        StartDate date NOT NULL
            CONSTRAINT DF_Promotions_StartDate DEFAULT CONVERT(date, GETDATE()),
        EndDate date NOT NULL,
        Status nvarchar(20) NOT NULL
            CONSTRAINT DF_Promotions_Status DEFAULT N'Active',
        Color varchar(20) NOT NULL
            CONSTRAINT DF_Promotions_Color DEFAULT 'blue',
        CreatedAt datetime2 NOT NULL
            CONSTRAINT DF_Promotions_CreatedAt DEFAULT SYSDATETIME(),
        UpdatedAt datetime2 NOT NULL
            CONSTRAINT DF_Promotions_UpdatedAt DEFAULT SYSDATETIME(),
        CONSTRAINT PK_Promotions PRIMARY KEY CLUSTERED (PromotionID),
        CONSTRAINT CK_Promotions_DateRange CHECK (EndDate >= StartDate)
    );
END;
GO

IF OBJECT_ID(N'dbo.Quotations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Quotations
    (
        QuoteID varchar(30) NOT NULL,
        CustomerID varchar(20) NOT NULL,
        TotalValue decimal(18, 0) NULL
            CONSTRAINT DF_Quotations_TotalValue DEFAULT 0,
        Status nvarchar(30) NULL
            CONSTRAINT DF_Quotations_Status DEFAULT N'Draft',
        CreatedDate date NULL
            CONSTRAINT DF_Quotations_CreatedDate DEFAULT CONVERT(date, GETDATE()),
        CONSTRAINT PK_Quotations PRIMARY KEY CLUSTERED (QuoteID),
        CONSTRAINT FK_Quotations_Customers FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers (CustomerID)
    );
END;
GO

IF COL_LENGTH(N'dbo.Promotions', N'DiscountType') IS NULL
BEGIN
    ALTER TABLE dbo.Promotions ADD DiscountType varchar(10) NOT NULL
        CONSTRAINT DF_Promotions_DiscountType DEFAULT 'PERCENT';
END;
GO

IF COL_LENGTH(N'dbo.Promotions', N'DiscountValue') IS NULL
BEGIN
    ALTER TABLE dbo.Promotions ADD DiscountValue decimal(18, 2) NOT NULL
        CONSTRAINT DF_Promotions_DiscountValue DEFAULT 0;
END;
GO

IF COL_LENGTH(N'dbo.Promotions', N'MinOrderValue') IS NULL
BEGIN
    ALTER TABLE dbo.Promotions ADD MinOrderValue decimal(18, 0) NOT NULL
        CONSTRAINT DF_Promotions_MinOrderValue DEFAULT 0;
END;
GO

IF COL_LENGTH(N'dbo.Promotions', N'MaxUses') IS NULL
    ALTER TABLE dbo.Promotions ADD MaxUses int NULL;
GO

IF COL_LENGTH(N'dbo.Promotions', N'UsedCount') IS NULL
BEGIN
    ALTER TABLE dbo.Promotions ADD UsedCount int NOT NULL
        CONSTRAINT DF_Promotions_UsedCount DEFAULT 0;
END;
GO

IF COL_LENGTH(N'dbo.Promotions', N'AppliedProductID') IS NULL
    ALTER TABLE dbo.Promotions ADD AppliedProductID varchar(20) NULL;
GO

IF COL_LENGTH(N'dbo.Promotions', N'AppliedCategory') IS NULL
    ALTER TABLE dbo.Promotions ADD AppliedCategory nvarchar(50) NULL;
GO

IF OBJECT_ID(N'dbo.SalesOrders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SalesOrders
    (
        OrderID varchar(30) NOT NULL,
        CustomerID varchar(20) NOT NULL,
        CreatedBy int NULL,
        TotalValue decimal(18, 0) NOT NULL
            CONSTRAINT DF_SalesOrders_TotalValue DEFAULT 0,
        Status nvarchar(30) NOT NULL,
        OrderDate date NULL
            CONSTRAINT DF_SalesOrders_OrderDate DEFAULT CONVERT(date, GETDATE()),
        CONSTRAINT PK_SalesOrders PRIMARY KEY CLUSTERED (OrderID),
        CONSTRAINT FK_SalesOrders_Customers FOREIGN KEY (CustomerID)
            REFERENCES dbo.Customers (CustomerID),
        CONSTRAINT FK_SalesOrders_Users FOREIGN KEY (CreatedBy)
            REFERENCES dbo.Users (UserID)
    );
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'PaymentMethod') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD PaymentMethod nvarchar(30) NULL
        CONSTRAINT DF_SalesOrders_PaymentMethod DEFAULT N'Cash';
    EXEC(N'UPDATE dbo.SalesOrders SET PaymentMethod = N''Cash'' WHERE PaymentMethod IS NULL;');
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'CreatedAt') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD CreatedAt datetime2 NULL
        CONSTRAINT DF_SalesOrders_CreatedAt DEFAULT SYSDATETIME();
    EXEC(N'UPDATE dbo.SalesOrders
        SET CreatedAt = CAST(OrderDate AS datetime2)
        WHERE CreatedAt IS NULL AND OrderDate IS NOT NULL;');
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'PaidAt') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD PaidAt datetime2 NULL;
    EXEC(N'UPDATE dbo.SalesOrders
        SET PaidAt = COALESCE(CreatedAt, CAST(OrderDate AS datetime2))
        WHERE Status IN (N''Completed'', N''Paid'', N''Hoàn thành'');');
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'PaymentStatus') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD PaymentStatus nvarchar(30) NULL
        CONSTRAINT DF_SalesOrders_PaymentStatus DEFAULT N'Paid';
    EXEC(N'UPDATE dbo.SalesOrders
        SET PaymentStatus = CASE
            WHEN Status IN (N''Completed'', N''Paid'', N''Hoàn thành'') THEN N''Paid''
            ELSE N''Unpaid'' END
        WHERE PaymentStatus IS NULL;');
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'OrderStatus') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD OrderStatus nvarchar(30) NULL
        CONSTRAINT DF_SalesOrders_OrderStatus DEFAULT N'Completed';
    EXEC(N'UPDATE dbo.SalesOrders
        SET OrderStatus = CASE
            WHEN Status IN (N''Cancelled'', N''Canceled'', N''Đã hủy'') THEN N''Cancelled''
            ELSE N''Completed'' END
        WHERE OrderStatus IS NULL;');
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'IdempotencyKey') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD IdempotencyKey varchar(64) NULL;
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'RequestFingerprint') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD RequestFingerprint char(64) NULL;
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'SubtotalValue') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD SubtotalValue decimal(18, 0) NULL;
    EXEC(N'UPDATE dbo.SalesOrders SET SubtotalValue = TotalValue
           WHERE SubtotalValue IS NULL;');
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'DiscountValue') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrders ADD DiscountValue decimal(18, 0) NOT NULL
        CONSTRAINT DF_SalesOrders_DiscountValue DEFAULT 0;
END;
GO

IF COL_LENGTH(N'dbo.SalesOrders', N'PromotionID') IS NULL
    ALTER TABLE dbo.SalesOrders ADD PromotionID varchar(20) NULL;
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_SalesOrders_IdempotencyKey'
      AND object_id = OBJECT_ID(N'dbo.SalesOrders')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_SalesOrders_IdempotencyKey
        ON dbo.SalesOrders (IdempotencyKey)
        WHERE IdempotencyKey IS NOT NULL;
END;
GO

IF OBJECT_ID(N'dbo.SalesOrderItems', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SalesOrderItems
    (
        ItemID int IDENTITY(1, 1) NOT NULL,
        OrderID varchar(30) NOT NULL,
        ProductID varchar(20) NOT NULL,
        Quantity int NOT NULL,
        UnitPrice decimal(18, 0) NOT NULL,
        SubTotal AS (Quantity * UnitPrice),
        CONSTRAINT PK_SalesOrderItems PRIMARY KEY CLUSTERED (ItemID),
        CONSTRAINT CK_SalesOrderItems_Quantity CHECK (Quantity > 0),
        CONSTRAINT FK_SalesOrderItems_Orders FOREIGN KEY (OrderID)
            REFERENCES dbo.SalesOrders (OrderID) ON DELETE CASCADE,
        CONSTRAINT FK_SalesOrderItems_Products FOREIGN KEY (ProductID)
            REFERENCES dbo.Products (ProductID)
    );
END;
GO

IF COL_LENGTH(N'dbo.SalesOrderItems', N'ProductNameSnapshot') IS NULL
BEGIN
    ALTER TABLE dbo.SalesOrderItems ADD ProductNameSnapshot nvarchar(255) NULL;
    EXEC(N'UPDATE items
        SET ProductNameSnapshot = products.ProductName
        FROM dbo.SalesOrderItems items
        JOIN dbo.Products products ON products.ProductID = items.ProductID
        WHERE items.ProductNameSnapshot IS NULL;');
END;
GO

IF OBJECT_ID(N'dbo.StockMovements', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.StockMovements
    (
        MovementID varchar(30) NOT NULL,
        ProductID varchar(20) NOT NULL,
        MovementType varchar(10) NOT NULL,
        Quantity int NOT NULL,
        ReferenceID varchar(30) NULL,
        MovementDate date NULL
            CONSTRAINT DF_StockMovements_MovementDate DEFAULT CONVERT(date, GETDATE()),
        CONSTRAINT PK_StockMovements PRIMARY KEY CLUSTERED (MovementID),
        CONSTRAINT CK_StockMovements_Type CHECK (MovementType IN ('IN', 'OUT')),
        CONSTRAINT CK_StockMovements_Quantity CHECK (Quantity > 0),
        CONSTRAINT FK_StockMovements_Products FOREIGN KEY (ProductID)
            REFERENCES dbo.Products (ProductID)
    );
END;
GO

IF OBJECT_ID(N'dbo.PurchaseRequests', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.PurchaseRequests
    (
        RequestID varchar(30) NOT NULL,
        ProductID varchar(20) NOT NULL,
        Quantity int NOT NULL,
        Reason nvarchar(255) NOT NULL,
        Requester nvarchar(100) NOT NULL,
        TotalValue decimal(18, 0) NOT NULL,
        Status nvarchar(30) NULL
            CONSTRAINT DF_PurchaseRequests_Status DEFAULT N'Pending approval',
        CreatedAt datetime NULL
            CONSTRAINT DF_PurchaseRequests_CreatedAt DEFAULT GETDATE(),
        CONSTRAINT PK_PurchaseRequests PRIMARY KEY CLUSTERED (RequestID),
        CONSTRAINT CK_PurchaseRequests_Quantity CHECK (Quantity > 0),
        CONSTRAINT FK_PurchaseRequests_Products FOREIGN KEY (ProductID)
            REFERENCES dbo.Products (ProductID)
    );
END;
GO

IF COL_LENGTH(N'dbo.StockMovements', N'Reason') IS NULL
    ALTER TABLE dbo.StockMovements ADD Reason nvarchar(255) NULL;
GO

IF COL_LENGTH(N'dbo.StockMovements', N'PerformedBy') IS NULL
    ALTER TABLE dbo.StockMovements ADD PerformedBy int NULL;
GO

IF COL_LENGTH(N'dbo.StockMovements', N'CreatedAt') IS NULL
BEGIN
    ALTER TABLE dbo.StockMovements ADD CreatedAt datetime2 NULL
        CONSTRAINT DF_StockMovements_CreatedAt DEFAULT SYSDATETIME();
    EXEC(N'UPDATE dbo.StockMovements
           SET CreatedAt = CAST(MovementDate AS datetime2)
           WHERE CreatedAt IS NULL AND MovementDate IS NOT NULL;');
END;
GO

IF OBJECT_ID(N'dbo.Activities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Activities
    (
        ActivityID int IDENTITY(1, 1) NOT NULL,
        ActivityTime varchar(10) NOT NULL,
        Description nvarchar(255) NOT NULL,
        Category nvarchar(50) NOT NULL,
        CreatedAt datetime NULL
            CONSTRAINT DF_Activities_CreatedAt DEFAULT GETDATE(),
        CONSTRAINT PK_Activities PRIMARY KEY CLUSTERED (ActivityID)
    );
END;
GO

IF OBJECT_ID(N'dbo.SystemSettings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SystemSettings
    (
        SettingKey varchar(50) NOT NULL,
        SettingValue nvarchar(500) NOT NULL,
        UpdatedAt datetime2 NOT NULL
            CONSTRAINT DF_SystemSettings_UpdatedAt DEFAULT SYSDATETIME(),
        UpdatedBy int NULL,
        CONSTRAINT PK_SystemSettings PRIMARY KEY CLUSTERED (SettingKey),
        CONSTRAINT FK_SystemSettings_Users FOREIGN KEY (UpdatedBy)
            REFERENCES dbo.Users (UserID)
    );
END;
GO

IF COL_LENGTH(N'dbo.Activities', N'UserID') IS NULL
    ALTER TABLE dbo.Activities ADD UserID int NULL;
GO

IF COL_LENGTH(N'dbo.Activities', N'Action') IS NULL
    ALTER TABLE dbo.Activities ADD Action varchar(50) NULL;
GO

IF COL_LENGTH(N'dbo.Activities', N'EntityType') IS NULL
    ALTER TABLE dbo.Activities ADD EntityType varchar(50) NULL;
GO

IF COL_LENGTH(N'dbo.Activities', N'EntityID') IS NULL
    ALTER TABLE dbo.Activities ADD EntityID varchar(50) NULL;
GO

IF COL_LENGTH(N'dbo.Activities', N'OldValues') IS NULL
    ALTER TABLE dbo.Activities ADD OldValues nvarchar(max) NULL;
GO

IF COL_LENGTH(N'dbo.Activities', N'NewValues') IS NULL
    ALTER TABLE dbo.Activities ADD NewValues nvarchar(max) NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrders_OrderDate' AND object_id = OBJECT_ID(N'dbo.SalesOrders'))
    CREATE INDEX IX_SalesOrders_OrderDate ON dbo.SalesOrders (OrderDate DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrders_CreatedBy' AND object_id = OBJECT_ID(N'dbo.SalesOrders'))
    CREATE INDEX IX_SalesOrders_CreatedBy ON dbo.SalesOrders (CreatedBy, OrderDate DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrders_CustomerDate' AND object_id = OBJECT_ID(N'dbo.SalesOrders'))
    CREATE INDEX IX_SalesOrders_CustomerDate ON dbo.SalesOrders (CustomerID, OrderDate DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrderItems_OrderID' AND object_id = OBJECT_ID(N'dbo.SalesOrderItems'))
    CREATE INDEX IX_SalesOrderItems_OrderID ON dbo.SalesOrderItems (OrderID);
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_Promotions_DiscountType')
    ALTER TABLE dbo.Promotions ADD CONSTRAINT CK_Promotions_DiscountType
        CHECK (DiscountType IN ('PERCENT', 'FIXED'));
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_Promotions_DiscountValue')
    ALTER TABLE dbo.Promotions ADD CONSTRAINT CK_Promotions_DiscountValue
        CHECK (DiscountValue >= 0 AND (DiscountType <> 'PERCENT' OR DiscountValue <= 100));
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_Promotions_Usage')
    ALTER TABLE dbo.Promotions ADD CONSTRAINT CK_Promotions_Usage
        CHECK (UsedCount >= 0 AND (MaxUses IS NULL OR MaxUses > 0));
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_Products_NonNegativeValues')
    ALTER TABLE dbo.Products WITH CHECK ADD CONSTRAINT CK_Products_NonNegativeValues
        CHECK (Price >= 0 AND Stock >= 0 AND ReorderLevel >= 0);
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_SalesOrders_MoneyValues')
    ALTER TABLE dbo.SalesOrders WITH CHECK ADD CONSTRAINT CK_SalesOrders_MoneyValues
        CHECK
        (
            TotalValue >= 0
            AND (SubtotalValue IS NULL OR SubtotalValue >= 0)
            AND DiscountValue >= 0
            AND (SubtotalValue IS NULL OR SubtotalValue - DiscountValue = TotalValue)
        );
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_SalesOrderItems_UnitPrice')
    ALTER TABLE dbo.SalesOrderItems WITH CHECK ADD CONSTRAINT CK_SalesOrderItems_UnitPrice
        CHECK (UnitPrice >= 0);
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_Promotions_Products')
    ALTER TABLE dbo.Promotions ADD CONSTRAINT FK_Promotions_Products
        FOREIGN KEY (AppliedProductID) REFERENCES dbo.Products (ProductID);
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_SalesOrders_Promotions')
    ALTER TABLE dbo.SalesOrders ADD CONSTRAINT FK_SalesOrders_Promotions
        FOREIGN KEY (PromotionID) REFERENCES dbo.Promotions (PromotionID);
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_StockMovements_Users')
    ALTER TABLE dbo.StockMovements ADD CONSTRAINT FK_StockMovements_Users
        FOREIGN KEY (PerformedBy) REFERENCES dbo.Users (UserID);
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_Activities_Users')
    ALTER TABLE dbo.Activities ADD CONSTRAINT FK_Activities_Users
        FOREIGN KEY (UserID) REFERENCES dbo.Users (UserID);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Promotions_ActiveDates' AND object_id = OBJECT_ID(N'dbo.Promotions'))
    CREATE INDEX IX_Promotions_ActiveDates ON dbo.Promotions (Status, StartDate, EndDate);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_StockMovements_ProductDate' AND object_id = OBJECT_ID(N'dbo.StockMovements'))
    CREATE INDEX IX_StockMovements_ProductDate ON dbo.StockMovements (ProductID, CreatedAt DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Activities_CreatedAt' AND object_id = OBJECT_ID(N'dbo.Activities'))
    CREATE INDEX IX_Activities_CreatedAt ON dbo.Activities (CreatedAt DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_UserSessions_UserActive' AND object_id = OBJECT_ID(N'dbo.UserSessions'))
    CREATE INDEX IX_UserSessions_UserActive ON dbo.UserSessions (UserID, RevokedAt, ExpiresAt);
GO

PRINT N'DXLabCore schema is ready.';
GO
