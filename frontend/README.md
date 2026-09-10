<!-- SPDX-License-Identifier: MIT -->

# DX-Lab Core Frontend

Thư mục này chỉ chứa giao diện React/Vite và lớp gọi HTTP. Frontend không kết
nối trực tiếp SQL Server và không tự quyết định quyền quản trị.

## Bố cục

```text
frontend/
├── src/
│   ├── admin/      # trang và style dành cho quản trị viên
│   ├── config/     # menu, cổng đăng nhập và permission hiển thị
│   ├── hooks/      # TanStack Query hooks dùng lại giữa các trang
│   ├── api.js      # một điểm cấu hình URL và xử lý lỗi API
│   ├── App.jsx     # shell đăng nhập, layout và trang nhân viên
│   ├── main.jsx    # React providers
│   └── styles.css
├── .env.example
├── package.json
├── package-lock.json
└── vite.config.js
```

## Chạy riêng frontend

```powershell
npm ci
npm run dev
```

Chỉ thay `VITE_API_URL` trong `.env` cục bộ. Không commit `.env`, `node_modules`,
`dist` hoặc cache Vite. Giá bán, tồn kho, khách hàng và đơn hàng phải đến từ API.
