@echo off
setlocal EnableExtensions
chcp 65001 >nul

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [提示] 未检测到 .venv，先自动安装环境...
    call "一键安装GUI环境.bat"
    if errorlevel 1 goto :fail
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :fail

echo [启动] 正在打开 edge-tts GUI...
python gui.py
if errorlevel 1 goto :fail

goto :ok

:fail
echo [失败] 启动失败，请检查上方日志。
pause
exit /b 1

:ok
exit /b 0
