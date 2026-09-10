# Third-Party Notices

DX-Lab Core sử dụng trực tiếp các thư viện mã nguồn mở dưới đây. Các thư viện
được cài qua `npm` hoặc `pip`; mã nguồn của chúng không được nhận là mã do nhóm
DX-Lab Core tự viết. Phiên bản chính xác nằm trong `frontend/package-lock.json`
và `backend/requirements.txt`.

## Frontend dependencies

| Thành phần | Phiên bản khai báo | Giấy phép | Nguồn |
| --- | --- | --- | --- |
| React | 19.2.8 | MIT | <https://github.com/facebook/react> |
| React DOM | 19.2.8 | MIT | <https://github.com/facebook/react> |
| React Router DOM | 7.18.3 | MIT | <https://github.com/remix-run/react-router> |
| TanStack Query | 5.102.8 | MIT | <https://github.com/TanStack/query> |
| TanStack Table | 8.21.3 | MIT | <https://github.com/TanStack/table> |
| Recharts | 3.10.1 | MIT | <https://github.com/recharts/recharts> |
| Lucide React | 0.468.0 | ISC | <https://github.com/lucide-icons/lucide> |
| Vite | 7.3.6 | MIT | <https://github.com/vitejs/vite> |
| Vite React plugin | 5.2.0 | MIT | <https://github.com/vitejs/vite-plugin-react> |

## Backend dependencies

| Thành phần | Phiên bản | Giấy phép | Nguồn |
| --- | --- | --- | --- |
| FastAPI | 0.141.1 | MIT | <https://github.com/fastapi/fastapi> |
| Uvicorn | 0.52.4 | BSD-3-Clause | <https://github.com/Kludex/uvicorn> |
| pyodbc | 5.3.0 | MIT | <https://github.com/mkleehammer/pyodbc> |
| python-dotenv | 1.2.3 | BSD-3-Clause | <https://github.com/theskumar/python-dotenv> |
| PyJWT | 2.13.0 | MIT | <https://github.com/jpadilla/pyjwt> |
| Pydantic | 2.13.5 | MIT | <https://github.com/pydantic/pydantic> |

## Nguồn tham khảo, không phải dependency

Các dự án Full Stack FastAPI Template, Material UI, React-admin và shadcn/ui
được dùng để nghiên cứu kiến trúc hoặc mẫu tương tác. Chúng không được cài vào
ứng dụng và không có template nào được sao chép nguyên khối. Cách áp dụng được
ghi tại `docs/OPEN_SOURCE_REFERENCES.md`.

Microsoft SQL Server và Microsoft ODBC Driver là thành phần hạ tầng bên ngoài,
không phải thành phần mã nguồn mở của kho mã này.

Toàn văn giấy phép của phần mềm DX-Lab Core nằm trong `LICENSE`; hướng dẫn kiểm
tra giấy phép phụ thuộc nằm trong `LICENSES/README.md`.
