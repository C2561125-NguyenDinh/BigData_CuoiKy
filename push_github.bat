@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "REPO=https://github.com/C2561125-NguyenDinh/BigData_CuoiKy.git"

echo === Day do an len GitHub: %REPO%
where git >nul 2>&1
if errorlevel 1 (
  echo [LOI] Chua cai Git. Tai tai https://git-scm.com/download/win roi chay lai file nay.
  pause & exit /b 1
)

if not exist ".git" git init

rem Ten va email cho commit (chi hoi lan dau neu may chua cau hinh)
git config user.name >nul 2>&1
if errorlevel 1 (
  set /p GUSER=Nhap ten GitHub: 
  call git config user.name "%%GUSER%%"
)
git config user.email >nul 2>&1
if errorlevel 1 (
  set /p GMAIL=Nhap email GitHub: 
  call git config user.email "%%GMAIL%%"
)

git add -A
git commit -m "Do an Big Data cuoi ky: phi giam un tac Manhattan - code va bao cao"
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin %REPO%

echo === Dang day len GitHub (lan dau co the hien cua so dang nhap GitHub)...
git push -u origin main
if not errorlevel 1 goto ok

echo.
echo [!] Day len that bai. Neu repo tren GitHub da co san file (vd README tao luc lap repo),
echo     co the ghi de toan bo bang ban tren may nay.
set /p ANS=Ghi de repo tren GitHub? (Y/N): 
if /i "%ANS%"=="Y" (
  git push -u origin main --force
  if not errorlevel 1 goto ok
)
echo [LOI] Chua day len duoc. Kiem tra dang nhap GitHub va quyen ghi vao repo.
pause & exit /b 1

:ok
echo.
echo === Xong. Xem tai: https://github.com/C2561125-NguyenDinh/BigData_CuoiKy
pause
