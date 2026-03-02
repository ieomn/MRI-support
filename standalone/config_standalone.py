"""
单机版配置 - 使用嵌入式数据库和本地存储
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os
import sys


class StandaloneSettings(BaseSettings):
    """单机版配置"""
    
    # 基础配置
    APP_NAME: str = "青海子宫内膜癌智能诊疗平台（单机版）"
    VERSION: str = "1.0.0-standalone"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8888
    
    # 文件上传限制
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    
    # JWT配置
    SECRET_KEY: str = "tengda-standalone-secret-key-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8小时
    
    # 缓存配置
    CACHE_SIZE_LIMIT: int = 1024 * 1024 * 1024  # 1GB
    
    # AI模型文件名
    UNET_MODEL_FILE: str = "unet_segmentation.pth"
    REGRESSION_MODEL_FILE: str = "prognosis_regression.pkl"
    
    # 自动备份
    AUTO_BACKUP: bool = True
    BACKUP_INTERVAL_DAYS: int = 7
    
    class Config:
        case_sensitive = True
    
    # ==================== 路径属性 ====================
    
    @property
    def APP_DIR(self) -> Path:
        """应用目录"""
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的路径
            return Path(sys._MEIPASS)
        else:
            # 开发环境
            return Path(__file__).parent
    
    @property
    def DATA_DIR(self) -> Path:
        """数据目录"""
        if getattr(sys, 'frozen', False):
            # 打包后：使用用户主目录
            data_dir = Path(os.path.expanduser("~")) / "TengdaData"
        else:
            # 开发环境：使用当前目录
            data_dir = Path(__file__).parent / "data"
        
        # 确保目录存在
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    @property
    def DATABASE_URL(self) -> str:
        """数据库URL"""
        db_file = self.DATA_DIR / 'tengda.db'
        return f"sqlite:///{db_file}"
    
    @property
    def CACHE_DIR(self) -> Path:
        """缓存目录"""
        cache_dir = self.DATA_DIR / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    @property
    def STORAGE_DIR(self) -> Path:
        """存储根目录"""
        storage_dir = self.DATA_DIR / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir
    
    @property
    def DICOM_DIR(self) -> Path:
        """DICOM文件目录"""
        dicom_dir = self.STORAGE_DIR / "dicom"
        dicom_dir.mkdir(parents=True, exist_ok=True)
        return dicom_dir
    
    @property
    def REPORTS_DIR(self) -> Path:
        """报告文件目录"""
        reports_dir = self.STORAGE_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir
    
    @property
    def THUMBNAILS_DIR(self) -> Path:
        """缩略图目录"""
        thumbnails_dir = self.STORAGE_DIR / "thumbnails"
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        return thumbnails_dir
    
    @property
    def AI_MODEL_DIR(self) -> Path:
        """AI模型目录"""
        model_dir = self.DATA_DIR / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir
    
    @property
    def BACKUP_DIR(self) -> Path:
        """备份目录"""
        backup_dir = self.DATA_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    @property
    def STATIC_DIR(self) -> Path:
        """静态文件目录（前端）"""
        return self.APP_DIR / "static"


# 创建全局配置实例
settings = StandaloneSettings()


def init_directories():
    """初始化所有必要的目录"""
    directories = [
        settings.DATA_DIR,
        settings.CACHE_DIR,
        settings.STORAGE_DIR,
        settings.DICOM_DIR,
        settings.REPORTS_DIR,
        settings.THUMBNAILS_DIR,
        settings.AI_MODEL_DIR,
        settings.BACKUP_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ 数据目录初始化完成: {settings.DATA_DIR}")
    return True
