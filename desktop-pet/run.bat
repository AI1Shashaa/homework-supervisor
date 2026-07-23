@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "assets\videos\video.mp4" (
  echo 未检测到视频素材，正在尝试从 Downloads 导入...
  python scripts\import_videos.py --from "%USERPROFILE%\Downloads"
  if errorlevel 1 (
    echo.
    echo 请先把 10 个 mp4 放到 Downloads，或手动运行:
    echo   python scripts\import_videos.py --from "C:\Users\1\Downloads"
    pause
    exit /b 1
  )
)

python -c "import PySide6" 2>nul
if errorlevel 1 (
  echo 正在安装依赖...
  pip install -r requirements.txt
)

python main.py
if errorlevel 1 pause
