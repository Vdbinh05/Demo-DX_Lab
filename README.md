# DX-Lab Core

DX-Lab Core là ứng dụng quản lý bán hàng sử dụng React, FastAPI và Microsoft SQL Server. Frontend và backend được đặt trong hai thư mục riêng để thành viên mới dễ nhận biết, cài đặt và phát triển độc lập.

## Cấu trúc dự án

```text
DX-Lab-Core/
├── frontend/                       # Giao diện React + Vite
│   ├── src/
│   ├── .env.example                # Mẫu địa chỉ API
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── backend/                        # FastAPI + SQL Server
│   ├── database/
│   │   ├── init_database.py        # Chạy schema và seed tự động
│   │   ├── schema.sql              # Tạo database và bảng
│   │   └── seed.sql                # Dữ liệu demo an toàn
│   ├── .env.example                # Mẫu cấu hình SQL Server
│   ├── main.py
│   └── requirements.txt
│
├── docs/                           # Tài liệu nguồn mở
├── .gitignore
├── CAI_DAT_LAN_DAU.bat             # Cài dự án trên máy mới
├── CHAY_DU_AN.bat                  # Chạy frontend và backend
├── README.md
└── THIRD_PARTY_NOTICES.md
```

Các thư mục `.venv`, `node_modules`, `dist`, `__pycache__` và file `.env` chỉ tồn tại trên máy lập trình viên, không được đẩy lên GitHub.

## 1. Yêu cầu

Cài đặt:

- Git.
- Node.js 20.19 trở lên.
- Python 3.10 trở lên.
- Microsoft SQL Server.
- ODBC Driver 17 for SQL Server.
- SQL Server Management Studio (SSMS), khuyến nghị để kiểm tra database.

SQL Server cần bật SQL Server Authentication. Tài khoản dùng trong lần cài đầu phải có quyền tạo database.

## 2. Tải mã nguồn

Máy chưa có dự án:

```powershell
git clone https://github.com/Vdbinh05/Demo-DX_Lab.git
cd Demo-DX_Lab
```

Máy đã có dự án:

```powershell
git pull origin main
```

## 3. Cài đặt lần đầu

Từ thư mục gốc, chạy:

```powershell
.\CAI_DAT_LAN_DAU.bat
```

Script tự động:

1. Tạo môi trường Python tại `backend/.venv`.
2. Cài dependency FastAPI.
3. Cài dependency React tại `frontend/node_modules`.
4. Tạo `backend/.env` và mở bằng Notepad.
5. Tạo database `DXLabCore`, 10 bảng và dữ liệu demo.

Khi Notepad mở `backend/.env`, điền tài khoản SQL Server trên chính máy đó:

```env
DXLAB_SQL_SERVER=localhost,1433
DXLAB_SQL_DATABASE=DXLabCore
DXLAB_SQL_USER=sa
DXLAB_SQL_PASSWORD=MAT_KHAU_SQL_SERVER_CUA_BAN
DXLAB_SQL_DRIVER={ODBC Driver 17 for SQL Server}
```

Lưu và đóng Notepad để quá trình cài đặt tiếp tục. Không ghi mật khẩu thật vào README, `.env.example` hoặc bất kỳ file nào được Git theo dõi.

## 4. Chạy dự án hằng ngày

Đảm bảo dịch vụ SQL Server đang hoạt động, sau đó chạy tại thư mục gốc:

```powershell
.\CHAY_DU_AN.bat
```

Địa chỉ sử dụng:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- Swagger API: <http://localhost:8000/docs>

Giữ hai cửa sổ server mở trong khi sử dụng. Nhấn `Ctrl + C` trong từng cửa sổ để dừng.

## 5. Tài khoản website demo

| Khu vực | Tên đăng nhập | Mật khẩu |
| --- | --- | --- |
| Quản trị viên | `admin.demo` | `Admin@123` |
| Nhân viên | `sales.demo` | `Sales@123` |

Đây là tài khoản phát triển công khai. Phải đổi hoặc xóa trước khi triển khai hệ thống thật. Người dùng đăng ký công khai từ giao diện luôn nhận vai trò `Sales`.

## 6. Khởi tạo database thủ công

Nếu script tự động không có quyền tạo database, mở SSMS và chạy theo thứ tự:

1. `backend/database/schema.sql`.
2. `backend/database/seed.sql`.

Hai script có thể chạy lại, không xóa dữ liệu hiện có và không chèn trùng mã demo.

Schema tạo các bảng:

- `Roles`, `Users`.
- `Customers`, `Products`.
- `SalesOrders`, `SalesOrderItems`.
- `Quotations`, `PurchaseRequests`.
- `StockMovements`, `Activities`.

Seed chỉ chứa dữ liệu giả, không chứa mật khẩu SQL Server hoặc dữ liệu khách hàng thật.

## 7. Chạy riêng từng phần

### Backend

Từ thư mục gốc:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm run dev
```

### Build frontend

```powershell
cd frontend
npm run build
```

## 8. Lỗi kết nối SQL Server

Nếu giao diện báo `Không thể kết nối SQL Server`, kiểm tra:

1. Dịch vụ SQL Server đang chạy.
2. `backend/.env` chứa đúng tên máy chủ, tài khoản và mật khẩu.
3. Database có tên `DXLabCore`.
4. SQL Server đang nghe tại cổng `1433`.
5. Máy đã cài ODBC Driver 17.
6. Nếu dùng named instance, thử `DXLAB_SQL_SERVER=localhost\SQLEXPRESS`.

`localhost` luôn là máy đang chạy chương trình. Mỗi thành viên nên dùng SQL Server và tài khoản riêng trên máy của mình.

## 9. Phạm vi hiện tại

Đã kết nối SQL Server thật:

- `POST /register`: đăng ký tài khoản.
- `POST /login`: đăng nhập và trả về `RoleID`.
- Mật khẩu mới được băm bằng PBKDF2-SHA256.
- Frontend đối chiếu khu vực Nhân viên/Quản trị viên với vai trò từ backend.

Các màn hình nghiệp vụ ngoài đăng nhập và đăng ký vẫn đang dùng dữ liệu demo phía frontend. JWT và kiểm tra RBAC tại từng API là bước backend tiếp theo.

## 10. Mã nguồn mở

- [Nguồn mở được tham khảo](docs/OPEN_SOURCE_REFERENCES.md)
- [Thông báo thư viện bên thứ ba](THIRD_PARTY_NOTICES.md)

Không commit `.env`, mật khẩu SQL Server, file backup chứa dữ liệu thật hoặc thông tin cá nhân.
