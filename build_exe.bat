@echo off
chcp 65001 >nul
setlocal

if not exist .venv\Scripts\activate.bat (
  echo [ERROR] 未检测到 .venv，请先运行 install_gui_env.bat
  exit /b 1
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

pyinstaller --noconfirm --clean --windowed --name EdgeTTS-GUI gui.py

if %errorlevel% neq 0 (
  echo [ERROR] 打包失败
  exit /b 1
)

echo [OK] 打包完成，EXE 位于 dist\EdgeTTS-GUI\EdgeTTS-GUI.exe
