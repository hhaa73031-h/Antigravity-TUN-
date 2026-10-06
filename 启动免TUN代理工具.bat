@echo off
chcp 65001 >nul
title Antigravity 免 TUN 代理助手
cd /d "%~dp0"

if exist "dist\Antigravity免TUN代理.exe" (
    start "" "dist\Antigravity免TUN代理.exe"
    exit /b
)

if exist "Antigravity免TUN代理.exe" (
    start "" "Antigravity免TUN代理.exe"
    exit /b
)

python app.py
exit /b
