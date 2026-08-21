@echo off
chcp 65001 >nul
title X-markdown 一键同步到手机端 (GitHub Pages)
echo ============================================================
echo   X-markdown 一键同步：桌面端数据 -> 推送到 GitHub -> Actions 部署
echo ============================================================
echo.

cd /d "%~dp0.."

echo 当前目录: %CD%
echo.
set /p REPO=请输入 GitHub 仓库 (owner/repo)，回车则使用现有 origin: 

if "%REPO%"=="" (
  node scripts/sync.mjs --push
) else (
  node scripts/sync.mjs --repo "%REPO%" --push
)

echo.
echo 若上面提示成功，GitHub Actions 会自动构建并部署手机端站点。
pause
