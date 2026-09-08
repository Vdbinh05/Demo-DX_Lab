# DX-Lab Core

DX-Lab Core gồm frontend React + Vite và backend xác thực FastAPI + SQL Server.

## Yêu cầu

- Node.js 20.19+ (khuyến nghị Node.js LTS mới)
- Python 3.10+
- SQL Server và ODBC Driver 17 for SQL Server
- Visual Studio Code
- Internet để npm tải package lần đầu

## Chạy backend

Thiết lập thông tin SQL Server bằng biến môi trường. Không commit mật khẩu thật vào Git:

```powershell
$env:DXLAB_SQL_SERVER="localhost"
$env:DXLAB_SQL_DATABASE="DXLabCore"
$env:DXLAB_SQL_USER="sa"
$env:DXLAB_SQL_PASSWORD="mat-khau-sql-server-cua-ban"
```

Sau đó cài dependency và chạy FastAPI:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

API chạy mặc định tại `http://localhost:8000`. Các biến hỗ trợ được liệt kê trong `backend/.env.example`.

## Chạy frontend

Mở thư mục này bằng Visual Studio Code, sau đó mở Terminal:

```bash
npm install
npm run dev
```

Vite sẽ hiển thị địa chỉ local, thường là:

```text
http://localhost:5173
```

Mở địa chỉ đó bằng Chrome/Edge.

## Build

```bash
npm run build
```

## Phạm vi hiện tại

Phạm vi đã kết nối dữ liệu thật:

- Đăng ký tài khoản qua `POST /register` và lưu vào SQL Server
- Đăng nhập qua `POST /login`
- Mật khẩu tài khoản mới được băm PBKDF2
- Các tài khoản cũ lưu mật khẩu dạng thường vẫn được hỗ trợ trong giai đoạn chuyển đổi

Các phần còn ở dạng prototype:

- Không có Keycloak thật
- Không có n8n thật
- Không có Ollama/Qdrant thật
- Dữ liệu nghiệp vụ ngoài tài khoản vẫn dùng mock data

Các chức năng đã mô phỏng:

- Login / chọn role
- Dashboard
- Sales
- Inventory
- Purchase Request
- Approval Center
- Workflow
- Knowledge / Documents
- AI Copilot
- Administration
- Tìm kiếm bảng dữ liệu
- Approve / Reject demo
- AI chat demo

## Định hướng tích hợp sau này

1. Keycloak/OIDC cho SSO.
2. Mở rộng REST API cho dữ liệu nghiệp vụ.
3. n8n cho workflow.
4. Hoàn thiện migration và quản lý schema SQL Server.
5. Metabase cho BI.
6. Ollama + Qdrant + RAG/Agent cho AI.

Không để frontend trực tiếp ghi CSDL hoặc tự quyết định các hành động nhạy cảm; các thao tác cần approval nên đi qua Backend/API và HITL.


## GUI version included

Bản hiện tại đã nâng cấp thành frontend GUI hoàn chỉnh hơn cho mục 2.3:

- Dashboard enterprise với KPI, chart, approval và inventory alert
- Sales Orders có form Create Order + tính tổng tiền + trạng thái approval demo
- Customers / Products / Quotations
- Inventory / Stock / Stock Movement
- Purchase Requests
- Approval Center với Approve / Reject
- AI Copilot với quick prompts + mock tool panel
- My Tasks / Workflow History / Knowledge / Administration
- Role simulation: CEO / Manager / Sales / Warehouse
- Toast notification, responsive layout, search/filter UI
