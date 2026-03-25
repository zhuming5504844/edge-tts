@echo off
chcp 65001 >nul
setlocal

if not exist .venv\Scripts\activate.bat (
  echo [ERROR] 未检测到 .venv，请先运行 install_gui_env.bat
  exit /b 1
)

call .venv\Scripts\activate.bat
python gui.py
