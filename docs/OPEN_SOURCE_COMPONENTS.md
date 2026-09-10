<!-- SPDX-License-Identifier: MIT -->

# Ma trận thành phần mã nguồn mở

| Nhu cầu | Thành phần | Cách tích hợp trong dự án | Bằng chứng |
| --- | --- | --- | --- |
| Điều hướng có URL | React Router | `BrowserRouter`, `useLocation`, `useNavigate` | `frontend/src/main.jsx`, `frontend/src/App.jsx` |
| Đồng bộ dữ liệu API | TanStack Query | `QueryClientProvider`, `useQuery` và vô hiệu cache sau mutation | `frontend/src/main.jsx`, `frontend/src/hooks`, `frontend/src/admin/AdminPages.jsx` |
| Bảng dữ liệu | TanStack Table | mô hình cột và `flexRender` cho danh sách đơn | `frontend/src/admin/AdminPages.jsx` |
| Biểu đồ doanh thu | Recharts | biểu đồ cột responsive từ dữ liệu API | `frontend/src/admin/AdminPages.jsx` |
| Icon giao diện | Lucide | icon React nhất quán | `frontend/src/App.jsx`, `frontend/src/admin/AdminPages.jsx` |
| API và OpenAPI | FastAPI | router, dependency xác thực, Swagger | `backend/main.py`, `backend/routers` |
| Validation | Pydantic | schema request, giới hạn chuỗi/số lượng | `backend/main.py`, `backend/routers` |
| SQL Server | pyodbc | transaction và connection pooling | `backend/database.py`, `backend/routers` |
| JWT | PyJWT | access token có hạn dùng | `backend/core.py` |

Không tính Microsoft SQL Server hay ODBC Driver là mã nguồn mở; chúng là hạ
tầng chạy bản thử nghiệm. Lockfile và tệp requirements là nguồn sự thật về
phiên bản được cài.
