@echo off
chcp 65001 >nul
echo ====================================
echo 青海子宫内膜癌诊疗平台 - 调试模式
echo ====================================
echo.

cd /d "%~dp0dist"

if not exist "青海子宫内膜癌诊疗平台.exe" (
    echo [错误] 找不到exe文件！
    echo 请先运行打包脚本: python build_exe.py
    echo.
    pause
    exit /b 1
)

echo 正在启动程序...
echo 如果程序崩溃，错误信息会显示在下方
echo ====================================
echo.

"青海子宫内膜癌诊疗平台.exe"

echo.
echo ====================================
echo 程序已退出
echo ====================================
echo.
pause

