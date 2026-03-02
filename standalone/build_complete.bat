@echo off
chcp 65001 >nul
echo ====================================
echo 完整打包流程
echo ====================================
echo.

echo [步骤1/5] 检查环境...
where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到npm，请先安装Node.js
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到python
    pause
    exit /b 1
)

echo ✓ 环境检查通过
echo.

echo [步骤2/5] 打包前端...
cd ..\frontend-doctor
if not exist "package.json" (
    echo ❌ 找不到前端项目
    pause
    exit /b 1
)

echo 正在打包前端（需要1-2分钟）...
call npm run build
if errorlevel 1 (
    echo ❌ 前端打包失败
    pause
    exit /b 1
)

echo ✓ 前端打包完成
echo.

echo [步骤3/5] 初始化演示数据...
cd ..\standalone
python init_demo_data.py
echo.

echo [步骤4/5] 打包后端为exe...
echo 正在打包（需要5-10分钟）...
python build_exe.py
if errorlevel 1 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo [步骤5/5] 测试exe...
echo.
echo ====================================
echo ✅ 打包完成！
echo ====================================
echo.
echo exe位置: dist\青海子宫内膜癌诊疗平台.exe
echo.
echo 是否立即运行测试？(Y/N)
set /p choice=

if /i "%choice%"=="Y" (
    echo.
    echo 启动测试...
    cd dist
    "青海子宫内膜癌诊疗平台.exe"
)

pause

