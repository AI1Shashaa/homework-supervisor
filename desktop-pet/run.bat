@echo off
chcp 65001 >nul
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo 请先安装依赖: pip install -r requirements.txt
  pause
)
