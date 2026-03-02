"""
配置管理模块
支持环境变量和.env文件配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "青海子宫内膜癌智能诊疗平台"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/endometrial_cancer"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis缓存配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 缓存过期时间配置（秒）
    CACHE_PATIENT_INFO_TTL: int = 3600  # 患者信息 1小时
    CACHE_PATIENT_LIST_TTL: int = 600   # 患者列表 10分钟
    CACHE_DICOM_META_TTL: int = 86400   # DICOM元数据 24小时
    CACHE_AI_RESULT_TTL: int = 0        # AI结果永久缓存(0=不过期)
    CACHE_SESSION_TTL: int = 1800       # 会话 30分钟
    
    # MinIO对象存储配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_DICOM: str = "dicom-images"
    MINIO_BUCKET_REPORTS: str = "patient-reports"
    
    # JWT安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 文件上传限制
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_DICOM_EXTENSIONS: list = [".dcm", ".dicom", ".DCM"]
    
    # AI模型配置（本地 U-Net / Regression）
    AI_MODEL_PATH: str = "./models"
    UNET_MODEL_FILE: str = "unet_segmentation.pth"
    REGRESSION_MODEL_FILE: str = "prognosis_regression.pkl"
    AI_INFERENCE_TIMEOUT: int = 30  # 秒
    
    # MedGemma 远程推理配置（AutoDL 云 GPU）
    MEDGEMMA_API_URL: str = "http://localhost:8080"
    MEDGEMMA_API_TIMEOUT: int = 180  # MedGemma 27B 推理较慢，需更长超时
    MEDGEMMA_MAX_RETRIES: int = 2
    MEDGEMMA_MODEL_ID: str = "google/medgemma-27b-it"
    
    # Celery任务队列配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # 微信配置（随访提醒）
    WECHAT_APPID: Optional[str] = None
    WECHAT_SECRET: Optional[str] = None
    WECHAT_TEMPLATE_ID: Optional[str] = None
    
    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 全局配置实例
settings = get_settings()

