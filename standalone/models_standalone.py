"""
单机版数据模型 - 简化版
使用SQLite，移除了asyncpg相关的特性
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from database_standalone import Base
import enum


# ==================== 患者模型 ====================

class Patient(Base):
    """患者表"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    gender = Column(String(20))
    birth_date = Column(Date)
    phone = Column(String(20))
    address = Column(String(500))
    
    # 就诊信息
    admission_date = Column(Date)
    hospital = Column(String(200))
    diagnosis = Column(Text)
    stage = Column(String(50))
    
    # 病理信息（JSON）
    pathology_info = Column(JSON)
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Integer, default=0)


# ==================== 影像模型 ====================

class MRISeries(Base):
    """MRI序列表"""
    __tablename__ = "mri_series"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # DICOM信息
    series_uid = Column(String(100), unique=True, nullable=False)
    series_description = Column(String(200))
    
    # 存储信息
    storage_path = Column(String(500), nullable=False)
    file_count = Column(Integer)
    thumbnail_path = Column(String(500))
    
    # 元数据
    image_metadata = Column(JSON)
    
    # 系统字段
    upload_time = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())


class Annotation(Base):
    """标注数据表"""
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("mri_series.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # 标注信息
    annotation_type = Column(String(50))
    annotation_data = Column(JSON, nullable=False)
    
    # 标注者
    annotator_name = Column(String(100))
    
    # AI相关
    ai_confidence = Column(Float)
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())


class AIAnalysisResult(Base):
    """AI分析结果表"""
    __tablename__ = "ai_analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("mri_series.id"))
    
    # 分析类型
    analysis_type = Column(String(50), nullable=False)
    
    # 分割结果
    tumor_volume = Column(Float)
    
    # 预后预测
    prognosis_score = Column(Float)
    risk_level = Column(String(20))
    
    # 模型信息
    model_name = Column(String(100))
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())


# ==================== 随访模型 ====================

class FollowUpPlan(Base):
    """随访计划表"""
    __tablename__ = "followup_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    plan_name = Column(String(200))
    start_date = Column(DateTime)
    schedule_config = Column(JSON, nullable=False)
    
    doctor_name = Column(String(100))
    is_active = Column(Integer, default=1)
    
    created_at = Column(DateTime, server_default=func.now())


class FollowUpTask(Base):
    """随访任务表"""
    __tablename__ = "followup_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("followup_plans.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    task_title = Column(String(200), nullable=False)
    task_description = Column(Text)
    
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime)
    
    status = Column(String(20), default="pending")
    
    created_at = Column(DateTime, server_default=func.now())


class FollowUpRecord(Base):
    """随访记录表"""
    __tablename__ = "followup_records"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("followup_tasks.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    record_type = Column(String(50))
    record_data = Column(JSON)
    
    doctor_note = Column(Text)
    
    submit_time = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

