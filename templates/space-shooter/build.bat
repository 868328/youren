@echo off
REM build.bat — Windows 端一键构建脚本
REM
REM 功能: 直接使用 Godot headless 导出 Windows Desktop 版本
REM 用法: 双击运行, 或在终端执行 build.bat
REM
REM 前置条件:
REM   1. Godot 4.6 已安装 (修改下方 GODOT_PATH)
REM   2. 项目位于 D:\openclawworkspace\game-dev\projects\space-shooter\
REM

setlocal enabledelayedexpansion

REM ── 配置 ──────────────────────────────────────────────────────────────
set PROJECT_PATH=D:\openclawworkspace\game-dev\projects\space-shooter
set EXPORT_DIR=%PROJECT_PATH%\export
set GODOT_PATH=E:\godot\Godot_v4.6-stable_win64.exe

REM ── 字体颜色 ─────────────────────────────────────────────────────────
set ESC=
set RED=%ESC%[31m
set GREEN=%ESC%[32m
set YELLOW=%ESC%[33m
set CYAN=%ESC%[36m
set NC=%ESC%[0m

echo.
echo %CYAN%╔══════════════════════════════════════════╗%NC%
echo %CYAN%║     🚀  打飞机 — 构建脚本 (Windows)     ║%NC%
echo %CYAN%║     Godot 4.6 ^| Windows Desktop          ║%NC%
echo %CYAN%╚══════════════════════════════════════════╝%NC%
echo.

REM ── 检查 Godot ─────────────────────────────────────────────────────
if not exist "%GODOT_PATH%" (
    echo %RED%[ERROR] Godot 未找到: %GODOT_PATH%%NC%
    echo %YELLOW%[INFO]  请修改本脚本头部 GODOT_PATH 变量%NC%
    echo %YELLOW%[INFO]  或在 Windows agent.py 中配置路径%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK]    Godot: %GODOT_PATH%%NC%

REM ── 检查项目目录 ────────────────────────────────────────────────────
if not exist "%PROJECT_PATH%\project.godot" (
    echo %RED%[ERROR] 项目目录无效: %PROJECT_PATH%%NC%
    echo %YELLOW%[INFO]  未找到 project.godot%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK]    项目: %PROJECT_PATH%%NC%

REM ── 创建导出目录 ────────────────────────────────────────────────────
if not exist "%EXPORT_DIR%" (
    mkdir "%EXPORT_DIR%"
    echo %YELLOW%[INFO]  创建导出目录%NC%
)

REM ── 清除旧的导出文件 ───────────────────────────────────────────────
echo %CYAN%[INFO]  清理旧导出文件...%NC%
del /q "%EXPORT_DIR%\*.*" >nul 2>nul

REM ── 执行导出 ────────────────────────────────────────────────────────
echo.
echo %CYAN%[INFO]  开始导出 Windows Desktop 版本...%NC%
echo.

"%GODOT_PATH%" --headless --path "%PROJECT_PATH%" --export-release "Windows Desktop"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %RED%[ERROR] Godot 导出失败 (exit code: %ERRORLEVEL%)%NC%
    echo %YELLOW%[INFO]  请检查 Godot 控制台输出以获取详细错误信息%NC%
    pause
    exit /b 1
)

echo.
echo %GREEN%[OK]    Godot 导出命令执行成功%NC%

REM ── 检查导出结果 ───────────────────────────────────────────────────
echo.
echo %CYAN%[INFO]  检查导出结果...%NC%

set EXE_COUNT=0
for %%f in ("%EXPORT_DIR%\*.exe") do set /a EXE_COUNT+=1

set PCK_COUNT=0
for %%f in ("%EXPORT_DIR%\*.pck") do set /a PCK_COUNT+=1

echo.
echo %GREEN%📦 导出目录: %EXPORT_DIR%%NC%
dir "%EXPORT_DIR%" /o-d

echo.
if %EXE_COUNT% GTR 0 (
    echo %GREEN%[OK]    找到 %EXE_COUNT% 个可执行文件%NC%
) else (
    echo %YELLOW%[WARN]  未找到 .exe 文件%NC%
)

if %PCK_COUNT% GTR 0 (
    echo %GREEN%[OK]    找到 %PCK_COUNT% 个数据包文件%NC%
)

echo.
echo %GREEN%========================================%NC%
echo %GREEN%  ✅  构建完成!%NC%
echo %GREEN%========================================%NC%
echo.

pause
exit /b 0
