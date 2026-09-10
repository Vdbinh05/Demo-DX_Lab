<!-- SPDX-License-Identifier: MIT -->

# Nguồn mở trong DX-Lab Core

Tài liệu này tách rõ hai khái niệm để nhóm có thể trình bày minh bạch trước ban
giám khảo: **thành phần được dùng trực tiếp** và **nguồn chỉ được nghiên cứu**.

## 1. Thành phần được sử dụng trực tiếp

### React Router

- Repository: <https://github.com/remix-run/react-router>
- Giấy phép: MIT.
- Mã được dùng qua package `react-router-dom`.
- Ứng dụng: URL thật cho từng khu vực như `/admin/overview` và
  `/employee/pos`, điều hướng sau đăng nhập và khôi phục đúng trang sau F5.

### TanStack Query

- Repository: <https://github.com/TanStack/query>
- Giấy phép: MIT.
- Mã được dùng qua package `@tanstack/react-query`.
- Ứng dụng: tải, cache, làm mới và đồng bộ sản phẩm, khách hàng, khuyến mãi,
  đơn cá nhân và dữ liệu quản trị từ API.

### TanStack Table

- Repository: <https://github.com/TanStack/table>
- Giấy phép: MIT.
- Mã được dùng qua package `@tanstack/react-table`.
- Ứng dụng: mô hình cột và render bảng đơn hàng quản trị; dữ liệu vẫn đến từ
  FastAPI và SQL Server.

### Recharts

- Repository: <https://github.com/recharts/recharts>
- Giấy phép: MIT.
- Mã được dùng qua package `recharts`.
- Ứng dụng: biểu đồ doanh thu theo tháng co giãn theo kích thước màn hình.

### FastAPI và hệ sinh thái backend

- FastAPI cung cấp router, dependency injection, validation và OpenAPI.
- Pydantic kiểm tra payload đầu vào.
- Uvicorn chạy ASGI server.
- pyodbc kết nối SQL Server với connection pooling.
- python-dotenv nạp cấu hình phát triển từ `backend/.env`.
- PyJWT ký và xác minh access token.

Danh sách phiên bản, giấy phép và liên kết nguồn đầy đủ nằm tại
`THIRD_PARTY_NOTICES.md`.

## 2. Nguồn được nghiên cứu, không sao chép nguyên khối

### Full Stack FastAPI Template

- Repository: <https://github.com/fastapi/full-stack-fastapi-template>
- Giấy phép: MIT.
- Nội dung nghiên cứu: cách phân lớp frontend/backend, xác thực và cấu hình.
- Phần DX-Lab Core vẫn được viết theo nghiệp vụ bán hàng và SQL Server riêng.

### Material UI Dashboard, React-admin và shadcn/ui

- Material UI: <https://github.com/mui/material-ui> — MIT.
- React-admin: <https://github.com/marmelab/react-admin> — MIT cho phần lõi.
- shadcn/ui: <https://github.com/shadcn-ui/ui> — MIT.
- Nội dung nghiên cứu: sidebar, KPI, bảng, trạng thái loading/error/empty và
  khả năng truy cập.
- Các package này không nằm trong `package.json`; giao diện hiện tại dùng CSS
  và component do nhóm viết.

## 3. Quy tắc khi bổ sung mã nguồn mở

1. Kiểm tra repository chính thức và giấy phép trước khi tải hoặc chép mã.
2. Ưu tiên cài dependency có phiên bản khóa thay vì chép tệp không rõ nguồn.
3. Nếu chỉnh sửa một đoạn mã được lấy trực tiếp, giữ bản quyền đầu tệp và ghi
   đường dẫn tệp, commit/tag nguồn, giấy phép và phần đã thay đổi.
4. Cập nhật `THIRD_PARTY_NOTICES.md`, tài liệu này và lockfile trong cùng commit.
5. Không đưa mã GPL/AGPL hoặc mã không có giấy phép vào dự án nếu chưa đánh giá
   tác động phân phối với cả nhóm.

## 4. Phạm vi bản thử nghiệm

SQL Server tiếp tục là cơ sở dữ liệu của bản nộp thử cho giảng viên. Việc đổi
sang PostgreSQL chỉ được xem xét khi đề chính thức tháng 10 yêu cầu; đó không
phải công việc của giai đoạn hiện tại.
