"""
患者数据模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Enum, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class GenderEnum(str, enum.Enum):
    """性别枚举"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(Base):
    """患者表"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_no = Column(String(50), unique=True, index=True, nullable=False, comment="患者编号")
    name = Column(String(100), nullable=False, comment="姓名")
    gender = Column(Enum(GenderEnum), nullable=False, comment="性别")
    birth_date = Column(Date, comment="出生日期")
    id_card = Column(String(18), comment="身份证号(加密)")
    phone = Column(String(20), comment="联系电话")
    address = Column(String(500), comment="家庭地址")
    
    # 就诊信息
    admission_date = Column(Date, comment="入院日期")
    hospital = Column(String(200), comment="所属医院")
    department = Column(String(100), comment="科室")
    attending_doctor = Column(String(100), comment="主治医生")
    
    # 诊断信息
    diagnosis = Column(Text, comment="诊断结果")
    stage = Column(String(50), comment="分期")
    grade = Column(String(50), comment="分级")
    
    # 病理信息 (JSON格式,灵活扩展)
    pathology_info = Column(JSON, comment="病理信息")
    genetic_info = Column(JSON, comment="基因信息")
    
    # 治疗方案
    treatment_plan = Column(Text, comment="治疗方案")
    surgery_date = Column(Date, comment="手术日期")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "patient_no": self.patient_no,
            "name": self.name,
            "gender": self.gender.value if self.gender else None,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "phone": self.phone,
            "address": self.address,
            "admission_date": self.admission_date.isoformat() if self.admission_date else None,
            "hospital": self.hospital,
            "diagnosis": self.diagnosis,
            "stage": self.stage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

