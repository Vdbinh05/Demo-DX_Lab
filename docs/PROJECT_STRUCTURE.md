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
