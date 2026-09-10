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

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrders_OrderDate' AND object_id = OBJECT_ID(N'dbo.SalesOrders'))
    CREATE INDEX IX_SalesOrders_OrderDate ON dbo.SalesOrders (OrderDate DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrders_CreatedBy' AND object_id = OBJECT_ID(N'dbo.SalesOrders'))
    CREATE INDEX IX_SalesOrders_CreatedBy ON dbo.SalesOrders (CreatedBy, OrderDate DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_SalesOrderItems_OrderID' AND object_id = OBJECT_ID(N'dbo.SalesOrderItems'))
    CREATE INDEX IX_SalesOrderItems_OrderID ON dbo.SalesOrderItems (OrderID);
GO

PRINT N'DXLabCore schema is ready.';
GO
