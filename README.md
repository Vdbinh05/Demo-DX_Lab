# DX-Lab Core

DX-Lab Core là ứng dụng quản lý bán hàng sử dụng React, FastAPI và Microsoft SQL Server. Frontend và backend được đặt trong hai thư mục riêng để thành viên mới dễ nhận biết, cài đặt và phát triển độc lập.

## Cấu trúc dự án

```text
DX-Lab-Core/
├── frontend/                       # Giao diện React + Vite
│   ├── src/
│   │   ├── admin/                  # Các màn quản trị dùng API thật
│   │   ├── config/                 # Cấu hình cổng, menu và permission
│   │   ├── hooks/                  # Đồng bộ catalog và đơn cá nhân
│   │   └── api.js                  # Lớp gọi FastAPI tập trung
│   ├── .env.example                # Mẫu địa chỉ API
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── README.md                    # Hướng dẫn riêng cho frontend
│   └── vite.config.js
│
├── backend/                        # FastAPI + SQL Server
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/             # Auth, catalog, orders và admin
│   │   │   ├── dependencies.py     # Xác thực request và phân quyền
│   │   │   └── router.py           # Điểm ghép tất cả router
│   │   ├── core/                   # Cấu hình, mật khẩu và JWT
│   │   ├── database/               # Kết nối pool và health check
│   │   ├── schemas/                # Model request/response Pydantic
│   │   └── main.py                 # App factory và middleware
│   ├── database/
│   │   ├── init_database.py        # Chạy schema và seed tự động
│   │   ├── schema.sql              # Tạo database và bảng
│   │   └── seed.sql                # Dữ liệu demo an toàn
│   ├── .env.example                # Mẫu cấu hình SQL Server
│   ├── main.py                      # Entry point tương thích lệnh chạy cũ
│   ├── tests/                       # Kiểm thử luồng bán hàng có hoàn nguyên
│   ├── README.md                    # Hướng dẫn riêng cho backend
│   └── requirements.txt
│
├── docs/                           # Tài liệu nguồn mở
├── LICENSES/                       # Chính sách giấy phép mã được tích hợp
├── .github/                        # Mẫu issue và pull request
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
5. Tạo database `DXLabCore`, 12 bảng và dữ liệu demo.

Khi Notepad mở `backend/.env`, điền tài khoản SQL Server trên chính máy đó:

```env
DXLAB_SQL_SERVER=localhost,1433
DXLAB_SQL_DATABASE=DXLabCore
DXLAB_SQL_USER=sa
DXLAB_SQL_PASSWORD=MAT_KHAU_SQL_SERVER_CUA_BAN
DXLAB_SQL_DRIVER={ODBC Driver 17 for SQL Server}
DXLAB_AUTH_SECRET=
DXLAB_ACCESS_TOKEN_MINUTES=480
DXLAB_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Ở máy phát triển có thể để trống `DXLAB_AUTH_SECRET`; backend tạo khóa cục bộ
ổn định trong tệp đã được Git bỏ qua. Khi triển khai thật phải cấp một khóa bí
mật dài bằng biến môi trường.

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
- `Customers`, `Products`, `Promotions`.
- `SalesOrders`, `SalesOrderItems`.
- `Quotations`, `PurchaseRequests`.
- `StockMovements`, `Activities`.
- `SystemSettings`.

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

### Kiểm tra luồng đơn hàng

Khởi động backend trước, sau đó từ thư mục gốc chạy:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\tests\integration_registration_smoke.py
.\backend\.venv\Scripts\python.exe .\backend\tests\integration_order_smoke.py
```

Hai bài kiểm tra tạo tài khoản và đơn hàng tạm, kiểm tra đăng nhập, thanh toán,
trừ kho, Admin xem chi tiết và chống gửi trùng; cuối cùng tự xóa dữ liệu thử và
hoàn lại tồn kho.

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
- `POST /login`: đăng nhập, trả về `RoleID` và access token có thời hạn.
- `GET /me`: xác thực lại phiên sau khi tải lại trang.
- Mật khẩu mới được băm bằng PBKDF2-SHA256.
- Frontend đối chiếu khu vực Nhân viên/Quản trị viên với vai trò từ backend.
- Mọi API `/admin/*` kiểm tra token, trạng thái tài khoản và vai trò `Admin` từ SQL Server.
- Tổng quan, doanh thu, đơn hàng, chi tiết đơn, sản phẩm bán chạy và khách mua hôm nay dùng dữ liệu SQL thật.
- Admin có thể tìm kiếm toàn hệ thống, xem thông báo tồn kho, quản lý sản phẩm/khách hàng, điều chỉnh kho, cấp/khóa tài khoản và lưu cấu hình doanh nghiệp.
- Trang đơn hàng chỉ thống kê giao dịch đã thanh toán và hiển thị phương thức `Tiền mặt` hoặc `Chuyển khoản`.
- Trang Bán hàng và Danh mục của Sale đọc chung giá bán, tồn kho và mã sản phẩm từ SQL Server; dữ liệu tự làm mới khi quay lại tab và định kỳ 15 giây.
- `POST /orders` tạo đơn, chi tiết đơn, trừ tồn kho và ghi `StockMovements` trong một SQL transaction; giá bán luôn được đọc lại ở backend.
- Mỗi lần thanh toán có `idempotency_key`; gửi lại cùng giao dịch không tạo đơn hoặc trừ kho lần hai.
- Đơn đã thanh toán được ghi `PaymentStatus=Paid`, `OrderStatus=Completed` và không có API hủy ở phạm vi bản thử nghiệm.
- Chi tiết đơn lưu snapshot tên và đơn giá tại thời điểm bán, không bị thay đổi khi Admin sửa sản phẩm sau này.
- `GET /orders/my-orders` trả đúng doanh thu và lịch sử đơn của tài khoản đang đăng nhập.
- Khách hàng tại POS và trang tra cứu Sale dùng chung dữ liệu từ `GET /catalog/customers`.
- Trang Khuyến mãi Sale chỉ đọc chương trình còn hiệu lực từ `GET /catalog/promotions`; nút tư vấn mở đúng đối tượng và thời hạn áp dụng.
- Phiên được giữ trong `sessionStorage`, URL được quản lý bởi React Router, xác thực lại với backend sau F5 và dùng khóa JWT ổn định qua restart.
- TanStack Query quản lý cache/làm mới API, TanStack Table render bảng đơn Admin và Recharts render biểu đồ doanh thu.
- ODBC connection pooling được bật để tái sử dụng kết nối bên dưới sau mỗi lần đóng connection ở cấp request.
- Backend kiểm tra kết nối và các bảng SQL Server bắt buộc ngay khi khởi động, đồng thời trả lỗi cấu hình dễ chẩn đoán.

Màn hình Admin tạo/sửa khuyến mãi và tích hợp thanh toán ngân hàng thật chưa nằm trong phạm vi hiện tại.

## 10. Mã nguồn mở

- [Nguồn mở được tham khảo](docs/OPEN_SOURCE_REFERENCES.md)
- [Ma trận thành phần mã nguồn mở](docs/OPEN_SOURCE_COMPONENTS.md)
- [Quy ước cấu trúc dự án](docs/PROJECT_STRUCTURE.md)
- [Kiểm tra tuân thủ phần mềm nguồn mở](docs/OPEN_SOURCE_COMPLIANCE.md)
- [Thông báo thư viện bên thứ ba](THIRD_PARTY_NOTICES.md)
- [Giấy phép MIT của dự án](LICENSE)
- [Hướng dẫn đóng góp](CONTRIBUTING.md)
- [Chính sách bảo mật](SECURITY.md)

Không commit `.env`, mật khẩu SQL Server, file backup chứa dữ liệu thật hoặc thông tin cá nhân.

## 11. Giấy phép

DX-Lab Core được phát hành theo giấy phép MIT, một giấy phép được OSI phê duyệt.
Giấy phép cho phép sử dụng, nghiên cứu, sửa đổi và phân phối lại phần mềm với
điều kiện giữ nguyên thông báo bản quyền và giấy phép. Toàn văn nằm trong
[`LICENSE`](LICENSE).

Microsoft SQL Server và Microsoft ODBC Driver chỉ là hạ tầng của bản thử nghiệm
hiện tại và không phải phần mềm nguồn mở. Nhóm phải đánh giá thay thế khi đề thi
chính thức yêu cầu một chuỗi công nghệ hoàn toàn mở.
