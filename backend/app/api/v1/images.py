"""
影像管理API
支持 DICOM 和 NIfTI (.nii/.nii.gz) 格式
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.core.cache import get_cache, CacheManager
from app.models.image import MRISeries
from app.services.dicom_service import dicom_service
from app.services.nifti_service import nifti_service
from pydantic import BaseModel

router = APIRouter()


# ==================== Pydantic模型 ====================

class ImageSeriesResponse(BaseModel):
    """影像序列响应模型"""
    id: int
    series_uid: str
    modality: str
    series_description: str
    file_count: int
    thumbnail_path: Optional[str]
    upload_time: str
    
    class Config:
        from_attributes = True


# ==================== API端点 ====================

@router.post("/upload/{patient_id}", response_model=dict)
async def upload_image_series(
    patient_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """
    上传影像序列 (F-DM-03)
    支持 DICOM 和 NIfTI (.nii/.nii.gz) 格式
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="未上传文件")

        first_name = files[0].filename or ""
        is_nifti = nifti_service.is_nifti(first_name)

        if is_nifti:
            return await _handle_nifti_upload(patient_id, files, db, cache)
        else:
            return await _handle_dicom_upload(patient_id, files, db, cache)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


async def _handle_dicom_upload(
    patient_id: int,
    files: List[UploadFile],
    db: AsyncSession,
    cache: CacheManager,
) -> dict:
    """处理 DICOM 文件上传"""
    file_contents = []
    for file in files:
        content = await file.read()
        file_contents.append(content)

    result = await dicom_service.batch_process_dicom_series(
        file_contents, patient_id
    )

    series = MRISeries(
        patient_id=patient_id,
        series_uid=result["series_uid"],
        study_uid=result["metadata"]["study_uid"],
        modality=result["metadata"]["modality"],
        series_description=result["metadata"]["series_description"],
        series_number=result["metadata"]["series_number"],
        storage_path=f"patients/{patient_id}/series/{result['series_uid']}",
        file_count=result["success_count"],
        total_size=sum(len(f) for f in file_contents),
        thumbnail_path=result["thumbnail_path"],
        image_metadata=result["metadata"],
        slice_thickness=result["metadata"]["slice_thickness"],
        pixel_spacing=result["metadata"]["pixel_spacing"],
    )

    db.add(series)
    await db.commit()
    await db.refresh(series)

    await cache.set_dicom_metadata(result["series_uid"], result["metadata"])

    return {
        "success": True,
        "message": f"DICOM 上传成功 {result['success_count']} 个文件",
        "data": {
            "series_id": series.id,
            "series_uid": series.series_uid,
            "file_count": result["success_count"],
            "failed_count": result["failed_count"],
            "format": "DICOM",
        },
    }


async def _handle_nifti_upload(
    patient_id: int,
    files: List[UploadFile],
    db: AsyncSession,
    cache: CacheManager,
) -> dict:
    """处理 NIfTI (.nii/.nii.gz) 文件上传"""
    import uuid

    file = files[0]
    filename = file.filename or "unknown.nii"
    content = await file.read()

    nifti_result = await asyncio.to_thread(
        nifti_service.process_nifti_for_medgemma,
        content, filename, 3,
    )

    nii_meta = nifti_result["metadata"]
    series_uid = f"NII-{uuid.uuid4().hex[:12]}"
    voxel = nii_meta.get("voxel_size", [])

    series = MRISeries(
        patient_id=patient_id,
        series_uid=series_uid,
        study_uid=series_uid,
        modality="MR",
        series_description=f"NIfTI: {filename}",
        series_number=1,
        storage_path=f"patients/{patient_id}/nifti/{series_uid}",
        file_count=1,
        total_size=len(content),
        image_metadata={
            "format": "NIfTI",
            "filename": filename,
            "shape": nii_meta.get("shape"),
            "voxel_size": voxel,
            "extracted_planes": nifti_result["planes"],
            "slice_count": len(nifti_result["images_base64"]),
        },
        slice_thickness=voxel[2] if len(voxel) > 2 else None,
        pixel_spacing=voxel[:2] if len(voxel) >= 2 else None,
    )

    db.add(series)
    await db.commit()
    await db.refresh(series)

    nifti_cache = {
        "series_id": series.id,
        "images_base64": nifti_result["images_base64"],
        "planes": nifti_result["planes"],
    }
    await cache.set_dicom_metadata(series_uid, {
        **series.image_metadata,
        "nifti_slices": nifti_cache,
    })

    return {
        "success": True,
        "message": f"NIfTI 上传成功，已提取 {len(nifti_result['planes'])} 个切面",
        "data": {
            "series_id": series.id,
            "series_uid": series_uid,
            "file_count": 1,
            "format": "NIfTI",
            "shape": nii_meta.get("shape"),
            "planes": nifti_result["planes"],
            "slice_count": len(nifti_result["images_base64"]),
        },
    }


@router.get("/patient/{patient_id}", response_model=dict)
async def get_patient_images(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取患者的所有影像序列"""
    try:
        result = await db.execute(
            select(MRISeries).where(MRISeries.patient_id == patient_id)
        )
        series_list = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": s.id,
                    "series_uid": s.series_uid,
                    "modality": s.modality,
                    "series_description": s.series_description,
                    "file_count": s.file_count,
                    "thumbnail_path": s.thumbnail_path,
                    "upload_time": s.upload_time.isoformat() if s.upload_time else None,
                }
                for s in series_list
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/series/{series_id}/metadata", response_model=dict)
async def get_series_metadata(
    series_id: int,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """获取影像序列元数据"""
    try:
        result = await db.execute(
            select(MRISeries).where(MRISeries.id == series_id)
        )
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(status_code=404, detail="影像序列不存在")
        
        # 尝试从缓存获取
        cached_meta = await cache.get_dicom_metadata(series.series_uid)
        if cached_meta:
            return {"success": True, "data": cached_meta}
        
        # 返回数据库中的元数据
        metadata = series.image_metadata or {}
        await cache.set_dicom_metadata(series.series_uid, metadata)
        
        return {"success": True, "data": metadata}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询元数据失败: {str(e)}")


@router.get("/series/{series_id}/download-url", response_model=dict)
async def get_download_url(
    series_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取影像序列下载URL（预签名）"""
    try:
        result = await db.execute(
            select(MRISeries).where(MRISeries.id == series_id)
        )
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(status_code=404, detail="影像序列不存在")
        
        # 生成预签名URL（有效期1小时）
        url = await dicom_service.get_presigned_url(
            series.storage_path,
            expires=3600
        )
        
        return {
            "success": True,
            "data": {
                "url": url,
                "expires_in": 3600
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成下载链接失败: {str(e)}")

