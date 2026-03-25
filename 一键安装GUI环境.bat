@echo off
setlocal EnableExtensions
chcp 65001 >nul

cd /d "%~dp0"

set "PY_CMD="
where python >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
    where py >nul 2>&1 && set "PY_CMD=py -3"
)
if not defined PY_CMD (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+。
    goto :fail
)

if not exist ".venv\Scripts\python.exe" (
    echo [环境] 正在创建 .venv ...
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :fail
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :fail

echo [依赖] 更新 pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [依赖] 安装 edge-tts (开发模式)...
python -m pip install -e .
if errorlevel 1 goto :fail

echo [依赖] 安装 GUI 打包工具...
python -m pip install -r gui_requirements.txt
if errorlevel 1 goto :fail

echo [完成] GUI 运行与打包环境安装成功。
goto :ok

:fail
echo [失败] 安装过程中出现错误。
pause
exit /b 1

:ok
pause
exit /b 0
