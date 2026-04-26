@echo off
chcp 65001 >nul
cd /d "%~dp0"
python __main__.py --build-web
pause
