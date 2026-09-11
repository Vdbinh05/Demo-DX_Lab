<!-- SPDX-License-Identifier: MIT -->

# Quy ước cấu trúc dự án

## Ranh giới thư mục

| Phạm vi | Nơi đặt file | Không được đặt |
| --- | --- | --- |
| FastAPI, JWT, RBAC, SQL | `backend/` | JSX, CSS, npm package |
| React, CSS, gọi REST API | `frontend/` | câu lệnh SQL, mật khẩu DB |
| Thể lệ, kiến trúc, nguồn mở | `docs/` | code chạy production |
| Giấy phép dự án và dependency | thư mục gốc, `LICENSES/` | bí mật hoặc dữ liệu cá nhân |
| Script chạy cả hệ thống | thư mục gốc | logic nghiệp vụ |

## File cục bộ không đưa lên Git

- `backend/.env`: thông tin SQL Server của từng máy.
- `backend/.auth-secret`: khóa JWT phát sinh cho môi trường phát triển.
- `backend/.venv`: thư viện Python đã cài.
- `frontend/node_modules`: thư viện npm đã cài.
- `frontend/dist`: kết quả build, có thể tạo lại.

VS Code ẩn các mục này theo `.vscode/settings.json`. Khi cần chỉnh cấu hình,
dùng `backend/.env.example` và `frontend/.env.example` làm mẫu.

## Quy tắc cho nhóm ba người

1. Tạo branch ngắn theo chức năng và không sửa trực tiếp `main`.
2. Một pull request nên chỉ thuộc backend, frontend hoặc tài liệu; nếu thay đổi
   API xuyên suốt thì mô tả rõ request/response và migration SQL.
3. Chạy build frontend, unit test backend và smoke test liên quan trước khi gửi.
4. Dependency mới phải có giấy phép rõ ràng và được ghi vào hồ sơ nguồn mở.
5. Chỉ tạo release từ commit đã được cả nhóm chạy thử trên máy trình diễn.

## Luồng dữ liệu nghiệp vụ

Router chỉ nhận request và chuyển kết quả HTTP. Luật nghiệp vụ nằm trong
`backend/app/services`, truy vấn SQL trong `backend/app/repositories`, schema
Pydantic tại `backend/app/schemas`; cấu hình/bảo mật tại `backend/app/core`;
kết nối SQL Server tại `backend/app/database`. Migration trong `backend/database/schema.sql`
phải cộng thêm và chạy lặp an toàn để máy của từng thành viên nâng cấp mà không
xóa dữ liệu hiện có.

### Trách nhiệm từng lớp backend

```text
backend/app/
├── api/routes/       # URL, dependency quyền, commit/rollback và lỗi HTTP
├── services/         # luật nghiệp vụ, transaction flow và dữ liệu trả về
├── repositories/     # toàn bộ câu lệnh SQL Server theo từng miền
├── schemas/          # kiểm tra request/response bằng Pydantic
├── core/             # cấu hình, bảo mật và sinh mã nghiệp vụ
└── database/         # kết nối và chuyển bản ghi SQL thành dữ liệu JSON
```

Tên file trong `services/` và `repositories/` đi theo miền nghiệp vụ, ví dụ
`products.py`, `inventory.py`, `users.py`, `orders.py`. Route không được chứa
`SELECT`, `INSERT`, `UPDATE` hoặc `DELETE`; repository không được tạo
`HTTPException`. Báo cáo chỉ đọc được ghép kết quả ở service và không tự
`commit`.

### Luồng thanh toán chuẩn

```text
React POS
  -> POST /orders/preview (backend đọc giá, tồn kho và khuyến mãi hiện tại)
  -> người bán kiểm tra tổng tiền
  -> POST /orders kèm expected_total_value và idempotency_key
  -> service khóa các bản ghi liên quan và tính lại
  -> nếu tổng tiền thay đổi: trả 409, không tạo đơn
  -> nếu hợp lệ: lưu đơn + chi tiết + trừ kho + lịch sử kho + nhật ký
  -> commit một lần
```

Frontend không được tự quyết định giá cuối cùng. API cập nhật thông tin sản phẩm
không nhận trường `stock`; số lượng chỉ thay đổi qua nghiệp vụ tạo sản phẩm,
bán hàng hoặc điều chỉnh kho có lịch sử.

### Ma trận quyền đang hỗ trợ

| Nghiệp vụ | Admin | Sales | Warehouse |
| --- | --- | --- | --- |
| Quản trị tài khoản, sản phẩm và báo cáo | Có | Không | Không |
| Bán hàng, khách hàng, khuyến mãi và đơn cá nhân | Không | Có | Không |
| Đọc danh mục sản phẩm | Không qua catalog | Có | Có |

`CEO` và `Manager` có thể còn trong dữ liệu cũ nhưng không được cấp mới hoặc
đăng nhập cho tới khi nhóm thiết kế một luồng quyền cụ thể cho các vai trò đó.
