@echo off
chcp 65001 >nul 2>&1
title 知乎 Cookie 提取 - 获取精选AI高质量内容

echo ==================================================
echo   知乎 Cookie 提取工具
echo ==================================================
echo.
echo 正在启动图形界面...
echo.

set PYTHON_EXE=C:\Users\qzq\AppData\Local\Programs\Python\Python312\python.exe
set BACKEND_DIR=%~dp0backend

cd /d "%BACKEND_DIR%"
"%PYTHON_EXE%" zhihu_cookie_gui.py

echo.
echo 流程结束。
pause
