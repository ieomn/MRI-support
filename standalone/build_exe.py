"""
PyInstaller打包脚本
生成单个exe文件
"""
import PyInstaller.__main__
import shutil
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 清理旧的构建文件
for folder in ['build', 'dist']:
    folder_path = ROOT_DIR / folder
    if folder_path.exists():
        shutil.rmtree(folder_path)
        print(f"✓ 清理 {folder}")

print("\n开始打包...")
print("=" * 60)

# 检查前端文件是否存在
frontend_dist = ROOT_DIR.parent / 'frontend-doctor' / 'dist'
if not frontend_dist.exists():
    print("=" * 60)
    print("⚠️  警告：前端打包文件不存在！")
    print(f"路径: {frontend_dist}")
    print("\n请先打包前端：")
    print("  cd ../frontend-doctor")
    print("  npm run build")
    print("=" * 60)
    input("\n按Enter键继续（跳过前端）或Ctrl+C取消...")

# PyInstaller配置
pyinstaller_args = [
    'main_standalone.py',               # 主程序
    '--name=青海子宫内膜癌诊疗平台',        # 程序名称
    '--onefile',                        # 打包成单个exe
    '--console',                        # 显示控制台窗口（方便调试）
    # '--icon=icon.ico',                # 图标（如果有的话）
]

# 添加前端文件（如果存在）
if frontend_dist.exists():
    # Windows使用分号，Linux/Mac使用冒号
    pyinstaller_args.append(f'--add-data={frontend_dist};static')
    print(f"✓ 将打包前端文件: {frontend_dist}")

pyinstaller_args.extend([
    # 隐藏导入
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.protocols.websockets',
    '--hidden-import=uvicorn.protocols.websockets.auto',
    '--hidden-import=uvicorn.lifespan',
    '--hidden-import=uvicorn.lifespan.on',
    
    # 排除不需要的模块
    '--exclude-module=pytest',
    '--exclude-module=matplotlib',
    
    # 优化
    '--clean',                          # 清理临时文件
    '--noconfirm',                      # 不询问确认
])

PyInstaller.__main__.run(pyinstaller_args)

print("=" * 60)
print("✅ 打包完成！")
print(f"✓ exe文件位置: {ROOT_DIR / 'dist' / '青海子宫内膜癌诊疗平台.exe'}")
print("\n使用说明:")
print("1. 直接双击exe文件即可运行")
print("2. 首次运行会在用户目录创建TengdaData文件夹")
print("3. 程序会自动打开浏览器访问系统")
print("=" * 60)

