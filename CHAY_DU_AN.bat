@echo off
rem SPDX-License-Identifier: MIT
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo Chua cai dat du an. Dang mo CAI_DAT_LAN_DAU.bat...
    call "%~dp0CAI_DAT_LAN_DAU.bat"
    if errorlevel 1 exit /b 1
)

if not exist "backend\.env" (
    echo [LOI] Chua co backend\.env. Hay chay CAI_DAT_LAN_DAU.bat.
    pause
    exit /b 1
)

findstr /C:"replace-with-your-local-password" "backend\.env" >nul
if not errorlevel 1 (
    echo [LOI] Ban chua nhap mat khau SQL Server trong backend\.env.
    start /wait "Cau hinh DX-Lab" notepad.exe "backend\.env"
    findstr /C:"replace-with-your-local-password" "backend\.env" >nul
    if not errorlevel 1 exit /b 1
)

if not exist "frontend\node_modules" (
    echo [LOI] Chua cai thu vien frontend. Hay chay CAI_DAT_LAN_DAU.bat.
    pause
    exit /b 1
)

echo Dang khoi dong DX-Lab Core...
start "DX-Lab Backend" /D "%~dp0backend" cmd /k ""%~dp0backend\.venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
start "DX-Lab Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Co the dong cua so nay. Hai cua so server can duoc giu mo.
timeout /t 5 >nul
exit /b 0
