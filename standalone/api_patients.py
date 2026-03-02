"""
患者管理API - 单机版
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database_standalone import get_db
from models_standalone import Patient
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

router = APIRouter()


# ==================== Pydantic模型 ====================

class PatientCreate(BaseModel):
    name: str
    gender: str
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    admission_date: Optional[date] = None
    hospital: Optional[str] = None
    diagnosis: Optional[str] = None
    stage: Optional[str] = None


# ==================== API端点 ====================

@router.get("/")
def list_patients(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取患者列表"""
    query = db.query(Patient).filter(Patient.is_deleted == 0)
    
    if keyword:
        query = query.filter(
            (Patient.name.contains(keyword)) | 
            (Patient.patient_no.contains(keyword))
        )
    
    total = query.count()
    patients = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": p.id,
                    "patient_no": p.patient_no,
                    "name": p.name,
                    "gender": p.gender,
                    "phone": p.phone,
                    "hospital": p.hospital,
                    "diagnosis": p.diagnosis,
                    "stage": p.stage,
                    "admission_date": p.admission_date.isoformat() if p.admission_date else None,
                }
                for p in patients
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    }


@router.post("/")
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    """创建患者"""
    # 生成患者编号
    count = db.query(Patient).count()
    patient_no = f"EC{datetime.now().strftime('%Y%m%d')}{count + 1:04d}"
    
    patient = Patient(
        patient_no=patient_no,
        name=data.name,
        gender=data.gender,
        birth_date=data.birth_date,
        phone=data.phone,
        address=data.address,
        admission_date=data.admission_date,
        hospital=data.hospital,
        diagnosis=data.diagnosis,
        stage=data.stage,
    )
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    return {
        "success": True,
        "message": "患者创建成功",
        "data": {
            "id": patient.id,
            "patient_no": patient.patient_no,
        }
    }


@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """获取患者详情"""
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.is_deleted == 0
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    return {
        "success": True,
        "data": {
            "id": patient.id,
            "patient_no": patient.patient_no,
            "name": patient.name,
            "gender": patient.gender,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
            "phone": patient.phone,
            "address": patient.address,
            "admission_date": patient.admission_date.isoformat() if patient.admission_date else None,
            "hospital": patient.hospital,
            "diagnosis": patient.diagnosis,
            "stage": patient.stage,
        }
    }


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """删除患者"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    patient.is_deleted = 1
    db.commit()
    
    return {"success": True, "message": "删除成功"}

