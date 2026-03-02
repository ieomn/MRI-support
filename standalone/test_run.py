"""
测试运行脚本 - 不打包直接运行，方便调试
"""
import sys
import traceback

print("=" * 60)
print("测试运行单机版程序")
print("=" * 60)
print()

# 测试导入
print("1. 测试基础模块导入...")
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import pydantic
    print("   ✓ 基础模块导入成功")
except Exception as e:
    print(f"   ✗ 基础模块导入失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("2. 测试单机版配置模块...")
try:
    from config_standalone import settings, init_directories
    print(f"   ✓ 配置加载成功")
    print(f"   - 数据目录: {settings.DATA_DIR}")
    print(f"   - 数据库: {settings.DATABASE_URL}")
except Exception as e:
    print(f"   ✗ 配置加载失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("3. 初始化目录...")
try:
    init_directories()
    print(f"   ✓ 目录初始化成功")
except Exception as e:
    print(f"   ✗ 目录初始化失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("4. 测试数据库模块...")
try:
    from database_standalone import init_db
    init_db()
    print("   ✓ 数据库初始化成功")
except Exception as e:
    print(f"   ✗ 数据库初始化失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("5. 测试缓存模块...")
try:
    from cache_standalone import cache
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    assert value == "test_value"
    print("   ✓ 缓存测试成功")
except Exception as e:
    print(f"   ✗ 缓存测试失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("6. 测试存储模块...")
try:
    from storage_standalone import storage
    stats = storage.get_storage_stats()
    print(f"   ✓ 存储模块测试成功")
    print(f"   - 存储大小: {stats['total_size_mb']:.2f} MB")
except Exception as e:
    print(f"   ✗ 存储模块测试失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("7. 测试主程序...")
try:
    from main_standalone import create_app
    app = create_app()
    print("   ✓ FastAPI应用创建成功")
except Exception as e:
    print(f"   ✗ FastAPI应用创建失败: {e}")
    traceback.print_exc()
    input("\n按Enter键退出...")
    sys.exit(1)

print()
print("=" * 60)
print("✅ 所有测试通过！可以尝试启动服务器")
print("=" * 60)
print()
print("是否启动服务器测试？(y/n)")

choice = input().lower().strip()
if choice == 'y':
    print()
    print("启动服务器...")
    print("访问地址: http://127.0.0.1:8888")
    print("按 Ctrl+C 停止服务器")
    print()
    
    try:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8888)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"\n服务器启动失败: {e}")
        traceback.print_exc()
else:
    print("跳过服务器测试")

print()
input("按Enter键退出...")

