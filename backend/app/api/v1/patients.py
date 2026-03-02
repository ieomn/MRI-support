"""
患者管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.cache import get_cache, CacheManager
from app.models.patient import Patient, GenderEnum
from pydantic import BaseModel

router = APIRouter()


# ==================== Pydantic模型 ====================

class PatientCreate(BaseModel):
    """创建患者请求模型"""
    name: str
    gender: GenderEnum
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    admission_date: Optional[date] = None
    hospital: Optional[str] = None
    diagnosis: Optional[str] = None
    stage: Optional[str] = None


class PatientUpdate(BaseModel):
    """更新患者请求模型"""
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    diagnosis: Optional[str] = None
    stage: Optional[str] = None
    treatment_plan: Optional[str] = None


class PatientResponse(BaseModel):
    """患者响应模型"""
    id: int
    patient_no: str
    name: str
    gender: str
    age: Optional[int] = None
    phone: Optional[str] = None
    hospital: Optional[str] = None
    diagnosis: Optional[str] = None
    stage: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== API端点 ====================

@router.post("/", response_model=dict)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """
    创建新患者病例 (F-DM-01)
    """
    try:
        # 生成患者编号
        result = await db.execute(select(func.count(Patient.id)))
        count = result.scalar()
        patient_no = f"EC{date.today().strftime('%Y%m%d')}{count + 1:04d}"
        
        # 创建患者记录
        patient = Patient(
            patient_no=patient_no,
            name=patient_data.name,
            gender=patient_data.gender,
            birth_date=patient_data.birth_date,
            phone=patient_data.phone,
            address=patient_data.address,
            admission_date=patient_data.admission_date,
            hospital=patient_data.hospital,
            diagnosis=patient_data.diagnosis,
            stage=patient_data.stage,
        )
        
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        
        # 写入缓存
        await cache.set_patient_info(patient.id, patient.to_dict())
        
        return {
            "success": True,
            "message": "患者创建成功",
            "data": patient.to_dict()
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建患者失败: {str(e)}")


@router.get("/", response_model=dict)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """
    获取患者列表 (F-CD-01)
    支持分页和搜索
    """
    try:
        # 尝试从缓存获取
        cache_key = f"patient_list_{page}_{page_size}_{keyword or ''}"
        cached = await cache.get_cached_list("patient", page, page_size)
        if cached and not keyword:
            return cached
        
        # 构建查询
        query = select(Patient).where(Patient.is_deleted == 0)
        
        if keyword:
            query = query.where(
                (Patient.name.contains(keyword)) |
                (Patient.patient_no.contains(keyword))
            )
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 分页查询
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        patients = result.scalars().all()
        
        response_data = {
            "success": True,
            "data": {
                "items": [p.to_dict() for p in patients],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
        # 写入缓存（仅无搜索条件时）
        if not keyword:
            await cache.set_cached_list("patient", page, page_size, response_data)
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询患者列表失败: {str(e)}")


@router.get("/{patient_id}", response_model=dict)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """
    获取患者详情 (F-CD-02)
    """
    try:
        # 尝试从缓存获取
        cached = await cache.get_patient_info(patient_id)
        if cached:
            return {"success": True, "data": cached}
        
        # 从数据库查询
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id, Patient.is_deleted == 0)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
        
        patient_dict = patient.to_dict()
        
        # 写入缓存
        await cache.set_patient_info(patient_id, patient_dict)
        
        return {"success": True, "data": patient_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询患者详情失败: {str(e)}")


@router.put("/{patient_id}", response_model=dict)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """更新患者信息"""
    try:
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id, Patient.is_deleted == 0)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
        
        # 更新字段
        update_data = patient_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)
        
        await db.commit()
        await db.refresh(patient)
        
        # 清除缓存
        await cache.invalidate_patient_cache(patient_id)
        
        return {
            "success": True,
            "message": "患者信息更新成功",
            "data": patient.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新患者信息失败: {str(e)}")


@router.delete("/{patient_id}", response_model=dict)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """删除患者（软删除）"""
    try:
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id, Patient.is_deleted == 0)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
        
        # 软删除
        patient.is_deleted = 1
        await db.commit()
        
        # 清除缓存
        await cache.invalidate_patient_cache(patient_id)
        
        return {"success": True, "message": "患者删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除患者失败: {str(e)}")

