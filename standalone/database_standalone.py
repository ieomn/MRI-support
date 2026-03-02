"""
单机版数据库 - 使用SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from config_standalone import settings

# 创建SQLite引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite特殊配置
    poolclass=StaticPool,  # 单机版使用静态连接池
    echo=settings.DEBUG,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """数据库会话依赖注入（FastAPI专用）"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    # 导入所有模型
    from models_standalone import Patient, MRISeries, Annotation, AIAnalysisResult
    from models_standalone import FollowUpPlan, FollowUpTask, FollowUpRecord
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建完成")


def backup_database():
    """备份数据库"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = settings.BACKUP_DIR / f"tengda_backup_{timestamp}.db"
    
    # 获取数据库文件路径
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_file = db_url.replace("sqlite:///", "")
    else:
        db_file = db_url.replace("sqlite://", "")
    
    shutil.copy2(db_file, backup_file)
    
    print(f"✓ 数据库备份完成: {backup_file}")
    return backup_file

