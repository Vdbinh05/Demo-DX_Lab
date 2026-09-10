// SPDX-License-Identifier: MIT
import React, { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
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
  menus,
  permissionsByPortal,
  portalConfig,
} from "./config/navigation";
import { AdminHeaderTools, AdminPageRouter } from "./admin/AdminPages";
import { API_BASE_URL, apiRequest } from "./api";
import { useCatalogCustomers, useCatalogProducts, usePromotions } from "./hooks/useCatalogData";
import { useMyOrders } from "./hooks/useMyOrders";

const LOGIN_API_URL = `${API_BASE_URL}/login`;
const REGISTER_API_URL = `${API_BASE_URL}/register`;
const SESSION_STORAGE_KEY = "dxlab.session.v1";

const formatMoney = (value) => `${new Intl.NumberFormat("vi-VN").format(value)} ₫`;
const formatDateTime = (value) => value
  ? new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value))
  : "—";

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

      onAuthenticated(data.user, accountPortal, data.access_token);
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
                <small>Dữ liệu trực tiếp</small>
              </div>
              <div className="preview-grid">
                <div><Icon name="TrendingUp" /><span>Doanh thu</span><b>Theo thời gian thực</b></div>
                <div><Icon name="ShoppingBag" /><span>Đơn hàng</span><b>Truy xuất đầy đủ</b></div>
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

function Workspace({ user, portal, token, onLogout }) {
  const config = portalConfig[portal];
  const allowedMenu = menus[portal].filter((item) => permissionsByPortal[portal].has(item.permission));
  const location = useLocation();
  const routeNavigate = useNavigate();
  const routePrefix = `/${portal}/`;
  const requestedPage = location.pathname.startsWith(routePrefix)
    ? location.pathname.slice(routePrefix.length).split("/")[0]
    : "";
  const page = allowedMenu.some((item) => item.id === requestedPage) ? requestedPage : config.landingPage;
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const canonicalPath = `${routePrefix}${page}`;
    if (location.pathname !== canonicalPath) routeNavigate(canonicalPath, { replace: true });
  }, [location.pathname, page, routeNavigate, routePrefix]);

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
    routeNavigate(`${routePrefix}${nextPage}`);
    setSidebarOpen(false);
  };

  const logout = () => {
    onLogout();
    routeNavigate("/", { replace: true });
  };

  return (
    <div className={`workspace-app portal-${portal}`}>
      <Sidebar portal={portal} menu={allowedMenu} page={page} onNavigate={navigate} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="workspace-main">
        <Header user={user} portal={portal} token={token} pageLabel={currentItem?.label} onNavigate={navigate} onLogout={logout} onOpenMenu={() => setSidebarOpen(true)} />
        <div className="workspace-content">
          <PageRouter page={page} portal={portal} token={token} user={user} onNavigate={navigate} showToast={showToast} />
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
        {portal === "employee" && <div className={`portal-badge ${portal}`}><Icon name={config.icon} size={18} /><div><span>KHÔNG GIAN</span><b>{config.shortLabel}</b></div></div>}
        <nav className="sidebar-nav">
          <span className="nav-caption">ĐIỀU HƯỚNG</span>
          {menu.map((item) => (
            <button key={item.id} className={page === item.id ? "active" : ""} onClick={() => onNavigate(item.id)}>
              <Icon name={item.icon} size={19} /><span>{item.label}</span>{page === item.id && <i />}
            </button>
          ))}
        </nav>
      </aside>
    </>
  );
}

function Header({ user, portal, token, pageLabel, onNavigate, onLogout, onOpenMenu }) {
  const fullName = user?.FullName || user?.Username || "Người dùng";
  const initials = fullName.split(/\s+/).filter(Boolean).slice(-2).map((word) => word[0]).join("").toUpperCase();
  return (
    <header className="workspace-header">
      <div className="header-title">
        <button className="mobile-menu" onClick={onOpenMenu}><Icon name="Menu" /></button>
        <div><span>DX-Lab Core / {portalConfig[portal].label}</span><h1>{pageLabel}</h1></div>
      </div>
      <div className="header-actions">
        {portal === "admin" ? <AdminHeaderTools token={token} onNavigate={onNavigate} /> : <><button className="header-icon" aria-label="Tìm kiếm"><Icon name="Search" size={19} /></button><button className="header-icon notification" aria-label="Thông báo"><Icon name="Bell" size={19} /><i /></button></>}
        <div className="profile"><span className="profile-avatar">{initials || "DX"}</span><div><b>{fullName}</b><span>{user?.RoleID || portalConfig[portal].label}</span></div><button onClick={onLogout} title="Đăng xuất"><Icon name="LogOut" size={18} /></button></div>
      </div>
    </header>
  );
}

function PageRouter({ page, portal, token, user, onNavigate, showToast }) {
  const allowed = menus[portal].find((item) => item.id === page);
  if (!allowed || !permissionsByPortal[portal].has(allowed.permission)) return <AccessDenied />;

  if (portal === "employee") {
    if (page === "pos") return <PointOfSale token={token} user={user} showToast={showToast} />;
    if (page === "catalog") return <CatalogPage token={token} />;
    if (page === "promotions") return <PromotionsPage token={token} />;
    if (page === "my-orders") return <MyOrdersPage token={token} />;
    if (page === "customers") return <CustomersPage token={token} />;
  }

  return <AdminPageRouter page={page} token={token} user={user} onNavigate={onNavigate} showToast={showToast} />;
}

function PageHeading({ eyebrow, title, description, children }) {
  return <div className="page-heading"><div><span>{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>{children && <div className="page-actions">{children}</div>}</div>;
}

function PointOfSale({ token, user, showToast }) {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState([]);
  const [customerId, setCustomerId] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [checkingOut, setCheckingOut] = useState(false);
  const checkoutKeyRef = useRef(null);
  const { items: products, loading, error, reload: reloadProducts } = useCatalogProducts(token);
  const customerData = useCatalogCustomers(token);
  const visibleProducts = products.filter((product) => `${product.name} ${product.category}`.toLowerCase().includes(query.toLowerCase()));
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const selectedCustomer = customerData.items.find((item) => item.id === customerId);
  const cartSignature = cart.map((item) => `${item.id}:${item.quantity}`).join("|");

  useEffect(() => {
    checkoutKeyRef.current = null;
  }, [cartSignature, customerId, paymentMethod]);

  useEffect(() => {
    if (!customerId && customerData.items.length) {
      setCustomerId(customerData.items[0].id);
    }
  }, [customerData.items, customerId]);

  useEffect(() => {
    setCart((current) => current.map((item) => {
      const latest = products.find((product) => product.id === item.id);
      return latest ? { ...latest, quantity: item.quantity } : item;
    }));
  }, [products]);

  const addToCart = (product) => {
    const existing = cart.find((item) => item.id === product.id);
    if (product.stock <= 0 || (existing && existing.quantity >= product.stock)) {
      showToast(`${product.name} không còn đủ tồn kho.`);
      return;
    }
    setCart((current) => existing
      ? current.map((item) => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item)
      : [...current, { ...product, quantity: 1 }]);
  };
  const changeQuantity = (id, change) => setCart((current) => current
    .map((item) => item.id === id ? { ...item, quantity: Math.min(item.stock, item.quantity + change) } : item)
    .filter((item) => item.quantity > 0));
  const checkout = async () => {
    if (!cart.length || !customerId || checkingOut) return;
    const idempotencyKey = checkoutKeyRef.current || window.crypto.randomUUID();
    checkoutKeyRef.current = idempotencyKey;
    setCheckingOut(true);
    try {
      const order = await apiRequest("/orders", {
        token,
        method: "POST",
        body: {
          customer_id: customerId,
          payment_method: paymentMethod,
          idempotency_key: idempotencyKey,
          items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })),
        },
      });
      showToast(`Đã thanh toán đơn ${order.order_id} · ${formatMoney(order.total_value)} cho ${order.customer_name}.`);
      checkoutKeyRef.current = null;
      setCart([]);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["live-collection"] }),
        queryClient.invalidateQueries({ queryKey: ["my-orders"] }),
        queryClient.invalidateQueries({ queryKey: ["admin"] }),
      ]);
    } catch (requestError) {
      showToast(requestError.message);
      reloadProducts();
    } finally {
      setCheckingOut(false);
    }
  };

  return (
    <div className="page-stack">
      <PageHeading eyebrow="KHU VỰC NHÂN VIÊN" title={`Chào ${user?.FullName || user?.Username || "bạn"}, bắt đầu bán hàng`} description="Chọn sản phẩm, xác nhận khách hàng và hoàn tất đơn ngay tại quầy." />
      <div className="pos-layout">
        <section className="pos-products">
          <div className="pos-toolbar"><div className="search-box"><Icon name="Search" size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm sản phẩm hoặc danh mục..." /></div><span>{visibleProducts.length} sản phẩm</span></div>
          <div className="product-grid">
            {loading && <DataState icon="PackageSearch" title="Đang tải danh mục" description="Đang đồng bộ giá và tồn kho từ SQL Server..." />}
            {!loading && error && <DataState icon="CircleAlert" title="Không tải được sản phẩm" description={error} action="Thử lại" onAction={reloadProducts} />}
            {!loading && !error && !visibleProducts.length && <DataState icon="PackageX" title="Không tìm thấy sản phẩm" description="Hãy thử từ khóa hoặc danh mục khác." />}
            {visibleProducts.map((product) => (
              <article className="product-card" key={product.id}>
                <div className="product-visual"><Icon name={product.category === "Laptop" ? "Laptop" : product.category === "Màn hình" ? "Monitor" : "Package"} size={34} /><span className={product.stock <= product.reorder ? "low" : ""}>{product.stock} còn lại</span></div>
                <small>{product.id} · {product.category}</small><h3>{product.name}</h3><div><strong>{formatMoney(product.price)}</strong><button disabled={product.stock <= 0} onClick={() => addToCart(product)} aria-label={`Thêm ${product.name}`}><Icon name="Plus" size={19} /></button></div>
              </article>
            ))}
          </div>
        </section>
        <aside className="cart-panel">
          <div className="cart-head"><div><span>ĐƠN HÀNG HIỆN TẠI</span><h3>Giỏ hàng</h3></div><b>{cart.reduce((sum, item) => sum + item.quantity, 0)}</b></div>
          <label className="cart-customer"><span>Khách hàng</span><select value={customerId} disabled={customerData.loading} onChange={(event) => setCustomerId(event.target.value)}><option value="">{customerData.loading ? "Đang tải khách hàng..." : "Chọn khách hàng"}</option>{customerData.items.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>{customerData.error && <small>{customerData.error}</small>}</label>
          <label className="cart-customer"><span>Phương thức thanh toán</span><select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}><option value="Cash">Tiền mặt</option><option value="BankTransfer">Chuyển khoản</option></select></label>
          <div className="cart-items">
            {!cart.length && <div className="empty-cart"><Icon name="ShoppingBasket" size={34} /><b>Giỏ hàng đang trống</b><span>Chọn sản phẩm để bắt đầu bán hàng.</span></div>}
            {cart.map((item) => <div className="cart-item" key={item.id}><div><b>{item.name}</b><span>{formatMoney(item.price)}</span></div><div className="quantity"><button onClick={() => changeQuantity(item.id, -1)}><Icon name="Minus" size={14} /></button><span>{item.quantity}</span><button onClick={() => changeQuantity(item.id, 1)}><Icon name="Plus" size={14} /></button></div></div>)}
          </div>
          <div className="cart-summary"><div><span>Khách hàng</span><b>{selectedCustomer?.name || "Chưa chọn"}</b></div><div><span>Tạm tính</span><b>{formatMoney(total)}</b></div><div><span>Giảm giá</span><b>0 ₫</b></div><div className="cart-total"><span>Tổng thanh toán</span><strong>{formatMoney(total)}</strong></div><button className="checkout-button" disabled={!cart.length || !customerId || checkingOut} onClick={checkout}><Icon name="CreditCard" size={19} /> {checkingOut ? "Đang ghi nhận..." : "Thanh toán"}</button><small><Icon name="ShieldCheck" size={14} /> Giá và tồn kho được backend xác nhận lại trước khi tạo đơn.</small></div>
        </aside>
      </div>
    </div>
  );
}

function CatalogPage({ token }) {
  const [query, setQuery] = useState("");
  const { items: products, loading, error, reload } = useCatalogProducts(token);
  const filtered = products.filter((product) => JSON.stringify(product).toLowerCase().includes(query.toLowerCase()));
  return <div className="page-stack"><PageHeading eyebrow="TRA CỨU" title="Danh mục sản phẩm" description="Giá bán và tồn kho được đồng bộ trực tiếp từ SQL Server; nhân viên không thể sửa dữ liệu." /><TableToolbar query={query} onQuery={setQuery} placeholder="Tìm sản phẩm..." count={filtered.length} /><div className="table-card">{loading ? <DataState icon="PackageSearch" title="Đang tải danh mục" description="Đang đồng bộ dữ liệu mới nhất..." /> : error ? <DataState icon="CircleAlert" title="Không tải được sản phẩm" description={error} action="Thử lại" onAction={reload} /> : filtered.length ? <table><thead><tr><th>Mã</th><th>Sản phẩm</th><th>Danh mục</th><th>Giá bán</th><th>Tồn kho</th><th>Trạng thái</th></tr></thead><tbody>{filtered.map((product) => <tr key={product.id}><td><b>{product.id}</b></td><td>{product.name}</td><td>{product.category}</td><td><b>{formatMoney(product.price)}</b></td><td>{product.stock}</td><td><StatusBadge value={product.status} /></td></tr>)}</tbody></table> : <DataState icon="PackageX" title="Không tìm thấy sản phẩm" description="Hãy thử từ khóa hoặc danh mục khác." />}</div></div>;
}

function DataState({ icon, title, description, action, onAction }) {
  return <div className="sale-data-state"><Icon name={icon} size={28} /><b>{title}</b><span>{description}</span>{action && <button type="button" onClick={onAction}>{action}</button>}</div>;
}

function PromotionsPage({ token }) {
  const { items: promotions, loading, error, reload } = usePromotions(token);
  const [selected, setSelected] = useState(null);
  return <div className="page-stack"><PageHeading eyebrow="HỖ TRỢ BÁN HÀNG" title="Chương trình khuyến mãi" description="Chỉ hiển thị chương trình còn hiệu lực được đồng bộ từ SQL Server." />{loading ? <DataState icon="Sparkles" title="Đang tải khuyến mãi" description="Đang kiểm tra các chương trình còn hiệu lực..." /> : error ? <DataState icon="CircleAlert" title="Không tải được khuyến mãi" description={error} action="Thử lại" onAction={reload} /> : promotions.length ? <div className="promotion-grid">{promotions.map((promotion) => <article className={`promotion-card ${promotion.color}`} key={promotion.id}><div><span>{promotion.tag}</span><Icon name="Sparkles" /></div><small>{promotion.expires}</small><h3>{promotion.title}</h3><p>{promotion.description}</p><button type="button" onClick={() => setSelected(promotion)}>Tư vấn ngay <Icon name="ArrowRight" size={16} /></button></article>)}</div> : <DataState icon="Sparkles" title="Chưa có khuyến mãi" description="Hiện không có chương trình nào đang trong thời gian áp dụng." />}<div className="information-card"><Icon name="CircleHelp" /><div><b>Nhân viên cần lưu ý</b><p>Kiểm tra đúng hạng khách hàng và thời hạn trước khi tư vấn áp dụng chương trình.</p></div></div>{selected && <Modal title={selected.title} narrow onClose={() => setSelected(null)}><div className="promotion-detail"><span className="tier-badge">{selected.tag}</span><h3>Đối tượng: {selected.customerTier}</h3><p>{selected.description}</p><dl><div><dt>Bắt đầu</dt><dd>{new Intl.DateTimeFormat("vi-VN").format(new Date(`${selected.startDate}T00:00:00`))}</dd></div><div><dt>Kết thúc</dt><dd>{new Intl.DateTimeFormat("vi-VN").format(new Date(`${selected.endDate}T00:00:00`))}</dd></div></dl><button className="primary-button" type="button" onClick={() => setSelected(null)}>Đã hiểu điều kiện</button></div></Modal>}</div>;
}

function MyOrdersPage({ token }) {
  const { data, loading, error, reload } = useMyOrders(token);
  if (loading) return <DataState icon="ReceiptText" title="Đang tải đơn hàng" description="Đang đọc lịch sử bán hàng của bạn từ SQL Server..." />;
  if (error) return <DataState icon="CircleAlert" title="Không tải được đơn hàng" description={error} action="Thử lại" onAction={reload} />;
  const summary = data.summary;
  return <div className="page-stack"><PageHeading eyebrow="CÁ NHÂN" title="Đơn hàng của tôi" description="Chỉ hiển thị giao dịch do chính tài khoản đang đăng nhập tạo." /><div className="order-summary"><div><span>Doanh thu hôm nay</span><b>{formatMoney(summary.today_revenue)}</b></div><div><span>Đơn hôm nay</span><b>{summary.today_orders} đơn</b></div><div><span>Tổng doanh thu</span><b>{formatMoney(summary.total_revenue)}</b></div><div><span>Tổng đơn đã bán</span><b>{summary.total_orders} đơn</b></div></div><Panel title="Lịch sử bán hàng" subtitle="Dữ liệu thanh toán thật từ SQL Server">{data.items.length ? <div className="table-scroll"><table><thead><tr><th>Mã đơn</th><th>Khách hàng</th><th>Giá trị</th><th>Thanh toán</th><th>Thời gian</th></tr></thead><tbody>{data.items.map((order) => <tr key={order.order_id}><td><b>{order.order_id}</b></td><td>{order.customer}</td><td><b>{formatMoney(order.total_value)}</b></td><td><span className="tier-badge">{order.payment_method === "BankTransfer" ? "Chuyển khoản" : "Tiền mặt"}</span></td><td>{formatDateTime(order.paid_at)}</td></tr>)}</tbody></table></div> : <DataState icon="ReceiptText" title="Chưa có đơn hàng" description="Các đơn bạn thanh toán tại quầy sẽ xuất hiện tại đây." />}</Panel></div>;
}

function CustomersPage({ token }) {
  const { items, loading, error, reload } = useCatalogCustomers(token);
  const [query, setQuery] = useState("");
  const filtered = items.filter((customer) => JSON.stringify(customer).toLowerCase().includes(query.toLowerCase()));
  return <div className="page-stack"><PageHeading eyebrow="TRA CỨU" title="Khách hàng" description="Danh sách khách hàng hoạt động được đồng bộ trực tiếp từ SQL Server; nhân viên chỉ có quyền xem." /><TableToolbar query={query} onQuery={setQuery} placeholder="Tìm khách hàng..." count={filtered.length} /><div className="table-card">{loading ? <DataState icon="UsersRound" title="Đang tải khách hàng" description="Đang đồng bộ danh sách mới nhất..." /> : error ? <DataState icon="CircleAlert" title="Không tải được khách hàng" description={error} action="Thử lại" onAction={reload} /> : filtered.length ? <table><thead><tr><th>Mã</th><th>Khách hàng</th><th>Người liên hệ</th><th>Điện thoại</th><th>Hạng</th><th>Trạng thái</th></tr></thead><tbody>{filtered.map((customer) => <tr key={customer.id}><td><b>{customer.id}</b></td><td>{customer.name}</td><td>{customer.contact}</td><td>{customer.phone}</td><td><span className="tier-badge">{customer.tier}</span></td><td><StatusBadge value={customer.status} /></td></tr>)}</tbody></table> : <DataState icon="UsersRound" title="Không tìm thấy khách hàng" description="Hãy thử từ khóa khác." />}</div></div>;
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
  const [restoringSession, setRestoringSession] = useState(true);

  useEffect(() => {
    let active = true;
    const savedSession = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!savedSession) {
      setRestoringSession(false);
      return () => { active = false; };
    }

    let parsed;
    try {
      parsed = JSON.parse(savedSession);
    } catch {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
      setRestoringSession(false);
      return () => { active = false; };
    }

    if (!parsed?.token) {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
      setRestoringSession(false);
      return () => { active = false; };
    }

    apiRequest("/me", { token: parsed.token })
      .then((user) => {
        if (!active) return;
        const portal = portalFromRole(user.RoleID);
        if (!portal) throw new Error("Unsupported role");
        setSession({ user, portal, token: parsed.token });
      })
      .catch(() => {
        window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
      })
      .finally(() => {
        if (active) setRestoringSession(false);
      });

    return () => { active = false; };
  }, []);

  const authenticate = (user, portal, token) => {
    const nextSession = { user, portal, token };
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
  };

  const logout = () => {
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setSession(null);
  };

  if (restoringSession) {
    return <main className="session-loading"><LogoMark /><b>Đang khôi phục phiên làm việc</b><span>DX-Lab đang xác thực tài khoản với máy chủ...</span></main>;
  }

  if (!session) {
    return <LoginScreen onAuthenticated={authenticate} />;
  }

  return <Workspace user={session.user} portal={session.portal} token={session.token} onLogout={logout} />;
}
