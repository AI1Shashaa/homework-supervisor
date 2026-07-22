@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 安装依赖...
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [2/3] 使用 PyInstaller 打包单文件 EXE...
python -m PyInstaller --noconfirm desktop_pet.spec
if errorlevel 1 goto :fail

echo [3/3] 完成！
echo 可执行文件: %~dp0dist\DesktopPet.exe
echo 直接双击运行即可。
pause
exit /b 0

:fail
echo 打包失败，请确认已安装 Python 3.10+ 并勾选 Add to PATH。
pause
exit /b 1
