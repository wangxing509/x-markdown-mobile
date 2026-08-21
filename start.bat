@echo off
chcp 65001 >nul 2>&1
title X markdown Agent

echo ========================================
echo   X markdown 启动中...
echo ========================================

REM ====== 配置路径 ======
set PYTHON_EXE=C:\Users\qzq\AppData\Local\Programs\Python\Python312\python.exe
set NODE_DIR=C:\Users\qzq\.workbuddy\binaries\node\versions\22.22.2
set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%backend
set ELECTRON_EXE=%PROJECT_DIR%node_modules\electron\dist\electron.exe

set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PATH=%NODE_DIR%;%PATH%

cd /d "%PROJECT_DIR%"

REM ====== 检查依赖 ======
if not exist "%PYTHON_EXE%" (
    echo [错误] 未找到 Python: %PYTHON_EXE%
    pause
    exit /b 1
)
if not exist "%ELECTRON_EXE%" (
    echo [错误] 未找到 Electron: %ELECTRON_EXE%
    echo [提示] 请先运行: npm install
    pause
    exit /b 1
)
if not exist "%PROJECT_DIR%dist\index.html" (
    echo [错误] 未找到前端构建产物，正在构建...
    call "%NODE_DIR%\npx.cmd" vite build
    call "%NODE_DIR%\tsc.cmd" -p tsconfig.electron.json
    copy /Y electron\preload.cjs dist-electron\preload.cjs >nul
)

REM ====== [1/2] 启动 Python 后端 ======
echo [1/2] 启动 Python 后端 (端口 8765)...
start "XMarkdown-Backend" /min cmd /k "cd /d "%BACKEND_DIR%" && "%PYTHON_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8765"

REM ====== 等待后端就绪（最多 30 秒） ======
echo      等待后端就绪...
set WAIT_COUNT=0
:WAIT_BACKEND
timeout /t 1 /nobreak >nul
set /a WAIT_COUNT+=1

REM 用 PowerShell 检测健康检查接口
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/api/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    echo      后端已就绪 ^(耗时 %WAIT_COUNT% 秒^)
    goto START_ELECTRON
)
if %WAIT_COUNT% GEQ 30 (
    echo [警告] 后端 30 秒内未就绪，继续启动前端...
    goto START_ELECTRON
)
goto WAIT_BACKEND

:START_ELECTRON
REM ====== [2/2] 启动 Electron 前端 ======
echo [2/2] 启动 Electron 前端...
"%ELECTRON_EXE%" .

echo.
echo ========================================
echo   X markdown 已退出
echo ========================================
pause
