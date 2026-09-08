# DX-Lab Core Frontend

Frontend prototype cho DX-Lab Core, xây dựng bằng React + Vite.

## Yêu cầu

- Node.js 20.19+ (khuyến nghị Node.js LTS mới)
- Visual Studio Code
- Internet để npm tải package lần đầu

## Chạy project

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

Đây là frontend-only prototype:

- Không có Backend
- Không có PostgreSQL
- Không có Keycloak thật
- Không có n8n thật
- Không có Ollama/Qdrant thật
- Dữ liệu đang dùng mock data

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
2. REST API cho dữ liệu.
3. n8n cho workflow.
4. PostgreSQL cho database.
5. Metabase cho BI.
6. Ollama + Qdrant + RAG/Agent cho AI.

Không để frontend trực tiếp ghi nhiều bảng PostgreSQL hoặc tự quyết định các hành động nhạy cảm; các thao tác cần approval nên đi qua Backend/API và HITL.


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
