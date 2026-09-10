<!-- SPDX-License-Identifier: MIT -->

# DX-Lab Core Backend

Thư mục này chỉ chứa FastAPI, nghiệp vụ máy chủ, kiểm tra quyền và tài nguyên
SQL Server. Không đặt component React, CSS hoặc package npm tại đây.

## Bố cục

```text
backend/
├── database/       # schema, seed và công cụ khởi tạo SQL Server
├── routers/        # endpoint chia theo nhóm nghiệp vụ
├── tests/          # unit test và smoke test có hoàn nguyên dữ liệu
├── .env.example    # mẫu cấu hình, không chứa mật khẩu thật
├── config.py       # đọc và kiểm tra biến môi trường
├── core.py         # mật khẩu, JWT và xác thực quyền
├── db.py           # connection pooling và health check SQL Server
├── main.py         # điểm khởi động FastAPI
└── requirements.txt
```

## Chạy riêng backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Mọi thay đổi bảng phải viết theo kiểu chạy lại an toàn trong `database/schema.sql`.
Không sửa trực tiếp database mà bỏ qua migration. Không commit `.env`,
`.auth-secret`, `.venv`, dữ liệu thật hoặc file backup SQL Server.
