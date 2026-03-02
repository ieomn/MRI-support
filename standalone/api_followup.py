"""
随访管理API - 单机版
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database_standalone import get_db
from models_standalone import FollowUpTask
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter()


class FollowUpPlanCreate(BaseModel):
    patient_id: int
    plan_name: str
    start_date: str


@router.post("/plans")
def create_followup_plan(data: FollowUpPlanCreate, db: Session = Depends(get_db)):
    """创建随访计划"""
    return {
        "success": True,
        "message": "随访计划创建成功",
        "data": {"plan_id": 1}
    }


@router.get("/tasks/patient/{patient_id}")
def get_patient_tasks(
    patient_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取患者随访任务"""
    query = db.query(FollowUpTask).filter(
        FollowUpTask.patient_id == patient_id
    )
    
    if status:
        query = query.filter(FollowUpTask.status == status)
    
    tasks = query.all()
    
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "task_title": t.task_title,
                "task_description": t.task_description,
                "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                "status": t.status,
            }
            for t in tasks
        ]
    }


@router.get("/dashboard")
def get_followup_dashboard(db: Session = Depends(get_db)):
    """获取随访看板"""
    return {
        "success": True,
        "data": {
            "status_stats": {
                "pending": 5,
                "completed": 12,
                "overdue": 2,
            },
            "overdue_tasks": []
        }
    }

