@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "assets\videos\video.mp4" (
  echo 打包前需要先导入视频素材。
  python scripts\import_videos.py --from "%USERPROFILE%\Downloads"
  if errorlevel 1 (
    echo 也可先运行: python scripts\make_placeholders.py
    pause
    exit /b 1
  )
)

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm desktop_pet.spec
echo.
echo 完成: dist\DesktopPet.exe
pause
