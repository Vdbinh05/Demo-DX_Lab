import React, { useState } from "react";
import {
  ArrowLeftRight,
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  BadgePercent,
  BarChart3,
  Bell,
  BellRing,
  Boxes,
  Building2,
  CalendarDays,
  ChartNoAxesCombined,
  Circle,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  ClipboardList,
  CreditCard,
  Download,
  Ellipsis,
  Info,
  KeyRound,
  Laptop,
  LayoutDashboard,
  ListFilter,
  Lock,
  LockKeyhole,
  LockOpen,
  LogIn,
  LogOut,
  Megaphone,
  Menu,
  Minus,
  Monitor,
  Package,
  PackageCheck,
  PackageSearch,
  PackageX,
  Pencil,
  Plus,
  ReceiptText,
  ScrollText,
  Search,
  Settings,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  ShoppingBag,
  ShoppingBasket,
  ShoppingCart,
  Sparkles,
  Trash2,
  TrendingUp,
  TriangleAlert,
  UserCog,
  UserPlus,
  UserRound,
  UsersRound,
  WalletCards,
  Warehouse,
  X,
} from "lucide-react";
import {
  customers,
  employees,
  menus,
  monthlyRevenue,
  orders,
  permissionsByPortal,
  portalConfig,
  products,
  promotions,
} from "./data";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const LOGIN_API_URL = `${API_BASE_URL}/login`;
const REGISTER_API_URL = `${API_BASE_URL}/register`;

const formatMoney = (value) => `${new Intl.NumberFormat("vi-VN").format(value)} ₫`;

const iconMap = {
  ArrowLeftRight, ArrowRight, ArrowUpRight, BadgeCheck, BadgePercent, BarChart3,
  Bell, BellRing, Boxes, Building2, CalendarDays, ChartNoAxesCombined, Circle,
  CircleAlert, CircleCheck, CircleHelp, ClipboardList, CreditCard, Download,
  Ellipsis, Info, KeyRound, Laptop, LayoutDashboard, ListFilter, Lock,
  LockKeyhole, LockOpen, LogIn, LogOut, Megaphone, Menu, Minus, Monitor,
  Package, PackageCheck, PackageSearch, PackageX, Pencil, Plus, ReceiptText,
  ScrollText, Search, Settings, ShieldAlert, ShieldCheck, ShieldX, ShoppingBag,
  ShoppingBasket, ShoppingCart, Sparkles, Trash2, TrendingUp, TriangleAlert,
  UserCog, UserPlus, UserRound, UsersRound, WalletCards, Warehouse, X,
};

function Icon({ name, size = 20, strokeWidth = 1.9 }) {
  const Component = iconMap[name] || Circle;
  return <Component size={size} strokeWidth={strokeWidth} aria-hidden="true" />;
}

function apiErrorMessage(data, fallback) {
  const detail = data?.message ?? data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item?.msg).filter(Boolean).join("; ") || fallback;
  return fallback;
}

function portalFromRole(roleId) {
  const normalizedRole = String(roleId || "").trim().toLowerCase();
  return Object.entries(portalConfig).find(([, config]) =>
    config.roles.some((role) => role.toLowerCase() === normalizedRole),
  )?.[0] || null;
}

function LoginScreen({ onAuthenticated }) {
  const [portal, setPortal] = useState("employee");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [registerOpen, setRegisterOpen] = useState(false);
  const selectedPortal = portalConfig[portal];

  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");

    if (!username.trim() || !password) {
      setError("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(LOGIN_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await response.json().catch(() => null);

      if (!response.ok || !data?.success || !data?.user) {
        setError(apiErrorMessage(data, "Tên đăng nhập hoặc mật khẩu không chính xác."));
        return;
      }

      const accountPortal = portalFromRole(data.user.RoleID);
      if (!accountPortal) {
        setError(`Vai trò “${data.user.RoleID || "chưa xác định"}” chưa được cấu hình trong hệ thống.`);
        return;
      }

      if (accountPortal !== portal) {
        setError(
          `Tài khoản này thuộc khu vực ${portalConfig[accountPortal].label}. ` +
          `Hãy chọn đúng loại tài khoản để đăng nhập.`,
        );
        return;
      }

      onAuthenticated(data.user, accountPortal);
    } catch {
      setError("Không thể kết nối FastAPI tại cổng 8000. Hãy kiểm tra backend và cấu hình VITE_API_URL.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-orb auth-orb-one" />
      <div className="auth-orb auth-orb-two" />

      <section className="auth-shell">
        <div className="auth-story">
          <div className="auth-brand">
            <LogoMark />
            <div>
              <strong>DX-LAB CORE</strong>
              <span>Digital Commerce Workspace</span>
            </div>
          </div>

          <div className="story-content">
            <span className="story-kicker">MỘT HỆ THỐNG · ĐÚNG QUYỀN HẠN</span>
            <h1>Không gian làm việc rõ ràng cho từng vai trò.</h1>
            <p>
              Nhân viên tập trung bán hàng. Quản trị viên kiểm soát dữ liệu,
              vận hành và doanh thu trên một nền tảng thống nhất.
            </p>
            <div className="story-preview">
              <div className="preview-head">
                <span><i /> Tổng quan vận hành</span>
                <small>Tháng 09/2026</small>
              </div>
              <div className="preview-grid">
                <div><Icon name="TrendingUp" /><span>Doanh thu</span><b>486,2 triệu</b></div>
                <div><Icon name="ShoppingBag" /><span>Đơn hàng</span><b>128 đơn</b></div>
              </div>
              <div className="preview-chart">
                {[36, 52, 44, 67, 61, 82, 76, 94].map((height, index) => (
                  <i key={index} style={{ height: `${height}%` }} />
                ))}
              </div>
            </div>
          </div>

          <div className="story-trust">
            <span><Icon name="ShieldCheck" size={17} /> Phân quyền theo SQL Server</span>
            <span><Icon name="LockKeyhole" size={17} /> Mật khẩu được mã hóa</span>
          </div>
        </div>

        <div className="auth-panel">
          <div className="auth-form-wrap">
            <div className="auth-heading">
              <span className="mobile-brand"><LogoMark /> DX-LAB CORE</span>
              <p className="eyebrow">CỔNG ĐĂNG NHẬP</p>
              <h2>Chào mừng trở lại</h2>
              <p>Chọn khu vực làm việc, sau đó đăng nhập bằng tài khoản được cấp.</p>
            </div>

            <div className="portal-picker" role="radiogroup" aria-label="Loại tài khoản">
              {Object.entries(portalConfig).map(([key, config]) => (
                <button
                  type="button"
                  role="radio"
                  aria-checked={portal === key}
                  className={`portal-option ${portal === key ? "selected" : ""}`}
                  key={key}
                  onClick={() => { setPortal(key); setError(""); }}
                >
                  <span className="portal-icon"><Icon name={config.icon} /></span>
                  <span><b>{config.label}</b><small>{config.shortLabel}</small></span>
                  <i className="radio-dot" />
                </button>
              ))}
            </div>

            <div className={`portal-note ${portal}`}>
              <Icon name={selectedPortal.icon} size={18} />
              <span>{selectedPortal.description}</span>
            </div>

            <form className="auth-form" onSubmit={handleLogin}>
              {error && <div className="form-alert" role="alert"><Icon name="CircleAlert" size={18} /><span>{error}</span></div>}

              <label className="input-group">
                <span>Tên đăng nhập</span>
                <div className="input-shell">
                  <Icon name="UserRound" size={19} />
                  <input
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="Nhập tên đăng nhập"
                    autoComplete="username"
                  />
                </div>
              </label>

              <label className="input-group">
                <span>Mật khẩu</span>
                <div className="input-shell">
                  <Icon name="LockKeyhole" size={19} />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Nhập mật khẩu"
                    autoComplete="current-password"
                  />
                  <button type="button" className="input-action" onClick={() => setShowPassword((current) => !current)} aria-label="Hiện hoặc ẩn mật khẩu">
                    <Icon name={showPassword ? "EyeOff" : "Eye"} size={18} />
                  </button>
                </div>
              </label>

              <div className="auth-options">
                <label><input type="checkbox" /> Ghi nhớ đăng nhập</label>
                <button type="button">Quên mật khẩu?</button>
              </div>

              <button className="login-button" type="submit" disabled={loading}>
                {loading ? <span className="spinner" /> : <Icon name="LogIn" size={19} />}
                {loading ? "Đang xác thực..." : `Đăng nhập với tư cách ${selectedPortal.label}`}
              </button>
            </form>

            {portal === "employee" ? (
              <div className="register-link">
                Chưa có tài khoản nhân viên?
                <button type="button" onClick={() => setRegisterOpen(true)}>Tạo tài khoản</button>
              </div>
            ) : (
              <div className="admin-account-note">
                <Icon name="ShieldCheck" size={16} />
                <span>Tài khoản quản trị phải được hệ thống cấp, không tạo từ form đăng ký công khai.</span>
              </div>
            )}

            <div className="security-caption">
              <Icon name="Info" size={15} />
              Lựa chọn ở trên không cấp quyền. Hệ thống vẫn kiểm tra vai trò thật trong SQL Server.
            </div>
          </div>
        </div>
      </section>

      {registerOpen && <RegisterModal onClose={() => setRegisterOpen(false)} onUseUsername={(value) => { setUsername(value); setPortal("employee"); setRegisterOpen(false); }} />}
    </main>
  );
}

function RegisterModal({ onClose, onUseUsername }) {
  const [form, setForm] = useState({ fullName: "", username: "", password: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    const fullName = form.fullName.trim();
    const username = form.username.trim();

    if (!fullName || !username || !form.password || !form.confirmPassword) {
      setError("Vui lòng nhập đầy đủ thông tin.");
      return;
    }
    if (!/^[A-Za-z0-9._-]{3,50}$/.test(username)) {
      setError("Tên đăng nhập phải có 3–50 ký tự: chữ không dấu, số, dấu chấm, gạch dưới hoặc gạch ngang.");
      return;
    }
    if (form.password.length < 8) {
      setError("Mật khẩu phải có ít nhất 8 ký tự.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(REGISTER_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, username, password: form.password }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok || !data?.success) {
        setError(apiErrorMessage(data, "Không thể tạo tài khoản."));
        return;
      }
      setSuccess(true);
    } catch {
      setError("Không thể kết nối FastAPI tại cổng 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Tạo tài khoản nhân viên" onClose={onClose} narrow>
      {success ? (
        <div className="success-state">
          <span><Icon name="BadgeCheck" size={34} /></span>
          <h3>Tạo tài khoản thành công</h3>
          <p>Tài khoản <b>{form.username.trim()}</b> đã được lưu với vai trò <b>Sales</b>.</p>
          <button className="primary-button" onClick={() => onUseUsername(form.username.trim())}>Đăng nhập ngay</button>
        </div>
      ) : (
        <form onSubmit={submit}>
          <div className="register-policy"><Icon name="ShieldCheck" size={19} /><span>Tài khoản đăng ký công khai luôn là nhân viên. Admin chỉ có thể được cấp bởi quản trị viên.</span></div>
          <div className="form-grid">
            <label className="input-group full-span"><span>Họ và tên</span><input value={form.fullName} onChange={(event) => update("fullName", event.target.value)} placeholder="Nguyễn Văn A" maxLength={100} /></label>
            <label className="input-group full-span"><span>Tên đăng nhập</span><input value={form.username} onChange={(event) => update("username", event.target.value)} placeholder="nguyenvana" maxLength={50} autoComplete="username" /></label>
            <label className="input-group"><span>Mật khẩu</span><input type="password" value={form.password} onChange={(event) => update("password", event.target.value)} placeholder="Tối thiểu 8 ký tự" autoComplete="new-password" /></label>
            <label className="input-group"><span>Xác nhận mật khẩu</span><input type="password" value={form.confirmPassword} onChange={(event) => update("confirmPassword", event.target.value)} placeholder="Nhập lại mật khẩu" autoComplete="new-password" /></label>
          </div>
          {error && <div className="form-alert compact" role="alert"><Icon name="CircleAlert" size={17} />{error}</div>}
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={onClose}>Hủy</button>
            <button type="submit" className="primary-button" disabled={loading}>{loading ? "Đang tạo..." : "Tạo tài khoản"}</button>
          </div>
        </form>
      )}
    </Modal>
  );
}

function LogoMark() {
  return <span className="logo-mark"><span>DX</span></span>;
}

function Workspace({ user, portal, onLogout }) {
  const config = portalConfig[portal];
  const allowedMenu = menus[portal].filter((item) => permissionsByPortal[portal].has(item.permission));
  const [page, setPage] = useState(config.landingPage);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState("");

  const showToast = (message) => {
    setToast(message);
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => setToast(""), 2800);
  };

  const currentItem = allowedMenu.find((item) => item.id === page) || allowedMenu[0];
  const navigate = (nextPage) => {
    const target = allowedMenu.find((item) => item.id === nextPage);
    if (!target || !permissionsByPortal[portal].has(target.permission)) {
      showToast("Bạn không có quyền truy cập khu vực này.");
      return;
    }
    setPage(nextPage);
    setSidebarOpen(false);
  };

  return (
    <div className={`workspace-app portal-${portal}`}>
      <Sidebar portal={portal} menu={allowedMenu} page={page} onNavigate={navigate} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="workspace-main">
        <Header user={user} portal={portal} pageLabel={currentItem?.label} onLogout={onLogout} onOpenMenu={() => setSidebarOpen(true)} />
        <div className="workspace-content">
          <PageRouter page={page} portal={portal} user={user} onNavigate={navigate} showToast={showToast} />
        </div>
      </div>
      {toast && <div className="toast"><Icon name="CircleCheck" size={19} />{toast}</div>}
    </div>
  );
}

function Sidebar({ portal, menu, page, onNavigate, open, onClose }) {
  const config = portalConfig[portal];
  return (
    <>
      <button className={`sidebar-backdrop ${open ? "show" : ""}`} onClick={onClose} aria-label="Đóng menu" />
      <aside className={`workspace-sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-brand"><LogoMark /><div><strong>DX-LAB CORE</strong><span>Commerce Workspace</span></div></div>
        <div className={`portal-badge ${portal}`}><Icon name={config.icon} size={18} /><div><span>KHÔNG GIAN</span><b>{config.shortLabel}</b></div></div>
        <nav className="sidebar-nav">
          <span className="nav-caption">ĐIỀU HƯỚNG</span>
          {menu.map((item) => (
            <button key={item.id} className={page === item.id ? "active" : ""} onClick={() => onNavigate(item.id)}>
              <Icon name={item.icon} size={19} /><span>{item.label}</span>{page === item.id && <i />}
            </button>
          ))}
        </nav>
        <div className="sidebar-security"><Icon name="ShieldCheck" size={18} /><div><b>Quyền hạn được bảo vệ</b><span>{portal === "admin" ? "Toàn quyền quản trị" : "Không có quyền sửa hoặc xóa"}</span></div></div>
      </aside>
    </>
  );
}

function Header({ user, portal, pageLabel, onLogout, onOpenMenu }) {
  const fullName = user?.FullName || user?.Username || "Người dùng";
  const initials = fullName.split(/\s+/).filter(Boolean).slice(-2).map((word) => word[0]).join("").toUpperCase();
  return (
    <header className="workspace-header">
      <div className="header-title">
        <button className="mobile-menu" onClick={onOpenMenu}><Icon name="Menu" /></button>
        <div><span>DX-Lab Core / {portalConfig[portal].label}</span><h1>{pageLabel}</h1></div>
      </div>
      <div className="header-actions">
        <button className="header-icon" aria-label="Tìm kiếm"><Icon name="Search" size={19} /></button>
        <button className="header-icon notification" aria-label="Thông báo"><Icon name="Bell" size={19} /><i /></button>
        <div className="profile"><span className="profile-avatar">{initials || "DX"}</span><div><b>{fullName}</b><span>{user?.RoleID || portalConfig[portal].label}</span></div><button onClick={onLogout} title="Đăng xuất"><Icon name="LogOut" size={18} /></button></div>
      </div>
    </header>
  );
}

function PageRouter({ page, portal, user, onNavigate, showToast }) {
  const allowed = menus[portal].find((item) => item.id === page);
  if (!allowed || !permissionsByPortal[portal].has(allowed.permission)) return <AccessDenied />;

  if (portal === "employee") {
    if (page === "pos") return <PointOfSale user={user} showToast={showToast} />;
    if (page === "catalog") return <CatalogPage />;
    if (page === "promotions") return <PromotionsPage />;
    if (page === "my-orders") return <OrdersPage employee user={user} />;
    if (page === "customers") return <CustomersPage canWrite={false} showToast={showToast} />;
  }

  if (page === "overview") return <AdminOverview onNavigate={onNavigate} />;
  if (page === "revenue") return <RevenuePage />;
  if (page === "orders") return <OrdersPage showToast={showToast} />;
  if (page === "products") return <ProductsPage showToast={showToast} />;
  if (page === "customers") return <CustomersPage canWrite showToast={showToast} />;
  if (page === "inventory") return <InventoryPage showToast={showToast} />;
  if (page === "users") return <UsersPage showToast={showToast} />;
  if (page === "settings") return <SettingsPage showToast={showToast} />;
  return <AccessDenied />;
}

function PageHeading({ eyebrow, title, description, children }) {
  return <div className="page-heading"><div><span>{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>{children && <div className="page-actions">{children}</div>}</div>;
}

function AdminOverview({ onNavigate }) {
  const lowStock = products.filter((product) => product.stock <= product.reorder);
  return (
    <div className="page-stack">
      <PageHeading eyebrow="QUẢN TRỊ VIÊN" title="Tổng quan kinh doanh" description="Theo dõi doanh thu, đơn hàng và các vấn đề cần xử lý trong tháng 9.">
        <button className="secondary-button"><Icon name="CalendarDays" size={17} /> Tháng 09/2026</button>
        <button className="primary-button" onClick={() => onNavigate("revenue")}><Icon name="BarChart3" size={17} /> Xem báo cáo</button>
      </PageHeading>
      <div className="metric-grid">
        <MetricCard icon="WalletCards" label="Doanh thu tháng" value="486,2 triệu ₫" change="+12,8% so với tháng 8" tone="blue" />
        <MetricCard icon="ShoppingBag" label="Đơn đã bán" value="128" change="18 đơn trong hôm nay" tone="violet" />
        <MetricCard icon="UsersRound" label="Khách hàng" value="1.284" change="+32 khách hàng mới" tone="green" />
        <MetricCard icon="TriangleAlert" label="Cảnh báo tồn kho" value={String(lowStock.length)} change="Cần bổ sung sớm" tone="orange" />
      </div>
      <div className="dashboard-grid">
        <Panel title="Xu hướng doanh thu" subtitle="6 tháng gần nhất" action="Chi tiết" onAction={() => onNavigate("revenue")}>
          <RevenueBars compact />
        </Panel>
        <Panel title="Sản phẩm bán chạy" subtitle="Theo số lượng tháng này">
          <div className="top-products">
            {[...products].sort((a, b) => b.sold - a.sold).slice(0, 4).map((product, index) => (
              <div key={product.id}><span className="rank">{index + 1}</span><span className="product-avatar"><Icon name="Package" size={18} /></span><div><b>{product.name}</b><small>{product.category}</small></div><strong>{product.sold} đã bán</strong></div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel title="Đơn hàng gần đây" subtitle="Cập nhật theo dữ liệu bán hàng" action="Xem tất cả" onAction={() => onNavigate("orders")}>
        <OrdersTable data={orders.slice(0, 4)} />
      </Panel>
    </div>
  );
}

function MetricCard({ icon, label, value, change, tone }) {
  return <article className="metric-card"><span className={`metric-icon ${tone}`}><Icon name={icon} /></span><div><span>{label}</span><strong>{value}</strong><small><Icon name="ArrowUpRight" size={13} />{change}</small></div></article>;
}

function RevenueBars({ compact = false }) {
  const max = Math.max(...monthlyRevenue.map((item) => item.value));
  return <div className={`revenue-bars ${compact ? "compact" : ""}`}><div className="bar-grid"><span>500M</span><span>375M</span><span>250M</span><span>125M</span><span>0</span></div><div className="bars">{monthlyRevenue.map((item) => <div className="bar-column" key={item.month}><div className="bar-tooltip">{item.value}M</div><i style={{ height: `${(item.value / max) * 100}%` }} className={item.month === "T9" ? "current" : ""} /><span>{item.month}</span></div>)}</div></div>;
}

function RevenuePage() {
  return (
    <div className="page-stack">
      <PageHeading eyebrow="BÁO CÁO QUẢN TRỊ" title="Doanh thu tháng 09/2026" description="Dữ liệu tài chính chỉ hiển thị cho tài khoản quản trị.">
        <button className="secondary-button"><Icon name="Download" size={17} /> Xuất báo cáo</button>
      </PageHeading>
      <div className="financial-banner">
        <div><span>TỔNG DOANH THU</span><strong>486.200.000 ₫</strong><small><Icon name="TrendingUp" size={16} /> Tăng 12,8% so với tháng trước</small></div>
        <div className="financial-split"><div><span>Giá vốn ước tính</span><b>291,7 triệu ₫</b></div><div><span>Lợi nhuận gộp</span><b>194,5 triệu ₫</b></div><div><span>Biên lợi nhuận</span><b>40,0%</b></div></div>
      </div>
      <Panel title="Doanh thu theo tháng" subtitle="Đơn vị: triệu đồng"><RevenueBars /></Panel>
      <div className="dashboard-grid revenue-detail">
        <Panel title="Theo nhóm sản phẩm"><BreakdownRow label="Laptop & Máy tính" value="214,8 triệu" percent={44} /><BreakdownRow label="Màn hình" value="112,4 triệu" percent={23} /><BreakdownRow label="Phụ kiện" value="96,1 triệu" percent={20} /><BreakdownRow label="Khác" value="62,9 triệu" percent={13} /></Panel>
        <Panel title="Chỉ số bán hàng"><div className="report-list"><div><span>Giá trị đơn trung bình</span><b>3.798.000 ₫</b></div><div><span>Tỷ lệ hoàn thành</span><b>92,4%</b></div><div><span>Đơn chờ duyệt</span><b>4 đơn</b></div><div><span>Hoàn / hủy</span><b>3 đơn</b></div></div></Panel>
      </div>
    </div>
  );
}

function BreakdownRow({ label, value, percent }) {
  return <div className="breakdown-row"><div><span>{label}</span><b>{value}</b></div><div className="progress"><i style={{ width: `${percent}%` }} /></div><small>{percent}%</small></div>;
}

function PointOfSale({ user, showToast }) {
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState([]);
  const [customer, setCustomer] = useState("Khách lẻ");
  const visibleProducts = products.filter((product) => `${product.name} ${product.category}`.toLowerCase().includes(query.toLowerCase()));
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const addToCart = (product) => setCart((current) => {
    const existing = current.find((item) => item.id === product.id);
    if (existing) return current.map((item) => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
    return [...current, { ...product, quantity: 1 }];
  });
  const changeQuantity = (id, change) => setCart((current) => current.map((item) => item.id === id ? { ...item, quantity: item.quantity + change } : item).filter((item) => item.quantity > 0));
  const checkout = () => {
    if (!cart.length) return;
    showToast(`Đã tạo đơn bán hàng ${formatMoney(total)} cho ${customer}.`);
    setCart([]);
  };

  return (
    <div className="page-stack">
      <PageHeading eyebrow="KHU VỰC NHÂN VIÊN" title={`Chào ${user?.FullName || user?.Username || "bạn"}, bắt đầu bán hàng`} description="Chọn sản phẩm, xác nhận khách hàng và hoàn tất đơn ngay tại quầy." />
      <div className="pos-layout">
        <section className="pos-products">
          <div className="pos-toolbar"><div className="search-box"><Icon name="Search" size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm sản phẩm hoặc danh mục..." /></div><span>{visibleProducts.length} sản phẩm</span></div>
          <div className="product-grid">
            {visibleProducts.map((product) => (
              <article className="product-card" key={product.id}>
                <div className="product-visual"><Icon name={product.category === "Laptop" ? "Laptop" : product.category === "Màn hình" ? "Monitor" : "Package"} size={34} /><span className={product.stock <= product.reorder ? "low" : ""}>{product.stock} còn lại</span></div>
                <small>{product.id} · {product.category}</small><h3>{product.name}</h3><div><strong>{formatMoney(product.price)}</strong><button onClick={() => addToCart(product)} aria-label={`Thêm ${product.name}`}><Icon name="Plus" size={19} /></button></div>
              </article>
            ))}
          </div>
        </section>
        <aside className="cart-panel">
          <div className="cart-head"><div><span>ĐƠN HÀNG HIỆN TẠI</span><h3>Giỏ hàng</h3></div><b>{cart.reduce((sum, item) => sum + item.quantity, 0)}</b></div>
          <label className="cart-customer"><span>Khách hàng</span><select value={customer} onChange={(event) => setCustomer(event.target.value)}><option>Khách lẻ</option>{customers.map((item) => <option key={item.id}>{item.name}</option>)}</select></label>
          <div className="cart-items">
            {!cart.length && <div className="empty-cart"><Icon name="ShoppingBasket" size={34} /><b>Giỏ hàng đang trống</b><span>Chọn sản phẩm để bắt đầu bán hàng.</span></div>}
            {cart.map((item) => <div className="cart-item" key={item.id}><div><b>{item.name}</b><span>{formatMoney(item.price)}</span></div><div className="quantity"><button onClick={() => changeQuantity(item.id, -1)}><Icon name="Minus" size={14} /></button><span>{item.quantity}</span><button onClick={() => changeQuantity(item.id, 1)}><Icon name="Plus" size={14} /></button></div></div>)}
          </div>
          <div className="cart-summary"><div><span>Tạm tính</span><b>{formatMoney(total)}</b></div><div><span>Giảm giá</span><b>0 ₫</b></div><div className="cart-total"><span>Tổng thanh toán</span><strong>{formatMoney(total)}</strong></div><button className="checkout-button" disabled={!cart.length} onClick={checkout}><Icon name="CreditCard" size={19} /> Thanh toán</button><small><Icon name="ShieldCheck" size={14} /> Nhân viên chỉ được tạo đơn, không thể sửa giá sản phẩm.</small></div>
        </aside>
      </div>
    </div>
  );
}

function CatalogPage() {
  const [query, setQuery] = useState("");
  const filtered = products.filter((product) => JSON.stringify(product).toLowerCase().includes(query.toLowerCase()));
  return <div className="page-stack"><PageHeading eyebrow="TRA CỨU" title="Danh mục sản phẩm" description="Nhân viên được xem giá và tồn kho nhưng không thể thêm, sửa hoặc xóa sản phẩm." /><TableToolbar query={query} onQuery={setQuery} placeholder="Tìm sản phẩm..." count={filtered.length} /><div className="table-card"><table><thead><tr><th>Mã</th><th>Sản phẩm</th><th>Danh mục</th><th>Giá bán</th><th>Tồn kho</th><th>Trạng thái</th></tr></thead><tbody>{filtered.map((product) => <tr key={product.id}><td><b>{product.id}</b></td><td>{product.name}</td><td>{product.category}</td><td><b>{formatMoney(product.price)}</b></td><td>{product.stock}</td><td><StatusBadge value={product.status} /></td></tr>)}</tbody></table></div></div>;
}

function PromotionsPage() {
  return <div className="page-stack"><PageHeading eyebrow="HỖ TRỢ BÁN HÀNG" title="Chương trình khuyến mãi" description="Các chương trình đang áp dụng để nhân viên tư vấn cho khách hàng." /><div className="promotion-grid">{promotions.map((promotion) => <article className={`promotion-card ${promotion.color}`} key={promotion.id}><div><span>{promotion.tag}</span><Icon name="Sparkles" /></div><small>{promotion.expires}</small><h3>{promotion.title}</h3><p>{promotion.description}</p><button>Tư vấn ngay <Icon name="ArrowRight" size={16} /></button></article>)}</div><div className="information-card"><Icon name="CircleHelp" /><div><b>Nhân viên cần lưu ý</b><p>Khuyến mãi chỉ được áp dụng theo điều kiện hệ thống. Mọi thay đổi chương trình phải do Admin thực hiện.</p></div></div></div>;
}

function OrdersPage({ employee = false, user, showToast }) {
  const visibleOrders = employee ? orders.filter((order) => order.seller.toLowerCase().includes((user?.FullName || "Hoàn").split(" ").slice(-1)[0].toLowerCase())).slice(0, 4) : orders;
  return <div className="page-stack"><PageHeading eyebrow={employee ? "CÁ NHÂN" : "QUẢN TRỊ ĐƠN HÀNG"} title={employee ? "Đơn hàng của tôi" : "Tất cả đơn hàng"} description={employee ? "Chỉ hiển thị các đơn do tài khoản hiện tại tạo." : "Theo dõi và xử lý toàn bộ đơn hàng trong hệ thống."}>{!employee && <button className="primary-button" onClick={() => showToast?.("Chức năng tạo đơn quản trị sẽ kết nối API ở bước sau.")}><Icon name="Plus" size={17} /> Tạo đơn</button>}</PageHeading><div className="order-summary"><div><span>Hôm nay</span><b>18 đơn</b></div><div><span>Hoàn thành</span><b>14 đơn</b></div><div><span>Đang xử lý</span><b>3 đơn</b></div><div><span>Chờ duyệt</span><b>1 đơn</b></div></div><Panel title={employee ? "Lịch sử bán hàng" : "Danh sách đơn hàng"}>{visibleOrders.length ? <OrdersTable data={visibleOrders} showSeller={!employee} admin={!employee} /> : <div className="empty-table"><Icon name="ReceiptText" size={28} /><b>Chưa có đơn hàng</b><span>Tài khoản này chưa tạo đơn nào.</span></div>}</Panel></div>;
}

function OrdersTable({ data, showSeller = true, admin = false }) {
  return <div className="table-scroll"><table><thead><tr><th>Mã đơn</th><th>Khách hàng</th>{showSeller && <th>Nhân viên</th>}<th>Giá trị</th><th>Trạng thái</th><th>Ngày</th>{admin && <th />}</tr></thead><tbody>{data.map((order) => <tr key={order.id}><td><b>{order.id}</b></td><td>{order.customer}</td>{showSeller && <td>{order.seller}</td>}<td><b>{formatMoney(order.value)}</b></td><td><StatusBadge value={order.status} /></td><td>{order.date}</td>{admin && <td><button className="row-action"><Icon name="Ellipsis" size={18} /></button></td>}</tr>)}</tbody></table></div>;
}

function ProductsPage({ showToast }) {
  const [items, setItems] = useState(products);
  const [query, setQuery] = useState("");
  const filtered = items.filter((product) => JSON.stringify(product).toLowerCase().includes(query.toLowerCase()));
  const remove = (id) => { setItems((current) => current.filter((item) => item.id !== id)); showToast("Đã xóa sản phẩm trong dữ liệu giao diện mẫu."); };
  return <div className="page-stack"><PageHeading eyebrow="QUẢN LÝ DANH MỤC" title="Sản phẩm" description="Admin có thể thêm, sửa và xóa sản phẩm."><button className="primary-button" onClick={() => showToast("Biểu mẫu thêm sản phẩm sẽ kết nối API ở bước backend.")}><Icon name="Plus" size={17} /> Thêm sản phẩm</button></PageHeading><TableToolbar query={query} onQuery={setQuery} placeholder="Tìm sản phẩm..." count={filtered.length} /><div className="table-card"><table><thead><tr><th>Mã</th><th>Sản phẩm</th><th>Giá bán</th><th>Tồn kho</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{filtered.map((product) => <tr key={product.id}><td><b>{product.id}</b></td><td><div className="table-primary"><span><Icon name="Package" size={17} /></span><div><b>{product.name}</b><small>{product.category}</small></div></div></td><td><b>{formatMoney(product.price)}</b></td><td>{product.stock}</td><td><StatusBadge value={product.status} /></td><td><div className="row-actions"><button onClick={() => showToast(`Mở biểu mẫu sửa ${product.name}.`)} title="Sửa"><Icon name="Pencil" size={16} /></button><button className="delete" onClick={() => remove(product.id)} title="Xóa"><Icon name="Trash2" size={16} /></button></div></td></tr>)}</tbody></table></div></div>;
}

function CustomersPage({ canWrite, showToast }) {
  const [items, setItems] = useState(customers);
  const [query, setQuery] = useState("");
  const filtered = items.filter((customer) => JSON.stringify(customer).toLowerCase().includes(query.toLowerCase()));
  return <div className="page-stack"><PageHeading eyebrow={canWrite ? "QUẢN LÝ DỮ LIỆU" : "TRA CỨU"} title="Khách hàng" description={canWrite ? "Thêm, cập nhật và quản lý hồ sơ khách hàng." : "Tra cứu thông tin phục vụ bán hàng; không có quyền sửa dữ liệu."}>{canWrite && <button className="primary-button" onClick={() => showToast("Biểu mẫu khách hàng sẽ kết nối API ở bước backend.")}><Icon name="UserPlus" size={17} /> Thêm khách hàng</button>}</PageHeading><TableToolbar query={query} onQuery={setQuery} placeholder="Tìm khách hàng..." count={filtered.length} /><div className="table-card"><table><thead><tr><th>Mã</th><th>Khách hàng</th><th>Người liên hệ</th><th>Điện thoại</th><th>Hạng</th><th>Trạng thái</th>{canWrite && <th>Thao tác</th>}</tr></thead><tbody>{filtered.map((customer) => <tr key={customer.id}><td><b>{customer.id}</b></td><td>{customer.name}</td><td>{customer.contact}</td><td>{customer.phone}</td><td><span className="tier-badge">{customer.tier}</span></td><td><StatusBadge value={customer.status} /></td>{canWrite && <td><div className="row-actions"><button onClick={() => showToast(`Mở hồ sơ ${customer.name}.`)}><Icon name="Pencil" size={16} /></button><button className="delete" onClick={() => { setItems((current) => current.filter((item) => item.id !== customer.id)); showToast("Đã xóa khách hàng trong dữ liệu giao diện mẫu."); }}><Icon name="Trash2" size={16} /></button></div></td>}</tr>)}</tbody></table></div></div>;
}

function InventoryPage({ showToast }) {
  return <div className="page-stack"><PageHeading eyebrow="VẬN HÀNH KHO" title="Quản lý tồn kho" description="Admin theo dõi số lượng và thực hiện điều chỉnh kho."><button className="primary-button" onClick={() => showToast("Phiếu điều chỉnh kho sẽ kết nối API ở bước backend.")}><Icon name="ArrowLeftRight" size={17} /> Điều chỉnh kho</button></PageHeading><div className="metric-grid compact-metrics"><MetricCard icon="Boxes" label="Tổng mặt hàng" value="216" change="6 nhóm sản phẩm" tone="blue" /><MetricCard icon="PackageCheck" label="Đủ hàng" value="198" change="91,7% danh mục" tone="green" /><MetricCard icon="TriangleAlert" label="Sắp hết" value="16" change="Cần tạo yêu cầu mua" tone="orange" /><MetricCard icon="PackageX" label="Hết hàng" value="2" change="Cần xử lý ngay" tone="violet" /></div><Panel title="Cảnh báo tồn kho" subtitle="Sản phẩm dưới mức nhập lại"><div className="stock-list">{products.filter((product) => product.stock <= product.reorder).map((product) => <div key={product.id}><span className="stock-icon"><Icon name="TriangleAlert" size={18} /></span><div><b>{product.name}</b><small>{product.id} · Mức nhập lại {product.reorder}</small></div><strong>{product.stock} còn lại</strong><button onClick={() => showToast(`Đã tạo yêu cầu nhập ${product.name} ở giao diện mẫu.`)}>Tạo yêu cầu</button></div>)}</div></Panel></div>;
}

function UsersPage({ showToast }) {
  const [items, setItems] = useState(employees);
  return <div className="page-stack"><PageHeading eyebrow="QUẢN TRỊ HỆ THỐNG" title="Tài khoản và vai trò" description="Chỉ Admin được tạo tài khoản quản trị, đổi vai trò hoặc khóa người dùng."><button className="primary-button" onClick={() => showToast("Biểu mẫu cấp tài khoản sẽ kết nối API quản trị.")}><Icon name="UserPlus" size={17} /> Cấp tài khoản</button></PageHeading><div className="permission-callout"><Icon name="ShieldAlert" /><div><b>Nguyên tắc phân quyền</b><p>Frontend chỉ ẩn chức năng để cải thiện trải nghiệm. Backend vẫn phải kiểm tra JWT, trạng thái tài khoản và quyền trên mọi API ghi dữ liệu.</p></div></div><div className="table-card"><table><thead><tr><th>Người dùng</th><th>Tên đăng nhập</th><th>Vai trò</th><th>Trạng thái</th><th>Đăng nhập gần nhất</th><th>Thao tác</th></tr></thead><tbody>{items.map((employee) => <tr key={employee.id}><td><div className="table-primary"><span className="person-avatar">{employee.name.split(" ").slice(-1)[0][0]}</span><b>{employee.name}</b></div></td><td>{employee.username}</td><td><RoleBadge role={employee.role} /></td><td><StatusBadge value={employee.status} /></td><td>{employee.lastLogin}</td><td><div className="row-actions"><button onClick={() => showToast(`Mở phân quyền của ${employee.name}.`)}><Icon name="KeyRound" size={16} /></button><button onClick={() => { setItems((current) => current.map((item) => item.id === employee.id ? { ...item, status: item.status === "Active" ? "Locked" : "Active" } : item)); showToast("Đã thay đổi trạng thái trong giao diện mẫu."); }}><Icon name={employee.status === "Active" ? "Lock" : "LockOpen"} size={16} /></button></div></td></tr>)}</tbody></table></div></div>;
}

function SettingsPage({ showToast }) {
  return <div className="page-stack"><PageHeading eyebrow="CẤU HÌNH" title="Cài đặt hệ thống" description="Thiết lập chung dành riêng cho quản trị viên." /><div className="settings-grid"><SettingCard icon="Building2" title="Thông tin doanh nghiệp" description="Tên đơn vị, địa chỉ, mã số thuế và nhận diện." action="Cấu hình" onClick={() => showToast("Mở cấu hình doanh nghiệp.")} /><SettingCard icon="BadgePercent" title="Khuyến mãi" description="Tạo và điều chỉnh chương trình bán hàng." action="Quản lý" onClick={() => showToast("Mở quản lý khuyến mãi.")} /><SettingCard icon="BellRing" title="Thông báo" description="Cảnh báo tồn kho, đơn hàng và phê duyệt." action="Thiết lập" onClick={() => showToast("Mở thiết lập thông báo.")} /><SettingCard icon="ScrollText" title="Nhật ký hoạt động" description="Theo dõi thao tác nhạy cảm của người dùng." action="Xem nhật ký" onClick={() => showToast("Audit log sẽ được làm ở bước RBAC backend.")} /></div></div>;
}

function SettingCard({ icon, title, description, action, onClick }) {
  return <article className="setting-card"><span><Icon name={icon} /></span><div><h3>{title}</h3><p>{description}</p><button onClick={onClick}>{action} <Icon name="ArrowRight" size={15} /></button></div></article>;
}

function TableToolbar({ query, onQuery, placeholder, count }) {
  return <div className="table-toolbar"><div className="search-box"><Icon name="Search" size={18} /><input value={query} onChange={(event) => onQuery(event.target.value)} placeholder={placeholder} /></div><button className="secondary-button"><Icon name="ListFilter" size={17} /> Bộ lọc</button><span>{count} bản ghi</span></div>;
}

function Panel({ title, subtitle, action, onAction, children }) {
  return <section className="panel-card"><div className="panel-heading"><div><h3>{title}</h3>{subtitle && <span>{subtitle}</span>}</div>{action && <button onClick={onAction}>{action}<Icon name="ArrowUpRight" size={15} /></button>}</div>{children}</section>;
}

function StatusBadge({ value }) {
  const normalized = String(value).toLowerCase();
  const tone = /active|hoạt động|hoàn thành|còn hàng/.test(normalized) ? "success" : /locked|hết|hủy|từ chối/.test(normalized) ? "danger" : "warning";
  return <span className={`status-badge ${tone}`}><i />{value}</span>;
}

function RoleBadge({ role }) {
  return <span className={`role-badge ${portalFromRole(role) === "admin" ? "admin" : "employee"}`}><Icon name={portalFromRole(role) === "admin" ? "ShieldCheck" : "BadgeCheck"} size={14} />{role}</span>;
}

function AccessDenied() {
  return <div className="access-denied"><span><Icon name="ShieldX" size={36} /></span><h2>Không có quyền truy cập</h2><p>Tài khoản hiện tại không được phép mở khu vực này.</p></div>;
}

function Modal({ title, onClose, children, narrow = false }) {
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><section className={`modal ${narrow ? "narrow" : ""}`} role="dialog" aria-modal="true" aria-label={title}><div className="modal-header"><div><span>DX-LAB CORE</span><h2>{title}</h2></div><button onClick={onClose} aria-label="Đóng"><Icon name="X" /></button></div>{children}</section></div>;
}

export default function App() {
  const [session, setSession] = useState(null);

  if (!session) {
    return <LoginScreen onAuthenticated={(user, portal) => setSession({ user, portal })} />;
  }

  return <Workspace user={session.user} portal={session.portal} onLogout={() => setSession(null)} />;
}
