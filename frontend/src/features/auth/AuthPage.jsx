// SPDX-License-Identifier: MIT
import { useState } from "react";
import {
  BadgeCheck,
  CircleAlert,
  Eye,
  EyeOff,
  Info,
  LockKeyhole,
  LogIn,
  ShieldCheck,
  ShoppingBag,
  TrendingUp,
  UserRound,
  X,
} from "lucide-react";

import { API_BASE_URL } from "../../api";
import { portalConfig, portalFromRole } from "../../config/navigation";


const LOGIN_API_URL = `${API_BASE_URL}/login`;
const REGISTER_API_URL = `${API_BASE_URL}/register`;


function LogoMark() {
  return <span className="logo-mark"><span>DX</span></span>;
}


function AuthModal({ title, onClose, children }) {
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><section className="modal narrow" role="dialog" aria-modal="true" aria-label={title}><div className="modal-header"><div><span>DX-LAB CORE</span><h2>{title}</h2></div><button onClick={onClose} aria-label="Đóng"><X aria-hidden="true" /></button></div>{children}</section></div>;
}


function apiErrorMessage(data, fallback) {
  const detail = data?.message ?? data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item?.msg).filter(Boolean).join("; ") || fallback;
  return fallback;
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

  return <AuthModal title="Tạo tài khoản nhân viên" onClose={onClose}>{success ? <div className="success-state"><span><BadgeCheck size={34} aria-hidden="true" /></span><h3>Tạo tài khoản thành công</h3><p>Tài khoản <b>{form.username.trim()}</b> đã được lưu với vai trò <b>Sales</b>.</p><button className="primary-button" onClick={() => onUseUsername(form.username.trim())}>Đăng nhập ngay</button></div> : <form onSubmit={submit}><div className="register-policy"><ShieldCheck size={19} aria-hidden="true" /><span>Tài khoản đăng ký công khai luôn là nhân viên. Admin chỉ có thể được cấp bởi quản trị viên.</span></div><div className="form-grid"><label className="input-group full-span"><span>Họ và tên</span><input value={form.fullName} onChange={(event) => update("fullName", event.target.value)} placeholder="Nguyễn Văn A" maxLength={100} /></label><label className="input-group full-span"><span>Tên đăng nhập</span><input value={form.username} onChange={(event) => update("username", event.target.value)} placeholder="nguyenvana" maxLength={50} autoComplete="username" /></label><label className="input-group"><span>Mật khẩu</span><input type="password" value={form.password} onChange={(event) => update("password", event.target.value)} placeholder="Tối thiểu 8 ký tự" autoComplete="new-password" /></label><label className="input-group"><span>Xác nhận mật khẩu</span><input type="password" value={form.confirmPassword} onChange={(event) => update("confirmPassword", event.target.value)} placeholder="Nhập lại mật khẩu" autoComplete="new-password" /></label></div>{error && <div className="form-alert compact" role="alert"><CircleAlert size={17} aria-hidden="true" />{error}</div>}<div className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button type="submit" className="primary-button" disabled={loading}>{loading ? "Đang tạo..." : "Tạo tài khoản"}</button></div></form>}</AuthModal>;
}


export default function LoginScreen({ onAuthenticated }) {
  const [portal, setPortal] = useState("employee");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [registerOpen, setRegisterOpen] = useState(false);
  const selectedPortal = portalConfig[portal];
  const PortalIcon = portal === "admin" ? ShieldCheck : BadgeCheck;

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
        body: JSON.stringify({ username: username.trim(), password, portal }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok || !data?.success || !data?.user) {
        setError("Đăng nhập thất bại.");
        return;
      }
      const accountPortal = portalFromRole(data.user.RoleID);
      if (!accountPortal || accountPortal !== portal) {
        setError("Đăng nhập thất bại.");
        return;
      }
      onAuthenticated(data.user, accountPortal, data.access_token);
    } catch {
      setError("Không thể kết nối FastAPI tại cổng 8000. Hãy kiểm tra backend và cấu hình VITE_API_URL.");
    } finally {
      setLoading(false);
    }
  };

  return <main className="auth-page"><div className="auth-orb auth-orb-one" /><div className="auth-orb auth-orb-two" /><section className="auth-shell"><div className="auth-story"><div className="auth-brand"><LogoMark /><div><strong>DX-LAB CORE</strong><span>Digital Commerce Workspace</span></div></div><div className="story-content"><span className="story-kicker">MỘT HỆ THỐNG · ĐÚNG QUYỀN HẠN</span><h1>Không gian làm việc rõ ràng cho từng vai trò.</h1><p>Nhân viên tập trung bán hàng. Quản trị viên kiểm soát dữ liệu, vận hành và doanh thu trên một nền tảng thống nhất.</p><div className="story-preview"><div className="preview-head"><span><i /> Tổng quan vận hành</span><small>Dữ liệu trực tiếp</small></div><div className="preview-grid"><div><TrendingUp aria-hidden="true" /><span>Doanh thu</span><b>Theo thời gian thực</b></div><div><ShoppingBag aria-hidden="true" /><span>Đơn hàng</span><b>Truy xuất đầy đủ</b></div></div><div className="preview-chart">{[36, 52, 44, 67, 61, 82, 76, 94].map((height, index) => <i key={index} style={{ height: `${height}%` }} />)}</div></div></div><div className="story-trust"><span><ShieldCheck size={17} aria-hidden="true" /> Phân quyền theo SQL Server</span><span><LockKeyhole size={17} aria-hidden="true" /> Mật khẩu được mã hóa</span></div></div><div className="auth-panel"><div className="auth-form-wrap"><div className="auth-heading"><span className="mobile-brand"><LogoMark /> DX-LAB CORE</span><p className="eyebrow">CỔNG ĐĂNG NHẬP</p><h2>Chào mừng trở lại</h2><p>Chọn khu vực làm việc, sau đó đăng nhập bằng tài khoản được cấp.</p></div><div className="portal-picker" role="radiogroup" aria-label="Loại tài khoản">{Object.entries(portalConfig).map(([key, config]) => { const OptionIcon = key === "admin" ? ShieldCheck : BadgeCheck; return <button type="button" role="radio" aria-checked={portal === key} className={`portal-option ${portal === key ? "selected" : ""}`} key={key} onClick={() => { setPortal(key); setError(""); }}><span className="portal-icon"><OptionIcon aria-hidden="true" /></span><span><b>{config.label}</b><small>{config.shortLabel}</small></span><i className="radio-dot" /></button>; })}</div><div className={`portal-note ${portal}`}><PortalIcon size={18} aria-hidden="true" /><span>{selectedPortal.description}</span></div><form className="auth-form" onSubmit={handleLogin}>{error && <div className="form-alert" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{error}</span></div>}<label className="input-group"><span>Tên đăng nhập</span><div className="input-shell"><UserRound size={19} aria-hidden="true" /><input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Nhập tên đăng nhập" autoComplete="username" /></div></label><label className="input-group"><span>Mật khẩu</span><div className="input-shell"><LockKeyhole size={19} aria-hidden="true" /><input type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Nhập mật khẩu" autoComplete="current-password" /><button type="button" className="input-action" onClick={() => setShowPassword((current) => !current)} aria-label="Hiện hoặc ẩn mật khẩu">{showPassword ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}</button></div></label><div className="auth-options"><label><input type="checkbox" /> Ghi nhớ đăng nhập</label><button type="button">Quên mật khẩu?</button></div><button className="login-button" type="submit" disabled={loading}>{loading ? <span className="spinner" /> : <LogIn size={19} aria-hidden="true" />}{loading ? "Đang xác thực..." : `Đăng nhập với tư cách ${selectedPortal.label}`}</button></form>{portal === "employee" ? <div className="register-link">Chưa có tài khoản nhân viên?<button type="button" onClick={() => setRegisterOpen(true)}>Tạo tài khoản</button></div> : <div className="admin-account-note"><ShieldCheck size={16} aria-hidden="true" /><span>Tài khoản quản trị phải được hệ thống cấp, không tạo từ form đăng ký công khai.</span></div>}<div className="security-caption"><Info size={15} aria-hidden="true" />Lựa chọn ở trên không cấp quyền. Hệ thống vẫn kiểm tra vai trò thật trong SQL Server.</div></div></div></section>{registerOpen && <RegisterModal onClose={() => setRegisterOpen(false)} onUseUsername={(value) => { setUsername(value); setPortal("employee"); setRegisterOpen(false); }} />}</main>;
}
