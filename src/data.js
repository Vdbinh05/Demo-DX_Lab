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

export const products = [
  { id: "SP001", name: "Laptop Pro 14", category: "Laptop", price: 28900000, stock: 12, reorder: 20, sold: 18, status: "Sắp hết" },
  { id: "SP002", name: "Màn hình 27 QHD", category: "Màn hình", price: 7290000, stock: 48, reorder: 15, sold: 42, status: "Còn hàng" },
  { id: "SP003", name: "Bàn phím cơ", category: "Phụ kiện", price: 1890000, stock: 7, reorder: 10, sold: 67, status: "Sắp hết" },
  { id: "SP004", name: "Chuột Wireless Pro", category: "Phụ kiện", price: 1290000, stock: 63, reorder: 20, sold: 91, status: "Còn hàng" },
  { id: "SP005", name: "Mini PC Office", category: "Máy tính", price: 15900000, stock: 26, reorder: 12, sold: 24, status: "Còn hàng" },
  { id: "SP006", name: "Tai nghe Studio", category: "Âm thanh", price: 2490000, stock: 34, reorder: 10, sold: 36, status: "Còn hàng" },
];

export const customers = [
  { id: "CUS-001", name: "Công ty Minh Phát", contact: "Nguyễn Minh", phone: "0901 234 567", tier: "VIP", status: "Hoạt động" },
  { id: "CUS-002", name: "An Khang Retail", contact: "Trần Khang", phone: "0912 555 221", tier: "Thân thiết", status: "Hoạt động" },
  { id: "CUS-003", name: "Hải Đăng Store", contact: "Lê Hải", phone: "0988 771 332", tier: "Tiêu chuẩn", status: "Hoạt động" },
  { id: "CUS-004", name: "Nova Solutions", contact: "Phạm Anh", phone: "0933 880 991", tier: "Doanh nghiệp", status: "Hoạt động" },
];

export const orders = [
  { id: "SO-2026-0018", customer: "Công ty Minh Phát", seller: "Huy", value: 86400000, status: "Hoàn thành", date: "08/09/2026" },
  { id: "SO-2026-0017", customer: "An Khang Retail", seller: "Lan", value: 36450000, status: "Đang xử lý", date: "08/09/2026" },
  { id: "SO-2026-0016", customer: "Khách lẻ", seller: "Huy", value: 18900000, status: "Hoàn thành", date: "07/09/2026" },
  { id: "SO-2026-0015", customer: "Nova Solutions", seller: "Minh", value: 125600000, status: "Chờ duyệt", date: "07/09/2026" },
  { id: "SO-2026-0014", customer: "Hải Đăng Store", seller: "Lan", value: 27580000, status: "Hoàn thành", date: "06/09/2026" },
];

export const promotions = [
  { id: "KM01", title: "Tuần lễ phụ kiện", description: "Giảm 15% bàn phím, chuột và tai nghe.", tag: "-15%", expires: "Còn 5 ngày", color: "violet" },
  { id: "KM02", title: "Combo văn phòng", description: "Mua Mini PC kèm màn hình, tiết kiệm 1.200.000 ₫.", tag: "COMBO", expires: "Đến 30/09", color: "blue" },
  { id: "KM03", title: "Khách hàng VIP", description: "Tặng gói bảo hành mở rộng cho đơn từ 50 triệu.", tag: "VIP", expires: "Tháng 9", color: "orange" },
];

export const employees = [
  { id: 0, name: "DX-Lab Administrator", username: "admin", role: "Admin", status: "Active", lastLogin: "20:10 hôm nay" },
  { id: 1, name: "Chu Quốc Huy", username: "hoan", role: "Sales", status: "Active", lastLogin: "19:42 hôm nay" },
  { id: 2, name: "Nguyễn Minh Anh", username: "minhanh", role: "Manager", status: "Active", lastLogin: "17:28 hôm nay" },
  { id: 3, name: "Trần Hoàng Lan", username: "lan.sales", role: "Sales", status: "Active", lastLogin: "16:05 hôm nay" },
  { id: 4, name: "Lê Thanh Bình", username: "binh.kho", role: "Warehouse", status: "Locked", lastLogin: "02/09/2026" },
];

export const monthlyRevenue = [
  { month: "T4", value: 318 },
  { month: "T5", value: 354 },
  { month: "T6", value: 329 },
  { month: "T7", value: 402 },
  { month: "T8", value: 431 },
  { month: "T9", value: 486 },
];
