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
  ChevronLeft,
  ChevronRight,
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
  permissionsByRole,
  portalConfig,
  portalFromRole,
} from "./config/navigation";
import { AdminHeaderTools, AdminPageRouter } from "./admin/AdminPages";
import LoginScreen from "./features/auth/AuthPage";
import { API_BASE_URL, apiRequest } from "./api";
import { useCatalogCustomers, useCatalogProducts, usePromotions } from "./hooks/useCatalogData";
import { useMyOrders } from "./hooks/useMyOrders";

const SESSION_STORAGE_KEY = "dxlab.session.v1";

const formatMoney = (value) => `${new Intl.NumberFormat("vi-VN").format(value)} ₫`;
const formatDateTime = (value) => value
  ? new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value))
  : "—";

const iconMap = {
  ArrowLeftRight, ArrowRight, ArrowUpRight, BadgeCheck, BadgePercent, BarChart3,
  Bell, BellRing, Boxes, Building2, CalendarDays, ChartNoAxesCombined, ChevronLeft,
  ChevronRight, Circle,
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

function LogoMark() {
  return <span className="logo-mark"><span>DX</span></span>;
}

function Workspace({ user, portal, token, onLogout }) {
  const config = portalConfig[portal];
  const rolePermissions = permissionsByRole[user?.RoleID] || new Set();
  const allowedMenu = menus[portal].filter((item) => rolePermissions.has(item.permission));
  const location = useLocation();
  const routeNavigate = useNavigate();
  const routePrefix = `/${portal}/`;
  const requestedPage = location.pathname.startsWith(routePrefix)
    ? location.pathname.slice(routePrefix.length).split("/")[0]
    : "";
  const fallbackPage = allowedMenu.some((item) => item.id === config.landingPage)
    ? config.landingPage
    : allowedMenu[0]?.id;
  const page = allowedMenu.some((item) => item.id === requestedPage) ? requestedPage : fallbackPage;
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
    if (!target || !rolePermissions.has(target.permission)) {
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
          <PageRouter page={page} portal={portal} token={token} user={user} permissions={rolePermissions} onNavigate={navigate} showToast={showToast} />
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

function PageRouter({ page, portal, token, user, permissions, onNavigate, showToast }) {
  const allowed = menus[portal].find((item) => item.id === page);
  if (!allowed || !permissions.has(allowed.permission)) return <AccessDenied />;

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
  const [productPage, setProductPage] = useState(1);
  const [cart, setCart] = useState([]);
  const [customerId, setCustomerId] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [promotionId, setPromotionId] = useState("");
  const [checkingOut, setCheckingOut] = useState(false);
  const [quote, setQuote] = useState(null);
  const [quoteError, setQuoteError] = useState("");
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteRevision, setQuoteRevision] = useState(0);
  const checkoutKeyRef = useRef(null);
  const productData = useCatalogProducts(token, { q: query, page: productPage, pageSize: 12 });
  const { items: products, loading, error, reload: reloadProducts } = productData;
  const customerData = useCatalogCustomers(token);
  const promotionData = usePromotions(token);
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const selectedCustomer = customerData.items.find((item) => item.id === customerId);
  const eligiblePromotions = promotionData.items.filter((promotion) => {
    const tierMatches = promotion.customerTier === "Tất cả khách hàng"
      || promotion.customerTier.toLowerCase() === String(selectedCustomer?.tier || "").toLowerCase();
    const usageAvailable = promotion.maxUses == null || promotion.usedCount < promotion.maxUses;
    const scopeMatches = promotion.appliedProductId
      ? cart.some((item) => item.id === promotion.appliedProductId)
      : promotion.appliedCategory
        ? cart.some((item) => item.category.toLowerCase() === promotion.appliedCategory.toLowerCase())
        : true;
    return tierMatches && usageAvailable && scopeMatches
      && total >= promotion.minOrderValue && promotion.discountValue > 0;
  });
  const previewSubtotal = quote?.subtotal_value ?? total;
  const previewDiscount = quote?.discount_value ?? 0;
  const previewTotal = quote?.total_value ?? total;
  const cartSignature = cart.map((item) => `${item.id}:${item.quantity}:${item.price}`).join("|");

  useEffect(() => {
    checkoutKeyRef.current = null;
  }, [cartSignature, customerId, paymentMethod, promotionId]);

  useEffect(() => {
    if (!cart.length || !customerId) {
      setQuote(null);
      setQuoteError("");
      setQuoteLoading(false);
      return undefined;
    }

    const controller = new AbortController();
    setQuote(null);
    setQuoteError("");
    setQuoteLoading(true);
    const timer = window.setTimeout(() => {
      apiRequest("/orders/preview", {
        token,
        method: "POST",
        signal: controller.signal,
        body: {
          customer_id: customerId,
          promotion_id: promotionId || null,
          items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })),
        },
      })
        .then(setQuote)
        .catch((requestError) => {
          if (requestError.name !== "AbortError") {
            setQuote(null);
            setQuoteError(requestError.message);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setQuoteLoading(false);
        });
    }, 250);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [cart, customerId, promotionId, quoteRevision, token]);

  useEffect(() => {
    if (promotionId && !eligiblePromotions.some((item) => item.id === promotionId)) {
      setPromotionId("");
    }
  }, [eligiblePromotions, promotionId]);

  useEffect(() => {
    if (!customerId && customerData.items.length) {
      setCustomerId(customerData.items[0].id);
    }
  }, [customerData.items, customerId]);

  useEffect(() => {
    setCart((current) => {
      let changed = false;
      const next = current.map((item) => {
        const latest = products.find((product) => product.id === item.id);
        if (!latest) return item;
        const unchanged = latest.name === item.name
          && latest.category === item.category
          && latest.price === item.price
          && latest.stock === item.stock;
        if (unchanged) return item;
        changed = true;
        return { ...latest, quantity: item.quantity };
      });
      return changed ? next : current;
    });
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
    if (!cart.length || !customerId || !quote || checkingOut || quoteLoading || quoteError) return;
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
          expected_total_value: Number(quote.total_value),
          promotion_id: promotionId || null,
          items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })),
        },
      });
      showToast(`Đã thanh toán đơn ${order.order_id} · ${formatMoney(order.total_value)} cho ${order.customer_name}.`);
      checkoutKeyRef.current = null;
      setCart([]);
      setPromotionId("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["live-collection"] }),
        queryClient.invalidateQueries({ queryKey: ["my-orders"] }),
        queryClient.invalidateQueries({ queryKey: ["admin"] }),
      ]);
    } catch (requestError) {
      showToast(requestError.message);
      setQuoteRevision((current) => current + 1);
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
          <div className="pos-toolbar"><div className="search-box"><Icon name="Search" size={18} /><input value={query} onChange={(event) => { setQuery(event.target.value); setProductPage(1); }} placeholder="Tìm sản phẩm hoặc danh mục..." /></div><span>{productData.total} sản phẩm</span></div>
          <div className="product-grid">
            {loading && <DataState icon="PackageSearch" title="Đang tải danh mục" description="Đang đồng bộ giá và tồn kho từ SQL Server..." />}
            {!loading && error && <DataState icon="CircleAlert" title="Không tải được sản phẩm" description={error} action="Thử lại" onAction={reloadProducts} />}
            {!loading && !error && !products.length && <DataState icon="PackageX" title="Không tìm thấy sản phẩm" description="Hãy thử từ khóa hoặc danh mục khác." />}
            {products.map((product) => (
              <article className="product-card" key={product.id}>
                <div className="product-visual"><Icon name={product.category === "Laptop" ? "Laptop" : product.category === "Màn hình" ? "Monitor" : "Package"} size={34} /><span className={product.stock <= product.reorder ? "low" : ""}>{product.stock} còn lại</span></div>
                <small>{product.id} · {product.category}</small><h3>{product.name}</h3><div><strong>{formatMoney(product.price)}</strong><button disabled={product.stock <= 0} onClick={() => addToCart(product)} aria-label={`Thêm ${product.name}`}><Icon name="Plus" size={19} /></button></div>
              </article>
            ))}
          </div>
          <Pagination page={productData.page} totalPages={productData.totalPages} onPage={setProductPage} />
        </section>
        <aside className="cart-panel">
          <div className="cart-head"><div><span>ĐƠN HÀNG HIỆN TẠI</span><h3>Giỏ hàng</h3></div><b>{cart.reduce((sum, item) => sum + item.quantity, 0)}</b></div>
          <label className="cart-customer"><span>Khách hàng</span><select value={customerId} disabled={customerData.loading} onChange={(event) => setCustomerId(event.target.value)}><option value="">{customerData.loading ? "Đang tải khách hàng..." : "Chọn khách hàng"}</option>{customerData.items.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>{customerData.error && <small>{customerData.error}</small>}</label>
          <label className="cart-customer"><span>Phương thức thanh toán</span><select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}><option value="Cash">Tiền mặt</option><option value="BankTransfer">Chuyển khoản</option></select></label>
          <label className="cart-customer"><span>Khuyến mãi</span><select value={promotionId} disabled={!eligiblePromotions.length} onChange={(event) => setPromotionId(event.target.value)}><option value="">{eligiblePromotions.length ? "Không áp dụng" : "Không có chương trình phù hợp"}</option>{eligiblePromotions.map((promotion) => <option key={promotion.id} value={promotion.id}>{promotion.title} · {promotion.tag}</option>)}</select><small>Backend sẽ xác minh lại toàn bộ điều kiện khi thanh toán.</small></label>
          <div className="cart-items">
            {!cart.length && <div className="empty-cart"><Icon name="ShoppingBasket" size={34} /><b>Giỏ hàng đang trống</b><span>Chọn sản phẩm để bắt đầu bán hàng.</span></div>}
            {cart.map((item) => <div className="cart-item" key={item.id}><div><b>{item.name}</b><span>{formatMoney(item.price)}</span></div><div className="quantity"><button onClick={() => changeQuantity(item.id, -1)}><Icon name="Minus" size={14} /></button><span>{item.quantity}</span><button onClick={() => changeQuantity(item.id, 1)}><Icon name="Plus" size={14} /></button></div></div>)}
          </div>
          <div className="cart-summary"><div><span>Khách hàng</span><b>{selectedCustomer?.name || "Chưa chọn"}</b></div><div><span>Tạm tính</span><b>{formatMoney(previewSubtotal)}</b></div><div><span>Giảm giá</span><b>{formatMoney(previewDiscount)}</b></div><div className="cart-total"><span>{quoteLoading ? "Backend đang tính..." : "Tổng thanh toán dự kiến"}</span><strong>{formatMoney(previewTotal)}</strong></div>{quoteError && <small className="quote-error">{quoteError}</small>}<button className="checkout-button" disabled={!cart.length || !customerId || !quote || checkingOut || quoteLoading || Boolean(quoteError)} onClick={checkout}><Icon name="CreditCard" size={19} /> {checkingOut ? "Đang ghi nhận..." : "Thanh toán"}</button><small><Icon name="ShieldCheck" size={14} /> Số tiền này do backend tính lại từ giá và khuyến mãi trong SQL Server.</small></div>
        </aside>
      </div>
    </div>
  );
}

function CatalogPage({ token }) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const productData = useCatalogProducts(token, { q: query, page, pageSize: 20 });
  const { items: products, loading, error, reload } = productData;
  return <div className="page-stack"><PageHeading eyebrow="TRA CỨU" title="Danh mục sản phẩm" description="Giá bán và tồn kho được đồng bộ trực tiếp từ SQL Server; nhân viên không thể sửa dữ liệu." /><TableToolbar query={query} onQuery={(value) => { setQuery(value); setPage(1); }} placeholder="Tìm sản phẩm..." count={productData.total} /><div className="table-card">{loading ? <DataState icon="PackageSearch" title="Đang tải danh mục" description="Đang đồng bộ dữ liệu mới nhất..." /> : error ? <DataState icon="CircleAlert" title="Không tải được sản phẩm" description={error} action="Thử lại" onAction={reload} /> : products.length ? <table><thead><tr><th>Mã</th><th>Sản phẩm</th><th>Danh mục</th><th>Giá bán</th><th>Tồn kho</th><th>Trạng thái</th></tr></thead><tbody>{products.map((product) => <tr key={product.id}><td><b>{product.id}</b></td><td>{product.name}</td><td>{product.category}</td><td><b>{formatMoney(product.price)}</b></td><td>{product.stock}</td><td><StatusBadge value={product.status} /></td></tr>)}</tbody></table> : <DataState icon="PackageX" title="Không tìm thấy sản phẩm" description="Hãy thử từ khóa hoặc danh mục khác." />}</div><Pagination page={productData.page} totalPages={productData.totalPages} onPage={setPage} /></div>;
}

function Pagination({ page, totalPages, onPage }) {
  if (totalPages <= 1) return null;
  return <nav className="pagination" aria-label="Phân trang"><button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}><Icon name="ChevronLeft" size={16} /> Trước</button><span>Trang {page}/{totalPages}</span><button type="button" disabled={page >= totalPages} onClick={() => onPage(page + 1)}>Sau <Icon name="ChevronRight" size={16} /></button></nav>;
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
    const token = session?.token;
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setSession(null);
    if (token) {
      apiRequest("/logout", { token, method: "POST" }).catch(() => {});
    }
  };

  if (restoringSession) {
    return <main className="session-loading"><LogoMark /><b>Đang khôi phục phiên làm việc</b><span>DX-Lab đang xác thực tài khoản với máy chủ...</span></main>;
  }

  if (!session) {
    return <LoginScreen onAuthenticated={authenticate} />;
  }

  return <Workspace user={session.user} portal={session.portal} token={session.token} onLogout={logout} />;
}
