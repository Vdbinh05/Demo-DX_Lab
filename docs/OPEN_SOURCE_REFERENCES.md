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

> Ghi chú bảo mật: lớp phân quyền frontend không thay thế RBAC ở FastAPI. API thêm, sửa, xóa và xem doanh thu phải kiểm tra JWT cùng quyền của tài khoản ở backend.
