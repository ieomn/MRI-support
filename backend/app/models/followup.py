"""
随访数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class FollowUpStatusEnum(str, enum.Enum):
    """随访状态枚举"""
    PENDING = "pending"          # 待完成
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    OVERDUE = "overdue"          # 逾期
    CANCELLED = "cancelled"      # 已取消


class FollowUpPlan(Base):
    """随访计划表"""
    __tablename__ = "followup_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # 计划信息
    plan_name = Column(String(200), comment="计划名称")
    start_date = Column(DateTime, comment="开始日期")
    end_date = Column(DateTime, comment="结束日期")
    
    # 随访节点配置 (JSON数组)
    # 例: [{"day": 30, "tasks": ["问卷", "影像"]}, {"day": 90, "tasks": [...]}]
    schedule_config = Column(JSON, nullable=False, comment="随访时间节点配置")
    
    # 创建者
    doctor_id = Column(Integer, comment="创建医生ID")
    doctor_name = Column(String(100), comment="创建医生姓名")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FollowUpTask(Base):
    """随访任务表"""
    __tablename__ = "followup_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("followup_plans.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # 任务信息
    task_title = Column(String(200), nullable=False, comment="任务标题")
    task_description = Column(Text, comment="任务描述")
    task_type = Column(String(50), comment="任务类型(questionnaire/upload/call)")
    
    # 时间
    scheduled_date = Column(DateTime, nullable=False, comment="计划完成时间")
    completed_date = Column(DateTime, comment="实际完成时间")
    
    # 状态
    status = Column(Enum(FollowUpStatusEnum), default=FollowUpStatusEnum.PENDING, comment="任务状态")
    
    # 提醒
    reminder_sent = Column(Integer, default=0, comment="是否已发送提醒")
    reminder_time = Column(DateTime, comment="提醒发送时间")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FollowUpRecord(Base):
    """随访记录表"""
    __tablename__ = "followup_records"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("followup_tasks.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # 记录内容
    record_type = Column(String(50), comment="记录类型")
    record_data = Column(JSON, comment="记录数据(问卷答案、上传文件路径等)")
    
    # 问卷相关
    questionnaire_id = Column(Integer, comment="问卷ID")
    questionnaire_answers = Column(JSON, comment="问卷答案")
    
    # 文件上传
    uploaded_files = Column(JSON, comment="上传的文件列表")
    
    # 医生备注
    doctor_note = Column(Text, comment="医生备注")
    doctor_id = Column(Integer, comment="备注医生ID")
    
    # 系统字段
    submit_time = Column(DateTime, server_default=func.now(), comment="提交时间")
    created_at = Column(DateTime, server_default=func.now())

