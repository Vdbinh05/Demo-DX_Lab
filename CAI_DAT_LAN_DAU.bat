@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo       DX-LAB CORE - CAI DAT LAN DAU
echo ==============================================
echo.

where npm >nul 2>nul
if errorlevel 1 (
    echo [LOI] Khong tim thay npm. Hay cai Node.js LTS truoc.
    pause
    exit /b 1
)

set "PYTHON_EXE="
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=python"

if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"

if not defined PYTHON_EXE (
    echo [LOI] Khong tim thay Python. Hay cai Python 3.10 tro len.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Dang tao moi truong Python .venv...
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 goto :install_error
) else (
    echo [1/4] Da co moi truong Python .venv.
)

echo [2/4] Dang cai thu vien backend...
".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :install_error

echo [3/4] Dang cai thu vien frontend...
call npm install
if errorlevel 1 goto :install_error

echo [4/4] Dang tao cau hinh SQL Server cuc bo...
if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul

findstr /C:"replace-with-your-local-password" "backend\.env" >nul
if not errorlevel 1 (
    echo.
    echo Hay thay replace-with-your-local-password bang mat khau SQL Server cua ban.
    echo Tep nay da duoc .gitignore bao ve va se khong bi day len GitHub.
    start /wait "Cau hinh DX-Lab" notepad.exe "backend\.env"
)

findstr /C:"replace-with-your-local-password" "backend\.env" >nul
if not errorlevel 1 (
    echo.
    echo [LOI] Mat khau SQL Server van chua duoc cap nhat trong backend\.env.
    pause
    exit /b 1
)

echo.
echo Cai dat hoan tat. Tu lan sau chi can chay CHAY_DU_AN.bat
pause
exit /b 0

:install_error
echo.
echo [LOI] Cai dat chua hoan tat. Kiem tra thong bao phia tren.
pause
exit /b 1
