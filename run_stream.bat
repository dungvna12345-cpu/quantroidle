@echo off
chcp 65001 >nul
title Quan Tro Idle - iPhone Streamer
cd /d "%~dp0"
echo ========================================================
echo   KHOI DONG HE THONG STREAM QUAN TRO IDLE LEN IPHONE
echo ========================================================
echo.
python tools\stream_to_phone.py
pause
