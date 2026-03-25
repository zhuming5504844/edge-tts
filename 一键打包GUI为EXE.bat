@echo off
setlocal EnableExtensions
chcp 65001 >nul

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 .venv，请先运行“ 一键安装GUI环境.bat ”。
    goto :fail
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :fail

echo [打包] 正在使用 PyInstaller 打包 GUI...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name edge-tts-gui ^
  gui.py

if errorlevel 1 goto :fail

echo [完成] 打包成功。
echo [输出] dist\edge-tts-gui.exe
goto :ok

:fail
echo [失败] 打包过程出现错误。
pause
exit /b 1

:ok
pause
exit /b 0
