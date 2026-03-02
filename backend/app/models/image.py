"""
影像数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MRISeries(Base):
    """MRI序列表"""
    __tablename__ = "mri_series"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # DICOM基本信息
    series_uid = Column(String(100), unique=True, nullable=False, comment="序列UID")
    study_uid = Column(String(100), nullable=False, comment="检查UID")
    modality = Column(String(20), comment="成像方式")
    series_description = Column(String(200), comment="序列描述")
    series_number = Column(Integer, comment="序列号")
    
    # 存储信息
    storage_path = Column(String(500), nullable=False, comment="MinIO存储路径")
    file_count = Column(Integer, comment="文件数量")
    total_size = Column(Integer, comment="总大小(bytes)")
    
    # 影像参数
    image_metadata = Column(JSON, comment="影像元数据(窗宽窗位等)")
    slice_thickness = Column(Float, comment="层厚")
    pixel_spacing = Column(String(50), comment="像素间距")
    
    # 缩略图
    thumbnail_path = Column(String(500), comment="缩略图路径")
    
    # 系统字段
    upload_time = Column(DateTime, server_default=func.now(), comment="上传时间")
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    annotations = relationship("Annotation", back_populates="series")


class Annotation(Base):
    """标注数据表"""
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("mri_series.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # 标注信息
    annotation_type = Column(String(50), comment="标注类型(manual/ai/reviewed)")
    annotation_data = Column(JSON, nullable=False, comment="标注数据(坐标、轮廓)")
    slice_index = Column(Integer, comment="切片索引")
    
    # 标注者信息
    annotator_id = Column(Integer, comment="标注者ID")
    annotator_name = Column(String(100), comment="标注者姓名")
    
    # 审核信息
    is_reviewed = Column(Integer, default=0, comment="是否已审核")
    reviewer_id = Column(Integer, comment="审核者ID")
    review_time = Column(DateTime, comment="审核时间")
    
    # AI相关
    ai_confidence = Column(Float, comment="AI置信度")
    ai_model_version = Column(String(50), comment="AI模型版本")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    series = relationship("MRISeries", back_populates="annotations")


class AIAnalysisResult(Base):
    """AI分析结果表"""
    __tablename__ = "ai_analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("mri_series.id"), index=True)
    
    # 分析类型
    analysis_type = Column(String(50), nullable=False, comment="分析类型(segmentation/prediction)")
    
    # 分割结果
    segmentation_mask_path = Column(String(500), comment="分割掩码文件路径")
    tumor_volume = Column(Float, comment="肿瘤体积(cm³)")
    
    # 影像组学特征
    radiomics_features = Column(JSON, comment="影像组学特征")
    
    # 预后预测结果
    prognosis_score = Column(Float, comment="预后评分")
    risk_level = Column(String(20), comment="风险等级(low/medium/high)")
    recurrence_probability = Column(Float, comment="复发概率")
    survival_prediction = Column(JSON, comment="生存期预测")
    
    # 模型信息
    model_name = Column(String(100), comment="模型名称")
    model_version = Column(String(50), comment="模型版本")
    inference_time = Column(Float, comment="推理耗时(秒)")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())

