@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [OK] 当前目录: %CD%

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+ 并勾选 ^"Add Python to PATH^"。
    goto :end_fail
)

if not exist ".venv\Scripts\python.exe" (
    echo [环境] 正在创建 .venv 虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败。
        goto :end_fail
    )
)

echo [OK] 虚拟环境已就绪

set "PYTHON=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\python.exe -m pip"

echo [依赖] 安装/更新 pip...
%PIP% install --upgrade pip
if errorlevel 1 (
    echo [错误] pip 更新失败。
    goto :end_fail
)

echo [依赖] 安装/更新 edge-tts...
%PIP% install -e .
if errorlevel 1 (
    echo [错误] edge-tts 安装失败。
    goto :end_fail
)

echo [OK] Python 依赖已就绪

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 ffmpeg，edge-playback 可能无法播放。
    echo [提示] 可执行: winget install --id Gyan.FFmpeg -e
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

%PYTHON% -m edge_playback --text "%TEXT%"
if errorlevel 1 (
    echo [错误] 启动失败，请查看上方日志。
    goto :end_fail
)

echo [OK] 已退出。
goto :eof

:end_fail
echo.
echo [失败] 执行中断，请按任意键退出。
pause >nul
exit /b 1
