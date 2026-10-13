@echo off
REM ============================================================
REM  build-iso.bat — xây file .iso cho GROM LINUX trên Windows
REM
REM  File .iso Linux (kernel + rootfs + bootloader) phải được
REM  đóng gói bằng công cụ Linux (live-build, squashfs-tools,
REM  xorriso). Windows không có các công cụ này, nên script này
REM  tự gọi WSL (Windows Subsystem for Linux) để build bên trong
REM  môi trường Linux, bạn chỉ cần double-click file này.
REM
REM  Yêu cầu: đã cài WSL2 + một distro (khuyên dùng Ubuntu).
REM  Nếu chưa có, mở PowerShell (quyền Admin) và chạy:
REM      wsl --install -d Ubuntu
REM  rồi khởi động lại máy.
REM ============================================================

setlocal

echo ================================================
echo   GROM LINUX - ISO Builder
echo ================================================
echo.

REM ---- Kiểm tra WSL có sẵn không ----
where wsl >nul 2>nul
if errorlevel 1 (
    echo [LOI] Khong tim thay WSL tren may nay.
    echo.
    echo Hay cai WSL2 truoc:
    echo   1. Mo PowerShell voi quyen Administrator
    echo   2. Chay:  wsl --install -d Ubuntu
    echo   3. Khoi dong lai may, tao user Ubuntu khi duoc hoi
    echo   4. Chay lai file build-iso.bat nay
    echo.
    pause
    exit /b 1
)

echo [OK] Da tim thay WSL.
echo.

REM ---- Chuyển đường dẫn thư mục hiện tại (Windows) sang path WSL ----
set "WIN_DIR=%~dp0"
for /f "usebackq delims=" %%P in (`wsl wslpath -a "%WIN_DIR%"`) do set "WSL_DIR=%%P"

if "%WSL_DIR%"=="" (
    echo [LOI] Khong chuyen doi duoc duong dan sang WSL.
    pause
    exit /b 1
)

echo Thu muc build (WSL): %WSL_DIR%
echo.
echo Bat dau build ISO - qua trinh nay co the mat 15-40 phut
echo tuy toc do mang va may tinh. Can quyen sudo ben trong WSL.
echo.
pause

REM ---- Chạy script build thật bên trong WSL ----
wsl bash -c "cd '%WSL_DIR%' && sudo bash build-iso.sh"

if errorlevel 1 (
    echo.
    echo [LOI] Build that bai. Xem log o tren de biet chi tiet.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Build xong! File .iso nam trong thu muc output\
echo ================================================
pause
