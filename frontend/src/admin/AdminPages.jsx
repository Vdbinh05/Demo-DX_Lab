import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowDownToLine,
  ArrowLeftRight,
  Bell,
  Boxes,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  CircleDollarSign,
  Clock3,
  CreditCard,
  Database,
  Ellipsis,
  FileSearch,
  Landmark,
  LoaderCircle,
  Lock,
  LockOpen,
  Package,
  PackageCheck,
  PackagePlus,
  PackageX,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  ShoppingBag,
  Trash2,
  TrendingUp,
  TriangleAlert,
  UserPlus,
  UsersRound,
  WalletCards,
  X,
} from "lucide-react";
import { apiRequest } from "../api";
import "./admin.css";


const money = (value = 0) => `${new Intl.NumberFormat("vi-VN").format(Number(value) || 0)} ₫`;
const number = (value = 0) => new Intl.NumberFormat("vi-VN").format(Number(value) || 0);
const dateTime = (value) => value
  ? new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value))
  : "Chưa có dữ liệu";
const now = new Date();
const currentMonth = `${String(now.getMonth() + 1).padStart(2, "0")}/${now.getFullYear()}`;

function useRemote(path, token) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    let controller = null;

    const load = ({ silent = false } = {}) => {
      controller?.abort();
      controller = new AbortController();
      if (!silent) setLoading(true);
      setError("");
      apiRequest(path, { token, signal: controller.signal })
        .then((response) => { if (active) setData(response); })
        .catch((requestError) => {
          if (active && requestError.name !== "AbortError") setError(requestError.message);
        })
        .finally(() => { if (active && !silent) setLoading(false); });
    };

    load();
    const refresh = () => load({ silent: true });
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    const interval = window.setInterval(refresh, 15000);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refreshWhenVisible);

    return () => {
      active = false;
      controller?.abort();
      window.clearInterval(interval);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, [path, token, version]);

  return { data, loading, error, reload: () => setVersion((value) => value + 1) };
}

function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="admin-page-header">
      <div><span>{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>
      {actions && <div className="admin-page-actions">{actions}</div>}
    </div>
  );
}

function LoadingState({ label = "Đang lấy dữ liệu từ SQL Server..." }) {
  return <div className="admin-state"><LoaderCircle className="spin" /><b>{label}</b></div>;
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="admin-state error">
      <CircleAlert /><div><b>Không tải được dữ liệu</b><span>{message}</span></div>
      <button onClick={onRetry}><RefreshCw size={16} /> Thử lại</button>
    </div>
  );
}

function EmptyState({ icon: Icon = FileSearch, title, description }) {
  return <div className="admin-empty"><Icon /><b>{title}</b><span>{description}</span></div>;
}

function Metric({ icon: Icon, label, value, note, tone = "blue" }) {
  return (
    <article className="real-metric">
      <span className={`real-metric-icon ${tone}`}><Icon /></span>
      <div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>
    </article>
  );
}

function Card({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`admin-card ${className}`}>
      <header><div><h3>{title}</h3>{subtitle && <span>{subtitle}</span>}</div>{action}</header>
      {children}
    </section>
  );
}

function RevenueChart({ items = [] }) {
  const max = Math.max(1, ...items.map((item) => Number(item.revenue) || 0));
  return (
    <div className="real-chart" role="img" aria-label="Biểu đồ doanh thu sáu tháng gần nhất">
      <div className="real-chart-bars">
        {items.map((item, index) => (
          <div className="real-chart-column" key={`${item.year}-${item.month}`}>
            <div className="real-chart-value">{money(item.revenue)}</div>
            <i className={index === items.length - 1 ? "current" : ""} style={{ height: `${Math.max(3, (Number(item.revenue) / max) * 100)}%` }} />
            <span>T{item.month}/{String(item.year).slice(-2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function PaymentBadge({ method }) {
  const normalized = String(method || "Cash").toLowerCase();
  const bank = normalized.includes("bank") || normalized.includes("transfer") || normalized.includes("chuyển");
  return <span className={`payment-badge ${bank ? "bank" : "cash"}`}>{bank ? <Landmark size={14} /> : <CircleDollarSign size={14} />}{bank ? "Chuyển khoản" : "Tiền mặt"}</span>;
}

function PaidBadge({ value }) {
  const paid = /paid|completed|hoàn thành/i.test(String(value));
  return <span className={`paid-badge ${paid ? "paid" : "other"}`}><i />{paid ? "Đã thanh toán" : value}</span>;
}

function OrdersTable({ items, onOpen }) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <thead><tr><th>Mã đơn</th><th>Khách hàng</th><th>Nhân viên</th><th>Giá trị</th><th>Thanh toán</th><th>Thời gian</th><th aria-label="Thao tác" /></tr></thead>
        <tbody>{items.map((order) => (
          <tr key={order.order_id}>
            <td><b>{order.order_id}</b></td><td>{order.customer}</td><td>{order.seller}</td>
            <td><b>{money(order.total_value)}</b></td><td><PaymentBadge method={order.payment_method} /></td>
            <td>{dateTime(order.created_at)}</td>
            <td><button className="icon-action" onClick={() => onOpen(order.order_id)} aria-label={`Xem chi tiết ${order.order_id}`}><Ellipsis size={19} /></button></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function AdminModal({ title, subtitle, onClose, children, wide = false }) {
  return (
    <div className="admin-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={`admin-modal ${wide ? "wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <header><div><span>DX-LAB CORE</span><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button onClick={onClose} aria-label="Đóng"><X /></button></header>
        {children}
      </section>
    </div>
  );
}

function OrderDetail({ orderId, token, onClose }) {
  const { data, loading, error, reload } = useRemote(`/admin/orders/${encodeURIComponent(orderId)}`, token);
  return (
    <AdminModal title={`Chi tiết đơn ${orderId}`} subtitle="Dữ liệu được truy xuất trực tiếp từ lịch sử bán hàng" onClose={onClose} wide>
      {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> : (
        <div className="order-detail">
          <div className="order-detail-grid">
            <div><span>Khách hàng</span><b>{data.customer}</b><small>{data.contact_name || "Không có người liên hệ"} · {data.phone || "Chưa có SĐT"}</small></div>
            <div><span>Nhân viên bán</span><b>{data.seller}</b><small>{dateTime(data.created_at)}</small></div>
            <div><span>Phương thức</span><PaymentBadge method={data.payment_method} /></div>
            <div><span>Trạng thái</span><PaidBadge value={data.order_status} /></div>
          </div>
          <div className="detail-items">
            <table className="admin-table"><thead><tr><th>Sản phẩm</th><th>Đơn giá</th><th>Số lượng</th><th>Thành tiền</th></tr></thead>
              <tbody>{data.items.map((item) => <tr key={item.product_id}><td><b>{item.name}</b><small>{item.product_id}</small></td><td>{money(item.unit_price)}</td><td>{item.quantity}</td><td><b>{money(item.subtotal)}</b></td></tr>)}</tbody>
            </table>
          </div>
          <div className="order-detail-total"><span>Tổng thanh toán</span><strong>{money(data.total_value)}</strong></div>
        </div>
      )}
    </AdminModal>
  );
}

export function AdminOverview({ token, onNavigate }) {
  const { data, loading, error, reload } = useRemote("/admin/dashboard", token);
  const [orderId, setOrderId] = useState(null);
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (loading || !data) return <LoadingState />;
  const metrics = data.metrics;
  return (
    <div className="admin-stack">
      <PageHeader eyebrow="TỔNG QUAN KINH DOANH" title="Dữ liệu vận hành hôm nay" description={`Cập nhật từ SQL Server · tháng ${currentMonth}`} actions={<button className="admin-secondary" onClick={reload}><RefreshCw size={16} /> Làm mới</button>} />
      <div className="real-metric-grid">
        <Metric icon={WalletCards} label="Doanh thu tháng" value={money(metrics.month_revenue)} note={`${number(metrics.month_orders)} đơn đã thanh toán`} />
        <Metric icon={TrendingUp} label="Doanh thu hôm nay" value={money(metrics.today_revenue)} note={`${number(metrics.today_orders)} đơn phát sinh`} tone="violet" />
        <Metric icon={ShoppingBag} label="Đơn đã bán trong tháng" value={number(metrics.month_orders)} note="Chỉ tính đơn đã thanh toán" tone="green" />
        <Metric icon={UsersRound} label="Khách hàng" value={number(metrics.customer_count)} note={`${number(data.today_customers.length)} khách mua hôm nay`} tone="green" />
        <Metric icon={ShieldCheck} label="Tài khoản hệ thống" value={number(metrics.account_count)} note="Tài khoản thực đã được tạo" tone="blue" />
        <Metric icon={TriangleAlert} label="Cảnh báo tồn kho" value={number(metrics.low_stock_count)} note="Sản phẩm cần bổ sung" tone="orange" />
      </div>
      <div className="admin-dashboard-grid">
        <Card title="Doanh thu 6 tháng" subtitle="Chỉ tính đơn đã thanh toán" action={<button className="link-button" onClick={() => onNavigate("revenue")}>Xem báo cáo <ChevronRight size={16} /></button>}><RevenueChart items={data.monthly_revenue} /></Card>
        <Card title="Sản phẩm bán chạy" subtitle={`Tháng ${currentMonth}`}>
          {data.top_products.length ? <div className="real-ranking">{data.top_products.map((product, index) => <div key={product.product_id}><span>{index + 1}</span><i><Package size={18} /></i><div><b>{product.name}</b><small>{product.category}</small></div><strong>{number(product.sold_quantity)} đã bán</strong></div>)}</div> : <EmptyState icon={Package} title="Chưa có sản phẩm bán ra" description="Dữ liệu sẽ xuất hiện sau khi có đơn thanh toán." />}
        </Card>
      </div>
      <div className="admin-dashboard-grid lower">
        <Card title="Đơn hàng gần đây" subtitle="Có thể mở để truy xuất từng sản phẩm" action={<button className="link-button" onClick={() => onNavigate("orders")}>Xem tất cả <ChevronRight size={16} /></button>} className="orders-card">
          {data.recent_orders.length ? <OrdersTable items={data.recent_orders} onOpen={setOrderId} /> : <EmptyState title="Chưa có đơn hàng" description="Đơn bán hàng thật sẽ hiển thị tại đây." />}
        </Card>
        <Card title="Khách mua hôm nay" subtitle={`${data.today_customers.length} khách hàng`}>
          {data.today_customers.length ? <div className="today-customers">{data.today_customers.map((customer) => <div key={customer.customer_id}><span>{customer.name.slice(0, 1).toUpperCase()}</span><div><b>{customer.name}</b><small>{customer.contact_name || customer.phone || "Chưa có liên hệ"}</small></div></div>)}</div> : <EmptyState icon={UsersRound} title="Hôm nay chưa có khách mua" description="Danh sách tự cập nhật khi Sale thanh toán đơn." />}
        </Card>
      </div>
      {orderId && <OrderDetail orderId={orderId} token={token} onClose={() => setOrderId(null)} />}
    </div>
  );
}

export function RevenuePage({ token }) {
  const { data, loading, error, reload } = useRemote("/admin/revenue", token);
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (loading || !data) return <LoadingState />;
  const exportCsv = () => {
    const rows = [["Tháng", "Doanh thu", "Số đơn"], ...data.months.map((item) => [`${item.month}/${item.year}`, item.revenue, item.order_count])];
    const blob = new Blob([`\uFEFF${rows.map((row) => row.join(",")).join("\n")}`], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob); link.download = `doanh-thu-${currentMonth.replace("/", "-")}.csv`; link.click();
    URL.revokeObjectURL(link.href);
  };
  const total = Math.max(1, ...data.categories.map((item) => Number(item.revenue)));
  return (
    <div className="admin-stack">
      <PageHeader eyebrow="BÁO CÁO DOANH THU" title={`Kết quả tháng ${currentMonth}`} description="Số liệu tổng hợp từ các đơn đã thanh toán, không sử dụng dữ liệu mô phỏng." actions={<button className="admin-secondary" onClick={exportCsv}><ArrowDownToLine size={17} /> Xuất CSV</button>} />
      <div className="real-metric-grid">
        <Metric icon={WalletCards} label="Tổng doanh thu" value={money(data.summary.month_revenue)} note="Trong tháng hiện tại" />
        <Metric icon={ShoppingBag} label="Đơn đã thanh toán" value={number(data.summary.paid_orders)} note="Không gồm đơn hủy" tone="violet" />
        <Metric icon={CreditCard} label="Giá trị trung bình" value={money(data.summary.average_order)} note="Trên mỗi đơn" tone="green" />
        <Metric icon={UsersRound} label="Khách đã mua" value={number(data.summary.purchasing_customers)} note="Khách hàng duy nhất" tone="orange" />
      </div>
      <Card title="Doanh thu theo tháng" subtitle="Sáu tháng gần nhất"><RevenueChart items={data.months} /></Card>
      <Card title="Cơ cấu doanh thu" subtitle="Theo nhóm sản phẩm đã bán">
        {data.categories.length ? <div className="category-breakdown">{data.categories.map((item) => <div key={item.category}><div><b>{item.category}</b><span>{money(item.revenue)} · {number(item.quantity)} sản phẩm</span></div><i><span style={{ width: `${(Number(item.revenue) / total) * 100}%` }} /></i></div>)}</div> : <EmptyState title="Chưa có doanh thu" description="Cơ cấu sẽ xuất hiện khi có đơn đã thanh toán." />}
      </Card>
    </div>
  );
}

export function OrdersPage({ token }) {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [orderId, setOrderId] = useState(null);
  const path = `/admin/orders?q=${encodeURIComponent(submitted)}`;
  const { data, loading, error, reload } = useRemote(path, token);
  const items = data?.items || [];
  const today = new Date().toDateString();
  const stats = useMemo(() => ({
    today: items.filter((item) => new Date(item.created_at).toDateString() === today).length,
    paid: items.filter((item) => /paid|completed|hoàn thành/i.test(item.order_status)).length,
    cash: items.filter((item) => !/bank|transfer|chuyển/i.test(item.payment_method || "Cash")).length,
    bank: items.filter((item) => /bank|transfer|chuyển/i.test(item.payment_method || "")).length,
  }), [items, today]);
  return (
    <div className="admin-stack">
      <PageHeader eyebrow="LỊCH SỬ GIAO DỊCH" title="Tất cả đơn hàng" description="Tra cứu khách hàng, sản phẩm, nhân viên, thời gian và phương thức thanh toán." />
      <div className="order-stat-grid"><div><span>Hôm nay</span><b>{stats.today} đơn</b></div><div><span>Đã thanh toán</span><b>{stats.paid} đơn</b></div><div><span>Tiền mặt</span><b>{stats.cash} đơn</b></div><div><span>Chuyển khoản</span><b>{stats.bank} đơn</b></div></div>
      <Card title="Danh sách đơn hàng" subtitle={`${items.length} kết quả`} action={<form className="compact-search" onSubmit={(event) => { event.preventDefault(); setSubmitted(query.trim()); }}><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Mã đơn, khách hàng, nhân viên..." /><button>Tìm</button></form>}>
        {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> : items.length ? <OrdersTable items={items} onOpen={setOrderId} /> : <EmptyState title="Không tìm thấy đơn hàng" description="Hãy thử một từ khóa khác." />}
      </Card>
      {orderId && <OrderDetail orderId={orderId} token={token} onClose={() => setOrderId(null)} />}
    </div>
  );
}

function ProductForm({ item, token, onClose, onSaved }) {
  const [form, setForm] = useState(item || { product_id: "", name: "", category: "", price: 0, stock: 0, reorder_level: 10 });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      await apiRequest(item ? `/admin/products/${encodeURIComponent(item.product_id)}` : "/admin/products", { token, method: item ? "PUT" : "POST", body: { ...form, price: Number(form.price), stock: Number(form.stock), reorder_level: Number(form.reorder_level) } });
      onSaved(item ? "Đã cập nhật sản phẩm." : "Đã thêm sản phẩm mới.");
    } catch (requestError) { setError(requestError.message); } finally { setSaving(false); }
  };
  return <AdminModal title={item ? "Cập nhật sản phẩm" : "Thêm sản phẩm"} subtitle="Thay đổi được lưu trực tiếp vào SQL Server" onClose={onClose}><form className="admin-form" onSubmit={submit}>{error && <div className="form-error">{error}</div>}<label>Mã sản phẩm<input value={form.product_id} onChange={(event) => set("product_id", event.target.value)} disabled={Boolean(item)} placeholder="Để trống để hệ thống tự tạo" /></label><label>Tên sản phẩm<input required minLength="2" value={form.name} onChange={(event) => set("name", event.target.value)} /></label><div className="form-row"><label>Danh mục<input required value={form.category} onChange={(event) => set("category", event.target.value)} /></label><label>Giá bán<input required type="number" min="0" value={form.price} onChange={(event) => set("price", event.target.value)} /></label></div><div className="form-row"><label>Tồn kho<input required type="number" min="0" value={form.stock} onChange={(event) => set("stock", event.target.value)} /></label><label>Mức cảnh báo<input required type="number" min="0" value={form.reorder_level} onChange={(event) => set("reorder_level", event.target.value)} /></label></div><div className="form-actions"><button type="button" onClick={onClose}>Hủy</button><button className="admin-primary" disabled={saving}>{saving && <LoaderCircle className="spin" size={16} />}{item ? "Lưu thay đổi" : "Thêm sản phẩm"}</button></div></form></AdminModal>;
}

export function ProductsPage({ token, showToast }) {
  const [query, setQuery] = useState(""); const [editing, setEditing] = useState(undefined);
  const { data, loading, error, reload } = useRemote(`/admin/products?q=${encodeURIComponent(query)}`, token);
  const remove = async (item) => {
    if (!window.confirm(`Xóa sản phẩm ${item.name}? Sản phẩm đã có giao dịch sẽ được hệ thống bảo vệ.`)) return;
    try { await apiRequest(`/admin/products/${encodeURIComponent(item.product_id)}`, { token, method: "DELETE" }); showToast("Đã xóa sản phẩm."); reload(); } catch (requestError) { showToast(requestError.message); }
  };
  const saved = (message) => { setEditing(undefined); showToast(message); reload(); };
  return <div className="admin-stack"><PageHeader eyebrow="QUẢN LÝ DANH MỤC" title="Sản phẩm" description="Giá, tồn kho và số lượng bán đều lấy từ cơ sở dữ liệu." actions={<button className="admin-primary" onClick={() => setEditing(null)}><Plus size={17} /> Thêm sản phẩm</button>} /><div className="list-toolbar"><div><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm theo mã, tên hoặc danh mục..." /></div><span>{data?.items?.length || 0} sản phẩm</span></div><Card title="Danh sách sản phẩm">{loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Sản phẩm</th><th>Danh mục</th><th>Giá bán</th><th>Tồn kho</th><th>Đã bán</th><th>Thao tác</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.product_id}><td><div className="table-entity"><i><Package size={18} /></i><div><b>{item.name}</b><small>{item.product_id}</small></div></div></td><td>{item.category}</td><td><b>{money(item.price)}</b></td><td><span className={item.stock <= item.reorder_level ? "stock-number low" : "stock-number"}>{item.stock}</span><small>Mức cảnh báo: {item.reorder_level}</small></td><td>{number(item.sold_quantity)}</td><td><div className="table-actions"><button onClick={() => setEditing(item)} title="Sửa"><Pencil size={16} /></button><button className="danger" onClick={() => remove(item)} title="Xóa"><Trash2 size={16} /></button></div></td></tr>)}</tbody></table></div>}</Card>{editing !== undefined && <ProductForm item={editing} token={token} onClose={() => setEditing(undefined)} onSaved={saved} />}</div>;
}

function CustomerForm({ item, token, onClose, onSaved }) {
  const [form, setForm] = useState(item || { customer_id: "", name: "", contact_name: "", phone: "", tier: "Standard", customer_status: "Active" });
  const [saving, setSaving] = useState(false); const [error, setError] = useState("");
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event) => { event.preventDefault(); setSaving(true); setError(""); try { await apiRequest(item ? `/admin/customers/${encodeURIComponent(item.customer_id)}` : "/admin/customers", { token, method: item ? "PUT" : "POST", body: form }); onSaved(item ? "Đã cập nhật khách hàng." : "Đã thêm khách hàng."); } catch (requestError) { setError(requestError.message); } finally { setSaving(false); } };
  return <AdminModal title={item ? "Cập nhật khách hàng" : "Thêm khách hàng"} subtitle="Hồ sơ phục vụ tra cứu và lịch sử mua hàng" onClose={onClose}><form className="admin-form" onSubmit={submit}>{error && <div className="form-error">{error}</div>}<label>Mã khách hàng<input value={form.customer_id} onChange={(event) => set("customer_id", event.target.value)} disabled={Boolean(item)} placeholder="Để trống để hệ thống tự tạo" /></label><label>Tên khách hàng<input required value={form.name} onChange={(event) => set("name", event.target.value)} /></label><div className="form-row"><label>Người liên hệ<input value={form.contact_name || ""} onChange={(event) => set("contact_name", event.target.value)} /></label><label>Số điện thoại<input value={form.phone || ""} onChange={(event) => set("phone", event.target.value)} /></label></div><div className="form-row"><label>Hạng khách hàng<select value={form.tier} onChange={(event) => set("tier", event.target.value)}><option>Standard</option><option>Thân thiết</option><option>VIP</option><option>Doanh nghiệp</option></select></label><label>Trạng thái<select value={form.customer_status} onChange={(event) => set("customer_status", event.target.value)}><option value="Active">Hoạt động</option><option value="Inactive">Ngừng hoạt động</option></select></label></div><div className="form-actions"><button type="button" onClick={onClose}>Hủy</button><button className="admin-primary" disabled={saving}>{item ? "Lưu thay đổi" : "Thêm khách hàng"}</button></div></form></AdminModal>;
}

export function CustomersPage({ token, showToast }) {
  const [query, setQuery] = useState(""); const [editing, setEditing] = useState(undefined);
  const { data, loading, error, reload } = useRemote(`/admin/customers?q=${encodeURIComponent(query)}`, token);
  const remove = async (item) => { if (!window.confirm(`Xóa khách hàng ${item.name}?`)) return; try { await apiRequest(`/admin/customers/${encodeURIComponent(item.customer_id)}`, { token, method: "DELETE" }); showToast("Đã xóa khách hàng."); reload(); } catch (requestError) { showToast(requestError.message); } };
  const saved = (message) => { setEditing(undefined); showToast(message); reload(); };
  return <div className="admin-stack"><PageHeader eyebrow="HỒ SƠ KHÁCH HÀNG" title="Khách hàng" description="Số đơn và tổng chi tiêu được tính từ lịch sử bán hàng thật." actions={<button className="admin-primary" onClick={() => setEditing(null)}><UserPlus size={17} /> Thêm khách hàng</button>} /><div className="list-toolbar"><div><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tên, mã, người liên hệ hoặc số điện thoại..." /></div><span>{data?.items?.length || 0} khách hàng</span></div><Card title="Danh sách khách hàng">{loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Khách hàng</th><th>Liên hệ</th><th>Hạng</th><th>Số đơn</th><th>Tổng chi tiêu</th><th>Thao tác</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.customer_id}><td><div className="table-entity"><span className="customer-avatar">{item.name[0]}</span><div><b>{item.name}</b><small>{item.customer_id}</small></div></div></td><td>{item.contact_name || "—"}<small>{item.phone || "Chưa có SĐT"}</small></td><td><span className="customer-tier">{item.tier}</span></td><td>{item.order_count}</td><td><b>{money(item.total_spent)}</b></td><td><div className="table-actions"><button onClick={() => setEditing(item)}><Pencil size={16} /></button><button className="danger" onClick={() => remove(item)}><Trash2 size={16} /></button></div></td></tr>)}</tbody></table></div>}</Card>{editing !== undefined && <CustomerForm item={editing} token={token} onClose={() => setEditing(undefined)} onSaved={saved} />}</div>;
}

function InventoryForm({ products, token, onClose, onSaved }) {
  const [form, setForm] = useState({ product_id: products[0]?.product_id || "", quantity_change: 1, reason: "" }); const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
  const submit = async (event) => { event.preventDefault(); setSaving(true); setError(""); try { await apiRequest("/admin/inventory/adjustments", { token, method: "POST", body: { ...form, quantity_change: Number(form.quantity_change) } }); onSaved("Đã cập nhật tồn kho và ghi lịch sử điều chỉnh."); } catch (requestError) { setError(requestError.message); } finally { setSaving(false); } };
  return <AdminModal title="Điều chỉnh tồn kho" subtitle="Mỗi thay đổi đều tạo một bản ghi StockMovements" onClose={onClose}><form className="admin-form" onSubmit={submit}>{error && <div className="form-error">{error}</div>}<label>Sản phẩm<select value={form.product_id} onChange={(event) => setForm({ ...form, product_id: event.target.value })}>{products.map((item) => <option key={item.product_id} value={item.product_id}>{item.name} ({item.stock} còn lại)</option>)}</select></label><label>Số lượng thay đổi<input type="number" required value={form.quantity_change} onChange={(event) => setForm({ ...form, quantity_change: event.target.value })} /><small>Dùng số dương để nhập thêm, số âm để xuất bớt.</small></label><label>Lý do<textarea required minLength="3" value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} placeholder="Ví dụ: Kiểm kê thực tế, nhập hàng mới..." /></label><div className="form-actions"><button type="button" onClick={onClose}>Hủy</button><button className="admin-primary" disabled={saving}>Lưu điều chỉnh</button></div></form></AdminModal>;
}

export function InventoryPage({ token, showToast }) {
  const { data, loading, error, reload } = useRemote("/admin/inventory", token); const products = useRemote("/admin/products", token); const [open, setOpen] = useState(false);
  if (loading) return <LoadingState />; if (error) return <ErrorState message={error} onRetry={reload} />;
  const summary = data.summary;
  return <div className="admin-stack"><PageHeader eyebrow="VẬN HÀNH KHO" title="Tồn kho" description="Cảnh báo dựa trên Stock và ReorderLevel của từng sản phẩm." actions={<button className="admin-primary" onClick={() => setOpen(true)}><ArrowLeftRight size={17} /> Điều chỉnh kho</button>} /><div className="real-metric-grid"><Metric icon={Boxes} label="Tổng mặt hàng" value={number(summary.total_products)} note="Sản phẩm trong danh mục" /><Metric icon={PackageCheck} label="Đủ hàng" value={number(summary.healthy_count)} note="Trên mức cảnh báo" tone="green" /><Metric icon={TriangleAlert} label="Sắp hết" value={number(summary.low_count)} note="Cần bổ sung" tone="orange" /><Metric icon={PackageX} label="Hết hàng" value={number(summary.out_count)} note="Cần xử lý ngay" tone="violet" /></div><Card title="Sản phẩm cần chú ý" subtitle="Ưu tiên sản phẩm đã hết hàng">{data.alerts.length ? <div className="inventory-alerts">{data.alerts.map((item) => <div key={item.product_id}><i className={item.stock === 0 ? "out" : "low"}><PackagePlus size={19} /></i><div><b>{item.name}</b><span>{item.product_id} · {item.category}</span></div><strong>{item.stock} còn lại</strong><small>Mức cảnh báo {item.reorder_level}</small></div>)}</div> : <EmptyState icon={PackageCheck} title="Tồn kho đang ổn định" description="Không có sản phẩm nào dưới mức cảnh báo." />}</Card>{open && <InventoryForm products={products.data?.items || []} token={token} onClose={() => setOpen(false)} onSaved={(message) => { setOpen(false); showToast(message); reload(); products.reload(); }} />}</div>;
}

function UserForm({ roles, token, onClose, onSaved }) {
  const [form, setForm] = useState({ full_name: "", username: "", password: "", role_id: "Sales" }); const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
  const submit = async (event) => { event.preventDefault(); setSaving(true); setError(""); try { await apiRequest("/admin/users", { token, method: "POST", body: form }); onSaved(); } catch (requestError) { setError(requestError.message); } finally { setSaving(false); } };
  return <AdminModal title="Cấp tài khoản" subtitle="Admin có thể tạo tài khoản và chọn đúng vai trò" onClose={onClose}><form className="admin-form" onSubmit={submit}>{error && <div className="form-error">{error}</div>}<label>Họ và tên<input required minLength="2" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} /></label><label>Tên đăng nhập<input required minLength="3" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label><label>Mật khẩu ban đầu<input type="password" required minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label><label>Vai trò<select value={form.role_id} onChange={(event) => setForm({ ...form, role_id: event.target.value })}>{roles.map((role) => <option key={role.role_id} value={role.role_id}>{role.role_name} ({role.role_id})</option>)}</select></label><div className="form-actions"><button type="button" onClick={onClose}>Hủy</button><button className="admin-primary" disabled={saving}>Tạo tài khoản</button></div></form></AdminModal>;
}

export function UsersPage({ token, showToast, currentUser }) {
  const { data, loading, error, reload } = useRemote("/admin/users", token); const [open, setOpen] = useState(false);
  const patchUser = async (userId, body, message) => { try { await apiRequest(`/admin/users/${userId}`, { token, method: "PATCH", body }); showToast(message); reload(); } catch (requestError) { showToast(requestError.message); } };
  const activeAdminCount = data?.items.filter((item) => item.role_id === "Admin" && item.account_status === "Active").length || 0;
  return <div className="admin-stack"><PageHeader eyebrow="TÀI KHOẢN HỆ THỐNG" title="Người dùng và vai trò" description="Danh sách chỉ hiển thị những tài khoản thực đã tạo trong SQL Server." actions={<button className="admin-primary" onClick={() => setOpen(true)}><UserPlus size={17} /> Cấp tài khoản</button>} /><Card title="Danh sách tài khoản" subtitle={data ? `${data.items.length} tài khoản` : "Đang tải"}>{loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Người dùng</th><th>Tên đăng nhập</th><th>Vai trò</th><th>Trạng thái</th><th>Đăng nhập gần nhất</th><th>Thao tác</th></tr></thead><tbody>{data.items.map((item) => {
        const isCurrentUser = item.user_id === currentUser?.UserID;
        const isLastActiveAdmin = item.role_id === "Admin" && item.account_status === "Active" && activeAdminCount === 1;
        const roleLocked = isCurrentUser || isLastActiveAdmin;
        return <tr key={item.user_id}><td><div className="table-entity"><span className="customer-avatar">{item.full_name.slice(-1)}</span><div><b>{item.full_name}</b><small>Tạo {dateTime(item.created_at)}</small></div></div></td><td>{item.username}</td><td><select className="inline-select" value={item.role_id} disabled={roleLocked} title={roleLocked ? "Không thể hạ quyền tài khoản Admin đang dùng hoặc Admin cuối cùng." : "Thay đổi vai trò"} onChange={(event) => patchUser(item.user_id, { role_id: event.target.value }, "Đã cập nhật vai trò.")}>{data.roles.map((role) => <option key={role.role_id}>{role.role_id}</option>)}</select></td><td><PaidBadge value={item.account_status === "Active" ? "Đang hoạt động" : "Đã khóa"} /></td><td>{dateTime(item.last_login_at)}</td><td><button className="icon-action" disabled={isCurrentUser || isLastActiveAdmin} title={isLastActiveAdmin ? "Không thể khóa Admin cuối cùng." : ""} onClick={() => patchUser(item.user_id, { account_status: item.account_status === "Active" ? "Locked" : "Active" }, item.account_status === "Active" ? "Đã khóa tài khoản." : "Đã mở khóa tài khoản.")}>{item.account_status === "Active" ? <Lock size={16} /> : <LockOpen size={16} />}</button></td></tr>;
      })}</tbody></table></div>}</Card>{open && data && <UserForm roles={data.roles} token={token} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); showToast("Đã tạo tài khoản mới."); reload(); }} />}</div>;
}

export function SettingsPage({ token, showToast }) {
  const { data, loading, error, reload } = useRemote("/admin/settings", token); const [form, setForm] = useState(null); const [saving, setSaving] = useState(false);
  useEffect(() => { if (data?.settings) setForm(data.settings); }, [data]);
  if (error) return <ErrorState message={error} onRetry={reload} />; if (loading || !form) return <LoadingState />;
  const submit = async (event) => { event.preventDefault(); setSaving(true); try { await apiRequest("/admin/settings", { token, method: "PUT", body: form }); showToast("Đã lưu cấu hình doanh nghiệp."); reload(); } catch (requestError) { showToast(requestError.message); } finally { setSaving(false); } };
  return <div className="admin-stack"><PageHeader eyebrow="THIẾT LẬP THỰC TẾ" title="Cấu hình hệ thống" description="Chỉ giữ lại các thiết lập có dữ liệu và có tác dụng thật." /><div className="settings-layout"><Card title="Thông tin doanh nghiệp" subtitle="Dùng cho hóa đơn và nhận diện hệ thống"><form className="admin-form embedded" onSubmit={submit}><label>Tên đơn vị<input required value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} /></label><div className="form-row"><label>Số điện thoại<input value={form.company_phone} onChange={(event) => setForm({ ...form, company_phone: event.target.value })} /></label><label>Mã số thuế<input value={form.tax_code} onChange={(event) => setForm({ ...form, tax_code: event.target.value })} /></label></div><label>Địa chỉ<textarea value={form.company_address} onChange={(event) => setForm({ ...form, company_address: event.target.value })} /></label><div className="form-actions"><button className="admin-primary" disabled={saving}>{saving ? "Đang lưu..." : "Lưu cấu hình"}</button></div></form></Card><div className="settings-side"><Card title="Tình trạng hệ thống"><div className="system-status"><span><Database /><div><b>SQL Server</b><small>{data.system.database}</small></div><CheckCircle2 /></span><span><Clock3 /><div><b>Kiểm tra gần nhất</b><small>{dateTime(data.system.checked_at)}</small></div></span><span><ShieldCheck /><div><b>Nhật ký hoạt động</b><small>{number(data.system.activity_count)} bản ghi</small></div></span></div></Card><div className="settings-note"><Building2 /><div><b>Cài đặt gọn, có mục đích</b><p>Khuyến mãi và thông báo sẽ được quản lý ở màn nghiệp vụ riêng khi triển khai giai đoạn Sale, thay vì đặt các thẻ không hoạt động tại đây.</p></div></div></div></div></div>;
}

export function AdminPageRouter({ page, token, user, onNavigate, showToast }) {
  if (page === "overview") return <AdminOverview token={token} onNavigate={onNavigate} />;
  if (page === "revenue") return <RevenuePage token={token} />;
  if (page === "orders") return <OrdersPage token={token} />;
  if (page === "products") return <ProductsPage token={token} showToast={showToast} />;
  if (page === "customers") return <CustomersPage token={token} showToast={showToast} />;
  if (page === "inventory") return <InventoryPage token={token} showToast={showToast} />;
  if (page === "users") return <UsersPage token={token} showToast={showToast} currentUser={user} />;
  if (page === "settings") return <SettingsPage token={token} showToast={showToast} />;
  return <EmptyState title="Không tìm thấy trang" description="Mục điều hướng không hợp lệ." />;
}

export function AdminHeaderTools({ token, onNavigate }) {
  const [mode, setMode] = useState(null); const [query, setQuery] = useState(""); const [results, setResults] = useState([]); const [notifications, setNotifications] = useState([]); const [loading, setLoading] = useState(false);
  useEffect(() => { apiRequest("/admin/notifications", { token }).then((data) => setNotifications(data.items)).catch(() => setNotifications([])); }, [token]);
  const openNotifications = async () => { setMode(mode === "notifications" ? null : "notifications"); if (mode !== "notifications") { setLoading(true); try { const data = await apiRequest("/admin/notifications", { token }); setNotifications(data.items); } finally { setLoading(false); } } };
  const search = async (event) => { event.preventDefault(); if (query.trim().length < 2) return; setLoading(true); try { const data = await apiRequest(`/admin/search?q=${encodeURIComponent(query.trim())}`, { token }); setResults(data.items); } finally { setLoading(false); } };
  const go = (target) => { onNavigate(target); setMode(null); setQuery(""); };
  return <div className="admin-header-tools"><button className="header-icon" aria-label="Tìm kiếm" onClick={() => setMode(mode === "search" ? null : "search")}><Search size={19} /></button><button className="header-icon notification" aria-label="Thông báo" onClick={openNotifications}><Bell size={19} />{notifications.length > 0 && <i />}</button>{mode && <div className="header-popover">{mode === "search" ? <><form onSubmit={search}><Search size={18} /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm sản phẩm, khách hàng, đơn..." /><button>Tìm</button></form><div className="popover-list">{loading ? <LoadingState label="Đang tìm..." /> : results.length ? results.map((item) => <button key={`${item.target}-${item.result_id}`} onClick={() => go(item.target)}><span>{item.result_type}</span><div><b>{item.title}</b><small>{item.subtitle}</small></div><ChevronRight size={17} /></button>) : <EmptyState icon={Search} title="Tìm kiếm toàn hệ thống" description="Nhập ít nhất 2 ký tự để tra cứu." />}</div></> : <><div className="popover-title"><div><b>Thông báo</b><span>Dữ liệu mới nhất từ hệ thống</span></div><button onClick={() => setMode(null)}><X size={17} /></button></div><div className="popover-list">{loading ? <LoadingState /> : notifications.length ? notifications.map((item) => <button key={item.notification_id} onClick={() => go(item.target)} className={item.priority ? "important" : ""}><i>{item.priority ? <TriangleAlert size={17} /> : <ShoppingBag size={17} />}</i><div><b>{item.title}</b><small>{item.message}</small></div><ChevronRight size={17} /></button>) : <EmptyState icon={Bell} title="Không có thông báo" description="Hệ thống chưa ghi nhận vấn đề cần chú ý." />}</div></>}</div>}</div>;
}
