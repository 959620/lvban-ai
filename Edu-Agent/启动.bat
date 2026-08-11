@echo off
chcp 65001 >nul
title Edu-Agent 教务助手
cd /d "%~dp0"

echo ========================================
echo   Edu-Agent 正在启动（无需手动开终端）
echo ========================================

if not exist ".venv\Scripts\python.exe" (
    echo 首次运行：正在创建环境，请稍候...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt -q
)

if not exist ".env" copy config\.env.example .env >nul

start "" "http://127.0.0.1:8000/"
echo 浏览器即将打开 http://127.0.0.1:8000/
echo 关闭本窗口将停止服务。
echo.

.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
