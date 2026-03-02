"""
标注管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.image import Annotation

router = APIRouter()


# ==================== Pydantic模型 ====================

class AnnotationCreate(BaseModel):
    """创建标注请求"""
    series_id: int
    patient_id: int
    annotation_type: str  # manual/ai/reviewed
    annotation_data: dict
    slice_index: Optional[int] = None
    annotator_id: Optional[int] = None
    annotator_name: Optional[str] = None


# ==================== API端点 ====================

@router.post("/", response_model=dict)
async def create_annotation(
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建标注 (F-DM-04)
    支持手动标注和AI辅助标注
    """
    try:
        annotation = Annotation(
            series_id=data.series_id,
            patient_id=data.patient_id,
            annotation_type=data.annotation_type,
            annotation_data=data.annotation_data,
            slice_index=data.slice_index,
            annotator_id=data.annotator_id,
            annotator_name=data.annotator_name,
        )
        
        db.add(annotation)
        await db.commit()
        await db.refresh(annotation)
        
        return {
            "success": True,
            "message": "标注创建成功",
            "data": {"annotation_id": annotation.id}
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建标注失败: {str(e)}")


@router.get("/series/{series_id}", response_model=dict)
async def get_series_annotations(
    series_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取影像序列的所有标注"""
    try:
        result = await db.execute(
            select(Annotation).where(Annotation.series_id == series_id)
        )
        annotations = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": a.id,
                    "annotation_type": a.annotation_type,
                    "annotation_data": a.annotation_data,
                    "slice_index": a.slice_index,
                    "annotator_name": a.annotator_name,
                    "is_reviewed": a.is_reviewed,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in annotations
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询标注失败: {str(e)}")

