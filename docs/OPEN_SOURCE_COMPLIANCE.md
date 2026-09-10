<!-- SPDX-License-Identifier: MIT -->

# Kiểm tra tuân thủ phần mềm nguồn mở

Kết quả này đối chiếu bản local ngày 10/09/2026 với sáu tiêu chí PoF trong thể
lệ OLP Phần mềm nguồn mở 2026. Đây là kiểm tra kỹ thuật trước khi phát hành,
không thay thế quyết định chấm điểm của ban tổ chức.

| Tiêu chí PoF | Trạng thái local | Bằng chứng hoặc việc còn thiếu |
| --- | --- | --- |
| Kho mã nguồn Internet | Chờ công bố | GitHub public đã tồn tại; commit trên nhánh `codex/open-source-foundation` phải được push/merge để mã hiện tại truy cập được. |
| Giấy phép OSI-approved | Đạt | MIT trong `LICENSE`, mục đích giấy phép trong README, SPDX trong các tệp mã do nhóm viết. |
| Có bản phát hành | Chưa đạt | Chưa có tag hoặc GitHub Release. Cần tạo release phiên bản sau khi ba thành viên kiểm thử. |
| Build từ mã nguồn | Đạt cho bản Windows thử nghiệm | Có script cài đặt, lockfile, requirements và hướng dẫn chạy. SQL Server/ODBC vẫn là rủi ro nguồn đóng cho bài chính thức. |
| Thư viện và gói phụ thuộc | Đạt | Không commit `.venv`, `node_modules`, `dist`; phiên bản và giấy phép được ghi trong lockfile và hồ sơ bên thứ ba. |
| Tài liệu và giao tiếp | Đạt local | Có README, CHANGELOG, CONTRIBUTING, SECURITY, issue template và pull request template; phải đưa lên GitHub để có hiệu lực công khai. |

## Các điều kiện trước khi gọi là sẵn sàng dự thi

1. Push hoặc merge commit đã kiểm thử vào nhánh công khai.
2. Bật GitHub Issues và dùng issue template để ghi nhận lỗi thật.
3. Tạo tag theo Semantic Versioning và GitHub Release trước hạn nộp.
4. Đính kèm mã nguồn dạng `tar.gz` và ghi hướng dẫn build trong release notes.
5. Khi đề chính thức được công bố, đánh giá việc thay SQL Server/ODBC bằng hệ
   quản trị cơ sở dữ liệu nguồn mở; không mô tả SQL Server là mã nguồn mở.
6. Chạy thử từ một clone sạch trên laptop trình diễn, không dựa vào `.env`,
   `.venv`, `node_modules` hoặc database có sẵn của máy phát triển.
