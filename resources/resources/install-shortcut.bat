@echo off
chcp 65001 >nul 2>&1
title X markdown - 创建桌面快捷方式

echo ========================================
echo   X markdown - 创建桌面快捷方式
echo ========================================
echo.

set PROJECT_DIR=%~dp0
set SHORTCUT_NAME=X markdown
set ICON_PATH=%PROJECT_DIR%resources\icon.ico
set TARGET_PATH=%PROJECT_DIR%start.bat

echo 项目目录: %PROJECT_DIR%
echo 图标路径: %ICON_PATH%
echo 启动脚本: %TARGET_PATH%
echo.

REM 获取桌面路径
for /f "usebackq tokens=2,*" %%A in (`reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul`) do set DESKTOP=%%B

if not defined DESKTOP (
    set DESKTOP=%USERPROFILE%\Desktop
)

echo 桌面路径: %DESKTOP%
echo.

REM 使用 PowerShell 创建快捷方式
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$sc = $ws.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%.lnk'); " ^
  "$sc.TargetPath = '%TARGET_PATH%'; " ^
  "$sc.IconLocation = '%ICON_PATH%, 0'; " ^
  "$sc.WorkingDirectory = '%PROJECT_DIR%'; " ^
  "$sc.Description = 'X markdown - AI 内容聚合 Agent 工具'; " ^
  "$sc.WindowStyle = 7; " ^
  "$sc.Save(); " ^
  "Write-Host '快捷方式已创建: %DESKTOP%\%SHORTCUT_NAME%.lnk'"

if %errorlevel%==0 (
    echo.
    echo ========================================
    echo   快捷方式创建成功！
    echo   位置: %DESKTOP%\%SHORTCUT_NAME%.lnk
    echo   双击即可启动 X markdown
    echo ========================================
) else (
    echo.
    echo [错误] 快捷方式创建失败
)

echo.
pause
