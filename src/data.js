export const menu = [
  { id: "dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  {
    id: "sales",
    label: "Sales",
    icon: "ShoppingCart",
    children: [
      ["customers", "Customers"],
      ["products", "Products"],
      ["orders", "Orders"],
      ["quotations", "Quotations"],
    ],
  },
  {
    id: "inventory",
    label: "Inventory",
    icon: "Boxes",
    children: [
      ["stock", "Stock"],
      ["movement", "Stock Movement"],
      ["purchase", "Purchase Requests"],
    ],
  },
  {
    id: "workflow",
    label: "Workflow",
    icon: "GitBranch",
    children: [
      ["tasks", "My Tasks"],
      ["approval", "Pending Approval"],
      ["history", "History"],
    ],
  },
  { id: "knowledge", label: "Knowledge / Documents", icon: "BookOpen" },
  { id: "ai", label: "AI Copilot", icon: "Sparkles" },
  { id: "admin", label: "Administration", icon: "Settings" },
];

export const customers = [
  { id: "CUS-001", name: "Công ty Minh Phát", contact: "Nguyễn Minh", phone: "0901 234 567", tier: "VIP", status: "Active" },
  { id: "CUS-002", name: "An Khang Retail", contact: "Trần Khang", phone: "0912 555 221", tier: "Standard", status: "Active" },
  { id: "CUS-003", name: "Hải Đăng Store", contact: "Lê Hải", phone: "0988 771 332", tier: "Standard", status: "Active" },
  { id: "CUS-004", name: "Nova Solutions", contact: "Phạm Anh", phone: "0933 880 991", tier: "Enterprise", status: "Active" },
];

export const products = [
  { id: "SP001", name: "Laptop Pro 14", category: "Laptop", price: 28900000, stock: 12, reorder: 20, status: "Low stock" },
  { id: "SP002", name: "Monitor 27 QHD", category: "Monitor", price: 7290000, stock: 48, reorder: 15, status: "In stock" },
  { id: "SP003", name: "Keyboard Mechanical", category: "Accessories", price: 1890000, stock: 7, reorder: 10, status: "Low stock" },
  { id: "SP004", name: "Mouse Wireless Pro", category: "Accessories", price: 1290000, stock: 63, reorder: 20, status: "In stock" },
  { id: "SP005", name: "Mini PC Office", category: "Computer", price: 15900000, stock: 26, reorder: 12, status: "In stock" },
];

export const orders = [
  { id: "SO-2026-0018", customer: "Công ty Minh Phát", value: 86400000, status: "Approved", date: "08/09/2026" },
  { id: "SO-2026-0017", customer: "An Khang Retail", value: 36450000, status: "Processing", date: "08/09/2026" },
  { id: "SO-2026-0016", customer: "Hải Đăng Store", value: 18900000, status: "Completed", date: "07/09/2026" },
  { id: "SO-2026-0015", customer: "Nova Solutions", value: 125600000, status: "Pending approval", date: "07/09/2026" },
];

export const purchaseRequests = [
  { id: "PR-2026-009", item: "Laptop Pro 14", qty: 100, reason: "Stock below reorder level", requester: "AI Copilot", status: "Pending approval", value: 2890000000 },
  { id: "PR-2026-008", item: "Keyboard Mechanical", qty: 50, reason: "Low stock", requester: "Nguyễn Văn A", status: "Approved", value: 94500000 },
  { id: "PR-2026-007", item: "Monitor 27 QHD", qty: 30, reason: "Forecasted demand", requester: "Sales", status: "Draft", value: 218700000 },
];

export const activities = [
  ["10:42", "AI Copilot created PR-2026-009", "AI"],
  ["10:15", "SO-2026-0018 was approved", "Approval"],
  ["09:48", "Stock alert for SP001", "Inventory"],
  ["09:12", "New order SO-2026-0017", "Sales"],
];