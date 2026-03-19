@echo off
chcp 65001 >nul
echo ============================================================
echo   火焰检测系统 - 快速测试
echo ============================================================
echo.

REM 清理旧的记录文件
echo [1/3] 清理旧的截图文件...
del /Q records\*.jpg 2>nul
if exist "records\*.jpg" (
    echo   ⚠ 部分文件未能删除
) else (
    echo   ✓ 清理完成
)
echo.

REM 启动主程序
echo [2/3] 启动主程序...
echo   ℹ 按 Ctrl+C 可随时退出
echo.
echo ============================================================
echo.

d:\桌面\中俄比赛\.conda\python.exe pc/main.py

echo.
echo ============================================================
echo [3/3] 程序已结束
echo ============================================================
echo.

REM 检查是否有新的截图
dir /B records\*.jpg 2>nul | findstr /N "^" | findstr "^[1-9]" >nul
if %errorlevel% equ 0 (
    echo ✓ 检测到截图文件:
    dir /B records\*.jpg
    echo.
    echo 最新截图时间:
    for %%f in (records\*.jpg) do (
        echo   %%~tf  %%~zf 字节
    )
) else (
    echo ⚠ 未检测到新的截图文件
)

echo.
echo ============================================================
echo 测试完成
echo ============================================================
pause
