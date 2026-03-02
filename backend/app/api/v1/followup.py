"""
随访管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.followup import FollowUpPlan, FollowUpTask, FollowUpRecord, FollowUpStatusEnum

router = APIRouter()


# ==================== Pydantic模型 ====================

class FollowUpPlanCreate(BaseModel):
    """创建随访计划"""
    patient_id: int
    plan_name: str
    start_date: datetime
    schedule_config: List[dict]  # [{"day": 30, "tasks": ["问卷", "影像"]}]
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None


class FollowUpTaskCreate(BaseModel):
    """创建随访任务"""
    plan_id: int
    patient_id: int
    task_title: str
    task_description: Optional[str] = None
    task_type: str
    scheduled_date: datetime


class FollowUpRecordCreate(BaseModel):
    """创建随访记录"""
    task_id: int
    patient_id: int
    record_type: str
    record_data: dict
    questionnaire_answers: Optional[dict] = None
    uploaded_files: Optional[List[str]] = None


# ==================== API端点 ====================

@router.post("/plans", response_model=dict)
async def create_followup_plan(
    data: FollowUpPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建随访计划 (F-FU-01)
    """
    try:
        plan = FollowUpPlan(
            patient_id=data.patient_id,
            plan_name=data.plan_name,
            start_date=data.start_date,
            schedule_config=data.schedule_config,
            doctor_id=data.doctor_id,
            doctor_name=data.doctor_name,
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # 根据配置自动创建任务
        tasks_created = []
        for config in data.schedule_config:
            task_date = data.start_date + timedelta(days=config["day"])
            for task_name in config.get("tasks", []):
                task = FollowUpTask(
                    plan_id=plan.id,
                    patient_id=data.patient_id,
                    task_title=task_name,
                    task_type="questionnaire" if "问卷" in task_name else "upload",
                    scheduled_date=task_date,
                    status=FollowUpStatusEnum.PENDING,
                )
                db.add(task)
                tasks_created.append(task)
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"随访计划创建成功，已生成 {len(tasks_created)} 个任务",
            "data": {
                "plan_id": plan.id,
                "tasks_count": len(tasks_created)
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建随访计划失败: {str(e)}")


@router.get("/plans/patient/{patient_id}", response_model=dict)
async def get_patient_followup_plans(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取患者的随访计划"""
    try:
        result = await db.execute(
            select(FollowUpPlan).where(
                FollowUpPlan.patient_id == patient_id,
                FollowUpPlan.is_active == 1
            )
        )
        plans = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "plan_name": p.plan_name,
                    "start_date": p.start_date.isoformat() if p.start_date else None,
                    "doctor_name": p.doctor_name,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in plans
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询随访计划失败: {str(e)}")


@router.get("/tasks/patient/{patient_id}", response_model=dict)
async def get_patient_tasks(
    patient_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取患者的随访任务 (F-FU-04)
    """
    try:
        query = select(FollowUpTask).where(FollowUpTask.patient_id == patient_id)
        
        if status:
            query = query.where(FollowUpTask.status == status)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": t.id,
                    "task_title": t.task_title,
                    "task_description": t.task_description,
                    "task_type": t.task_type,
                    "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                    "completed_date": t.completed_date.isoformat() if t.completed_date else None,
                    "status": t.status.value,
                    "reminder_sent": t.reminder_sent,
                }
                for t in tasks
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询随访任务失败: {str(e)}")


@router.post("/records", response_model=dict)
async def create_followup_record(
    data: FollowUpRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建随访记录（患者提交）
    """
    try:
        record = FollowUpRecord(
            task_id=data.task_id,
            patient_id=data.patient_id,
            record_type=data.record_type,
            record_data=data.record_data,
            questionnaire_answers=data.questionnaire_answers,
            uploaded_files=data.uploaded_files,
        )
        
        db.add(record)
        
        # 更新任务状态
        result = await db.execute(
            select(FollowUpTask).where(FollowUpTask.id == data.task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = FollowUpStatusEnum.COMPLETED
            task.completed_date = datetime.now()
        
        await db.commit()
        
        return {
            "success": True,
            "message": "随访记录提交成功",
            "data": {"record_id": record.id}
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建随访记录失败: {str(e)}")


@router.get("/dashboard", response_model=dict)
async def get_followup_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    获取随访看板数据 (F-FU-04)
    """
    try:
        from sqlalchemy import func
        
        # 统计各状态任务数量
        result = await db.execute(
            select(
                FollowUpTask.status,
                func.count(FollowUpTask.id)
            ).group_by(FollowUpTask.status)
        )
        status_stats = {status.value: count for status, count in result.all()}
        
        # 获取逾期任务
        overdue_result = await db.execute(
            select(FollowUpTask).where(
                FollowUpTask.status == FollowUpStatusEnum.PENDING,
                FollowUpTask.scheduled_date < datetime.now()
            ).limit(10)
        )
        overdue_tasks = overdue_result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "status_stats": status_stats,
                "overdue_tasks": [
                    {
                        "id": t.id,
                        "patient_id": t.patient_id,
                        "task_title": t.task_title,
                        "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                    }
                    for t in overdue_tasks
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取看板数据失败: {str(e)}")

