"""
FastAPI主应用入口
青海子宫内膜癌智能诊疗平台
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.config import settings
from app.core.database import init_db, close_db
from app.core.cache import cache_manager
from app.ml.medgemma_service import medgemma_service
from app.api.v1 import patients, images, annotations, followup, ai

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL,
    encoding="utf-8"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 应用启动中...")
    
    # 初始化数据库
    await init_db()
    logger.info("✓ 数据库初始化完成")
    
    # 连接Redis
    await cache_manager.connect()
    logger.info("✓ Redis缓存连接成功")
    
    # 预加载AI模型（可选，本地 U-Net / Regression）
    # from app.ml.unet_model import unet_service
    # from app.ml.regression_model import regression_service
    # unet_service.load_model()
    # regression_service.load_model()
    # logger.info("✓ 本地AI模型加载完成")
    
    # 连接 MedGemma 远程推理服务
    await medgemma_service.connect()
    medgemma_status = await medgemma_service.health_check()
    if medgemma_status.get("status") == "healthy":
        logger.info(f"✓ MedGemma 推理服务连接成功 (GPU: {medgemma_status.get('gpu', 'N/A')})")
    else:
        logger.warning(f"⚠ MedGemma 推理服务不可用: {medgemma_status.get('error', '未知')}")
        logger.warning("  影像分析和 LLM 预后功能将暂不可用，其他功能正常运行")
    
    logger.info(f"🎉 {settings.APP_NAME} v{settings.VERSION} 启动成功!")
    
    yield
    
    # 关闭时执行
    logger.info("📴 应用关闭中...")
    await medgemma_service.close()
    await cache_manager.close()
    await close_db()
    logger.info("✓ 资源清理完成")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="基于AI的医疗辅助诊疗平台",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )


# 健康检查端点
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected",
        "cache": "connected"
    }


# 注册API路由
app.include_router(patients.router, prefix="/api/v1/patients", tags=["患者管理"])
app.include_router(images.router, prefix="/api/v1/images", tags=["影像管理"])
app.include_router(annotations.router, prefix="/api/v1/annotations", tags=["标注管理"])
app.include_router(followup.router, prefix="/api/v1/followup", tags=["随访管理"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI分析"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

