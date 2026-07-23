@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo 正在从 Downloads 导入视频素材...
python scripts\import_videos.py --from "%USERPROFILE%\Downloads"
if errorlevel 1 (
  echo.
  echo 若路径不同，可手动指定，例如:
  echo   python scripts\import_videos.py --from "C:\Users\1\Downloads"
  pause
  exit /b 1
)
echo.
pause
