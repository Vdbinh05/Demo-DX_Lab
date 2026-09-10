// SPDX-License-Identifier: MIT
export const portalConfig = {
  employee: {
    label: "Nhân viên",
    shortLabel: "Khu vực bán hàng",
    description: "Bán hàng, xem sản phẩm, khuyến mãi và đơn cá nhân.",
    icon: "BadgeCheck",
    roles: ["Sales", "Warehouse", "Employee"],
    landingPage: "pos",
  },
  admin: {
    label: "Quản trị viên",
    shortLabel: "Trung tâm quản trị",
    description: "Quản lý dữ liệu, nhân sự và báo cáo doanh thu.",
    icon: "ShieldCheck",
    roles: ["Admin"],
    landingPage: "overview",
  },
};

export const menus = {
  employee: [
    { id: "pos", label: "Bán hàng", icon: "ShoppingCart", permission: "sales.create" },
    { id: "catalog", label: "Danh mục sản phẩm", icon: "PackageSearch", permission: "products.read" },
    { id: "promotions", label: "Khuyến mãi", icon: "Megaphone", permission: "promotions.read" },
    { id: "my-orders", label: "Đơn hàng của tôi", icon: "ReceiptText", permission: "orders.read_own" },
    { id: "customers", label: "Khách hàng", icon: "UsersRound", permission: "customers.read" },
  ],
  admin: [
    { id: "overview", label: "Tổng quan", icon: "LayoutDashboard", permission: "dashboard.read" },
    { id: "revenue", label: "Doanh thu", icon: "ChartNoAxesCombined", permission: "revenue.read" },
    { id: "orders", label: "Đơn hàng", icon: "ClipboardList", permission: "orders.read_all" },
    { id: "products", label: "Sản phẩm", icon: "Boxes", permission: "products.write" },
    { id: "customers", label: "Khách hàng", icon: "UsersRound", permission: "customers.write" },
    { id: "inventory", label: "Kho hàng", icon: "Warehouse", permission: "inventory.write" },
    { id: "users", label: "Tài khoản", icon: "UserCog", permission: "users.manage" },
    { id: "settings", label: "Cài đặt", icon: "Settings", permission: "settings.manage" },
  ],
};

export const permissionsByPortal = {
  employee: new Set([
    "sales.create",
    "products.read",
    "promotions.read",
    "orders.read_own",
    "customers.read",
  ]),
  admin: new Set([
    "dashboard.read",
    "revenue.read",
    "orders.read_all",
    "orders.write",
    "products.read",
    "products.write",
    "customers.read",
    "customers.write",
    "inventory.write",
    "users.manage",
    "settings.manage",
  ]),
};
