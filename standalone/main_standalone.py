"""
单机版主程序 - 可打包成exe
"""
import sys
import os
import webbrowser
import threading
from pathlib import Path
import traceback
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tengda_app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # 单机版模块
    from config_standalone import settings, init_directories
    from database_standalone import init_db, get_db
    from cache_standalone import cache
    from storage_standalone import storage
    
    logger.info("✓ 所有模块导入成功")
except Exception as e:
    logger.error(f"模块导入失败: {e}")
    logger.error(traceback.format_exc())
    input("按Enter键退出...")
    sys.exit(1)

# 导入API路由
try:
    import api_patients
    import api_images
    import api_ai
    import api_followup
    logger.info("✓ API路由模块导入成功")
except Exception as e:
    logger.warning(f"API路由导入失败（部分功能可能不可用）: {e}")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 初始化目录和数据库
    init_directories()
    init_db()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url=None,
    )
    
    # CORS配置（单机版允许所有来源）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 挂载静态文件（前端打包后的文件）
    if settings.STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=settings.STATIC_DIR / "assets"), name="assets")
    
    # 根路径返回前端页面
    @app.get("/", response_class=HTMLResponse)
    async def root():
        index_file = settings.STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return """
        <html>
            <head><title>青海子宫内膜癌智能诊疗平台</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1>🏥 青海子宫内膜癌智能诊疗平台（单机版）</h1>
                <h2>✅ 系统启动成功！</h2>
                <p>数据目录: {}</p>
                <p>访问 <a href="/api/docs">/api/docs</a> 查看API文档</p>
                <p>访问 <a href="/status">/status</a> 查看系统状态</p>
            </body>
        </html>
        """.format(settings.DATA_DIR)
    
    # 系统状态
    @app.get("/status")
    async def status():
        storage_stats = storage.get_storage_stats()
        return {
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "running",
            "database": str(settings.DATABASE_URL),
            "data_dir": str(settings.DATA_DIR),
            "storage_stats": storage_stats,
        }
    
    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    # 注册API路由
    try:
        app.include_router(api_patients.router, prefix="/api/v1/patients", tags=["患者管理"])
        app.include_router(api_images.router, prefix="/api/v1/images", tags=["影像管理"])
        app.include_router(api_ai.router, prefix="/api/v1/ai", tags=["AI分析"])
        app.include_router(api_followup.router, prefix="/api/v1/followup", tags=["随访管理"])
        logger.info("✓ API路由注册成功")
    except Exception as e:
        logger.warning(f"API路由注册失败: {e}")
    
    return app


def open_browser():
    """启动后自动打开浏览器"""
    import time
    time.sleep(2)  # 等待服务器启动
    webbrowser.open(f"http://{settings.HOST}:{settings.PORT}")


def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info(f"  {settings.APP_NAME}")
        logger.info(f"  版本: {settings.VERSION}")
        logger.info("=" * 60)
        logger.info(f"  数据目录: {settings.DATA_DIR}")
        logger.info(f"  访问地址: http://{settings.HOST}:{settings.PORT}")
        logger.info("=" * 60)
        logger.info("\n正在启动服务器...")
        
        # 创建应用
        logger.info("正在创建FastAPI应用...")
        app = create_app()
        logger.info("✓ FastAPI应用创建成功")
        
        # 自动打开浏览器
        if not settings.DEBUG:
            logger.info("准备自动打开浏览器...")
            threading.Thread(target=open_browser, daemon=True).start()
        
        # 启动服务器
        logger.info("正在启动Uvicorn服务器...")
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            log_level="info" if settings.DEBUG else "warning"
        )
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("程序启动失败！")
        logger.error("=" * 60)
        logger.error(f"错误信息: {e}")
        logger.error("\n详细错误:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        input("\n按Enter键退出...")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n未捕获的错误: {e}")
        logger.error(traceback.format_exc())
        input("\n按Enter键退出...")
        sys.exit(1)

