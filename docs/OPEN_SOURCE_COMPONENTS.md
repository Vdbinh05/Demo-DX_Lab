<!-- SPDX-License-Identifier: MIT -->

# Ma trận thành phần mã nguồn mở

| Nhu cầu | Thành phần | Cách tích hợp trong dự án | Bằng chứng |
| --- | --- | --- | --- |
| Điều hướng có URL | React Router | `BrowserRouter`, `useLocation`, `useNavigate` | `frontend/src/main.jsx`, `frontend/src/App.jsx` |
| Đồng bộ dữ liệu API | TanStack Query | `QueryClientProvider`, `useQuery` và vô hiệu cache sau mutation | `frontend/src/main.jsx`, `frontend/src/hooks`, `frontend/src/admin/AdminPages.jsx` |
| Bảng dữ liệu | TanStack Table | mô hình cột và `flexRender` cho danh sách đơn | `frontend/src/admin/AdminPages.jsx` |
| Biểu đồ doanh thu | Recharts | biểu đồ cột responsive từ dữ liệu API | `frontend/src/admin/AdminPages.jsx` |
| Icon giao diện | Lucide | icon React nhất quán | `frontend/src/App.jsx`, `frontend/src/admin/AdminPages.jsx` |
| API và OpenAPI | FastAPI | router, dependency xác thực, Swagger | `backend/app/main.py`, `backend/app/api` |
| Validation | Pydantic | schema request, giới hạn chuỗi/số lượng | `backend/app/schemas`, `backend/app/api/routes` |
| SQL Server | pyodbc | transaction và connection pooling | `backend/app/database/connection.py`, `backend/app/repositories`, `backend/app/services` |
| JWT | PyJWT | access token có hạn dùng | `backend/app/core/security.py` |
| Kiến trúc backend | Full Stack FastAPI Template | cách chia `app/api`, `app/core`, router tổng và dependency | commit `cb740b656d7a0a6c5e12c7bf8e50343ec94ee9c7` |

Không tính Microsoft SQL Server hay ODBC Driver là mã nguồn mở; chúng là hạ
tầng chạy bản thử nghiệm. Lockfile và tệp requirements là nguồn sự thật về
phiên bản được cài.
