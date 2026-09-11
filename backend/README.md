<!-- SPDX-License-Identifier: MIT -->

# DX-Lab Core Backend

Thư mục này chỉ chứa FastAPI, nghiệp vụ máy chủ, kiểm tra quyền và tài nguyên
SQL Server. Không đặt component React, CSS hoặc package npm tại đây.

## Bố cục

```text
backend/
├── app/
│   ├── api/        # router tổng, dependency HTTP và endpoint theo nghiệp vụ
│   ├── core/       # cấu hình, mật khẩu và JWT
│   ├── database/   # kết nối, pooling và health check SQL Server
│   ├── repositories/ # truy vấn SQL Server theo miền nghiệp vụ
│   ├── schemas/    # request/response model dùng chung
│   ├── services/   # luật nghiệp vụ và điều phối transaction
│   └── main.py     # tạo FastAPI app và middleware
├── database/       # schema, seed và công cụ khởi tạo SQL Server (giữ nguyên)
├── tests/          # unit, API-contract và smoke test có hoàn nguyên dữ liệu
├── .env.example    # mẫu cấu hình, không chứa mật khẩu thật
├── main.py         # entry point tương thích `uvicorn main:app`
└── requirements.txt
```

Cách chia lớp `app/api`, `app/core` và router tổng được điều chỉnh từ Full
Stack FastAPI Template (MIT), khóa tại commit
`cb740b656d7a0a6c5e12c7bf8e50343ec94ee9c7`. Dự án chỉ sử dụng cách tổ chức;
toàn bộ hợp đồng API bán hàng và lớp SQL Server vẫn là của DX-Lab Core.

## Chạy riêng backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

## Năng lực API hiện tại

- Xác thực theo đúng cổng Admin/Nhân viên, chống dò tài khoản, giới hạn đăng
  nhập sai, phiên JWT có thể thu hồi, đăng xuất phía server và đổi mật khẩu.
- Catalog sản phẩm hỗ trợ từ khóa, khoảng giá, danh mục, tồn kho, phân trang
  và sắp xếp.
- Tạo đơn idempotent trong transaction; giá, tồn kho và khuyến mãi được kiểm
  tra lại tại server. API `/orders/preview` dùng chung service tính giá với
  bước thanh toán để giao diện không tự quyết định tổng tiền. Nếu tổng thực tế
  khác `expected_total_value`, backend trả `409` và không tạo đơn.
- Cập nhật thông tin sản phẩm không thể ghi đè tồn kho; tồn kho ban đầu và mọi
  điều chỉnh sau đó đều có bản ghi `StockMovements`.
- API bán hàng kiểm tra vai trò `Sales` tại server; quyền hiển thị ở React
  chỉ phục vụ trải nghiệm và không thay thế phân quyền backend.
- Nhân viên chỉ xem danh sách và chi tiết đơn do mình tạo.
- Admin quản lý sản phẩm, khách hàng, khuyến mãi, người dùng, cấu hình; xem
  báo cáo, chi tiết đơn, lịch sử khách, lịch sử kho, phiếu đề nghị nhập và
  nhật ký hoạt động.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Các smoke test `integration_*_smoke.py` trong `tests/` tạo dữ liệu tạm, xác
minh transaction rồi tự hoàn nguyên. Chỉ chạy chúng khi backend và SQL Server
đang hoạt động.

Sau khi cập nhật mã nguồn, chạy lại migration an toàn bằng:

```powershell
.\.venv\Scripts\python.exe database\init_database.py
```

Mọi thay đổi bảng phải viết theo kiểu chạy lại an toàn trong `database/schema.sql`.
Health check xác nhận 12 bảng và 81 cột nghiệp vụ trước khi nhận request.
Không sửa trực tiếp database mà bỏ qua migration. Không commit `.env`,
`.auth-secret`, `.venv`, dữ liệu thật hoặc file backup SQL Server.
