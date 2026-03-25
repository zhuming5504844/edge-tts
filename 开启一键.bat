@echo off
setlocal EnableExtensions
chcp 65001 >nul


if /i not "%~1"=="--direct" (
    echo %CMDCMDLINE% | findstr /i /c:"/c" >nul
    if not errorlevel 1 (
        start "edge-tts 一键启动" cmd /k call ""%~f0" --direct %*"
        exit /b
    )
)
if /i "%~1"=="--direct" shift

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR="
if exist "%SCRIPT_DIR%setup.py" set "PROJECT_DIR=%SCRIPT_DIR%"
if not defined PROJECT_DIR if exist "%SCRIPT_DIR%edge-tts\setup.py" set "PROJECT_DIR=%SCRIPT_DIR%edge-tts\"

if not defined PROJECT_DIR (
    echo [错误] 在当前路径未找到 edge-tts 项目。
    echo [提示] 当前脚本路径: %SCRIPT_DIR%
    echo [提示] 请把本 .bat 放到 edge-tts 项目根目录，或放在其上一级目录。
    echo [提示] 例如: C:\Users\Administrator\Desktop\edge-tts
    goto :end_fail
)

cd /d "%PROJECT_DIR%"
echo [OK] 项目目录: %CD%

set "PY_CMD="
where python >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
    where py >nul 2>&1 && set "PY_CMD=py -3"
)
if not defined PY_CMD (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+ 并勾选 ^"Add Python to PATH^"。
    goto :end_fail
)

if not exist ".venv\Scripts\python.exe" (
    echo [环境] 正在创建 .venv 虚拟环境...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败。
        goto :end_fail
    )
)

echo [OK] 虚拟环境已就绪

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败。
    goto :end_fail
)

echo [依赖] 安装/更新 pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [错误] pip 更新失败。
    goto :end_fail
)

echo [依赖] 安装/更新 edge-tts...
python -m pip install -e .
if errorlevel 1 (
    echo [错误] edge-tts 安装失败。
    goto :end_fail
)

echo [OK] Python 依赖已就绪

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 ffmpeg，若你需要 mpv 播放可安装:
    echo [提示] winget install --id Gyan.FFmpeg -e
) else (
    echo [OK] ffmpeg 已就绪
)

echo [启动] 正在启动 edge-playback...
echo ===========================

if "%~1"=="" (
    set "TEXT=你好，这里是 edge-tts 一键启动测试。"
) else (
    set "TEXT=%*"
)

edge-playback --text "%TEXT%"
if errorlevel 1 (
    echo [错误] 启动失败，请查看上方日志。
    goto :end_fail
)

echo [OK] 已退出。
goto :end_ok

:end_fail
echo.
echo [失败] 执行中断，请按任意键退出。
pause >nul
exit /b 1

:end_ok
echo [完成] 请按任意键关闭窗口。
pause >nul
exit /b 0
