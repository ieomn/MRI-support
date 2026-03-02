"""
影像管理API - 单机版
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database_standalone import get_db
from storage_standalone import storage
from models_standalone import MRISeries
from typing import List
import uuid

router = APIRouter()


@router.post("/upload/{patient_id}")
async def upload_images(
    patient_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """上传影像文件"""
    if not files:
        raise HTTPException(status_code=400, detail="未上传文件")
    
    # 生成序列UID
    series_uid = str(uuid.uuid4())
    
    # 保存文件
    success_count = 0
    for idx, file in enumerate(files):
        content = await file.read()
        filename = f"slice_{idx:04d}.dcm"
        storage.save_dicom(patient_id, series_uid, filename, content)
        success_count += 1
    
    # 保存到数据库
    series = MRISeries(
        patient_id=patient_id,
        series_uid=series_uid,
        series_description=f"MRI序列 {series_uid[:8]}",
        storage_path=f"{patient_id}/{series_uid}",
        file_count=success_count,
    )
    
    db.add(series)
    db.commit()
    
    return {
        "success": True,
        "message": f"上传成功 {success_count} 个文件",
        "data": {
            "series_id": series.id,
            "series_uid": series_uid,
        }
    }


@router.get("/patient/{patient_id}")
def get_patient_images(patient_id: int, db: Session = Depends(get_db)):
    """获取患者的影像列表"""
    series_list = db.query(MRISeries).filter(
        MRISeries.patient_id == patient_id
    ).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "series_uid": s.series_uid,
                "series_description": s.series_description,
                "file_count": s.file_count,
                "upload_time": s.upload_time.isoformat() if s.upload_time else None,
            }
            for s in series_list
        ]
    }

