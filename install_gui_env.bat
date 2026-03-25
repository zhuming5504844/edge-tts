@echo off
chcp 65001 >nul
setlocal

where py >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] 未找到 Python 启动器 py，请先安装 Python 3.10+
  exit /b 1
)

if not exist .venv (
  echo [INFO] 创建虚拟环境 .venv
  py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-gui.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
  echo [ERROR] 依赖安装失败
  exit /b 1
)

echo [OK] GUI 环境安装完成。
echo [TIP] 运行命令: .venv\Scripts\python gui.py
