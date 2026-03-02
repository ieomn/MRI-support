"""
快速测试 - 验证API是否正常工作
"""
import sys
import time
import webbrowser
import threading
from main_standalone import main

print("=" * 60)
print("快速测试服务器")
print("=" * 60)
print()
print("测试内容：")
print("1. 启动服务器")
print("2. 自动打开浏览器")
print("3. 访问患者列表API")
print()
print("按 Ctrl+C 停止服务器")
print("=" * 60)
print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)

