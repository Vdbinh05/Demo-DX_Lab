# Nguồn mở tham khảo cho DX-Lab Core

Tài liệu này ghi lại các dự án mã nguồn mở được dùng làm tài liệu thiết kế và kỹ thuật cho giao diện phân quyền của DX-Lab Core.

## 1. Full Stack FastAPI Template

- Repository: <https://github.com/fastapi/full-stack-fastapi-template>
- Giấy phép: MIT
- Phần tham khảo: kiến trúc React + FastAPI, màn hình đăng nhập, dashboard quản trị, luồng xác thực JWT và cách tách quyền quản trị.
- Cách áp dụng: DX-Lab Core giữ FastAPI làm backend xác thực, React/Vite làm frontend và tách khu vực làm việc theo vai trò. Mã giao diện trong dự án này được viết lại cho nghiệp vụ bán hàng và SQL Server.

## 2. React Router

- Repository: <https://github.com/remix-run/react-router>
- Ví dụ xác thực: <https://github.com/remix-run/react-router/tree/main/examples/auth>
- Giấy phép: MIT
- Phần tham khảo: protected route, chuyển hướng sau đăng nhập và nguyên tắc kiểm tra quyền trước khi hiển thị màn hình.
- Cách áp dụng: bản frontend hiện tại có một lớp điều hướng tập trung (`PageRouter`) và kiểm tra permission trước khi render. Khi backend JWT hoàn thiện, có thể chuyển lớp này sang React Router mà không thay đổi ma trận quyền.

## 3. Material UI Dashboard Template

- Repository: <https://github.com/mui/material-ui>
- Dashboard template: <https://github.com/mui/material-ui/tree/master/docs/data/material/getting-started/templates/dashboard>
- Giấy phép: MIT
- Phần tham khảo: bố cục sidebar, top bar, thẻ KPI, bảng quản trị và dashboard responsive.
- Cách áp dụng: DX-Lab Core tự xây dựng component và CSS riêng, không chép nguyên template hoặc thêm Material UI vào dependency.

## 4. python-dotenv

- Repository: <https://github.com/theskumar/python-dotenv>
- Giấy phép: BSD-3-Clause
- Phần sử dụng: đọc các biến kết nối SQL Server từ `backend/.env` trong môi trường phát triển.
- Cách áp dụng: FastAPI nạp tệp `.env` nằm cạnh `backend/main.py`; biến môi trường của hệ điều hành vẫn được ưu tiên và tệp chứa mật khẩu thật không được commit.

## 5. React-admin

- Repository: <https://github.com/marmelab/react-admin>
- Tài liệu tính năng: <https://github.com/marmelab/react-admin/blob/master/docs/Features.md>
- Giấy phép: MIT (phần lõi mã nguồn mở).
- Phần tham khảo: bố cục danh sách quản trị, tìm kiếm theo nhiều tiêu chí, bảng dữ liệu, trang xem chi tiết và phản hồi loading/error/empty.
- Cách áp dụng: DX-Lab Core tự viết component React và CSS theo nhận diện riêng; không cài hoặc sao chép nguyên React-admin.

## 6. shadcn/ui

- Repository: <https://github.com/shadcn-ui/ui>
- Giấy phép: MIT.
- Phần tham khảo: cách ghép dashboard từ sidebar, card, chart, table và form; ưu tiên màu ngữ nghĩa, trạng thái focus và khả năng truy cập.
- Cách áp dụng: giao diện Admin dùng các khối nhỏ có một mục đích rõ ràng, loại bỏ thẻ cài đặt không hoạt động và giữ hệ component CSS sẵn có của dự án.

## 7. PyJWT

- Repository: <https://github.com/jpadilla/pyjwt>
- Giấy phép: MIT.
- Phần sử dụng: ký và kiểm tra access token giữa React và FastAPI.
- Cách áp dụng: token chỉ nhận diện phiên đăng nhập; mỗi API Admin vẫn tải lại trạng thái và `RoleID` từ SQL Server trước khi cho phép truy cập.

## Nguyên tắc sử dụng

- Chỉ sử dụng repository có giấy phép rõ ràng.
- Không sao chép nguyên một sản phẩm hoặc xóa thông tin bản quyền của tác giả gốc.
- Ghi nguồn và giấy phép khi áp dụng thêm thư viện hoặc đoạn mã đáng kể.
- Không lấy mã nguồn không rõ tác giả/giấy phép từ bài viết hoặc trang chia sẻ ngẫu nhiên.
- Frontend chỉ kiểm soát trải nghiệm; backend là nơi bắt buộc phải kiểm tra quyền thật.

## Phạm vi của bản dựng này

- Lựa chọn cổng đăng nhập Nhân viên hoặc Quản trị viên.
- Đối chiếu lựa chọn cổng với `RoleID` do FastAPI trả về.
- `Sales`, `Warehouse`, `Employee` thuộc cổng Nhân viên.
- Chỉ `Admin` thuộc cổng Quản trị viên; `CEO` và `Manager` chưa được tự động cấp quyền Admin.
- Tài khoản đăng ký công khai luôn gửi `role_id: "Sales"`.
- Nhân viên có khu vực bán hàng, sản phẩm, khuyến mãi, đơn cá nhân và tra cứu khách hàng.
- Quản trị viên có báo cáo doanh thu, đơn hàng, sản phẩm, khách hàng, kho, tài khoản và cấu hình.
- Dashboard Admin lấy số liệu trực tiếp từ SQL Server; không dùng các KPI mẫu trong `data.js`.
- Tìm kiếm toàn hệ thống, thông báo tồn kho, chi tiết đơn, CRUD sản phẩm/khách hàng, điều chỉnh kho và cấu hình doanh nghiệp đều gọi API thật.

> Ghi chú bảo mật: lớp phân quyền frontend không thay thế RBAC ở FastAPI. API thêm, sửa, xóa và xem doanh thu phải kiểm tra JWT cùng quyền của tài khoản ở backend.
