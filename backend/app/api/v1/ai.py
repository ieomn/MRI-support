"""
AI分析API
包含 U-Net 分割（保留）和 MedGemma 影像分析（新增）
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
import re
import numpy as np

from app.core.database import get_db
from app.core.cache import get_cache, CacheManager
from app.models.image import MRISeries, AIAnalysisResult
from app.ml.unet_model import unet_service
from app.ml.regression_model import regression_service
from app.ml.medgemma_service import medgemma_service

router = APIRouter()


# ==================== Pydantic模型 ====================

class SegmentationRequest(BaseModel):
    """U-Net 分割请求"""
    series_id: int
    threshold: float = 0.5


class PrognosisRequest(BaseModel):
    """传统回归预后预测请求"""
    patient_id: int
    clinical_data: dict


class MedGemmaImageRequest(BaseModel):
    """MedGemma 影像分析请求"""
    series_id: int
    patient_id: int
    clinical_context: Optional[str] = Field(None, description="临床上下文信息（可选）")
    prompt: Optional[str] = Field(None, description="自定义分析指令（可选）")


class MedGemmaPrognosisRequest(BaseModel):
    """MedGemma 预后分析请求"""
    patient_id: int
    clinical_data: dict


class MedGemmaFreeformRequest(BaseModel):
    """MedGemma 自由问答请求"""
    question: str = Field(..., description="医学问题")
    patient_id: Optional[int] = Field(None, description="关联患者ID（可选）")
    image_base64: Optional[str] = Field(None, description="Base64 编码的影像（可选）")


# ==================== API端点 ====================

@router.post("/segment", response_model=dict)
async def run_segmentation(
    data: SegmentationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """
    运行U-Net分割 (F-AI-01, F-DM-04)
    一键智能标注功能
    """
    try:
        # 检查缓存
        cached_result = await cache.get_ai_result(data.series_id, "segmentation")
        if cached_result:
            return {
                "success": True,
                "message": "使用缓存结果",
                "data": cached_result
            }
        
        # 获取影像序列
        result = await db.execute(
            select(MRISeries).where(MRISeries.id == data.series_id)
        )
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(status_code=404, detail="影像序列不存在")
        
        # TODO: 从MinIO加载DICOM影像
        # 这里使用模拟数据演示
        # 实际应用中需要从MinIO读取DICOM文件并转换为numpy数组
        demo_image = np.random.rand(256, 256).astype(np.float32) * 255
        
        # 运行分割
        mask, confidence = unet_service.predict(demo_image, data.threshold)
        
        # 计算肿瘤体积（需要像素间距信息）
        pixel_spacing = (1.0, 1.0)  # 从DICOM元数据获取
        slice_thickness = 5.0
        volume = unet_service.calculate_tumor_volume(
            [mask],
            pixel_spacing,
            slice_thickness
        )
        
        result_data = {
            "series_id": data.series_id,
            "mask_shape": mask.shape,
            "confidence": float(confidence),
            "tumor_volume": float(volume),
            "positive_pixels": int(mask.sum()),
        }
        
        # 缓存结果
        await cache.set_ai_result(data.series_id, "segmentation", result_data)
        
        # 后台任务：保存到数据库
        background_tasks.add_task(
            save_ai_result_to_db,
            db,
            series.patient_id,
            data.series_id,
            "segmentation",
            result_data
        )
        
        return {
            "success": True,
            "message": "分割完成",
            "data": result_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分割失败: {str(e)}")


@router.post("/predict-prognosis", response_model=dict)
async def predict_prognosis(
    data: PrognosisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache)
):
    """
    预后风险预测 (F-AI-03)
    """
    try:
        # 检查缓存
        cached_result = await cache.get_ai_result(data.patient_id, "prediction")
        if cached_result:
            return {
                "success": True,
                "message": "使用缓存结果",
                "data": cached_result
            }
        
        # 运行预测
        prediction_result = regression_service.predict_prognosis(data.clinical_data)
        
        # 缓存结果
        await cache.set_ai_result(data.patient_id, "prediction", prediction_result)
        
        # 后台任务：保存到数据库
        background_tasks.add_task(
            save_prognosis_to_db,
            db,
            data.patient_id,
            prediction_result
        )
        
        return {
            "success": True,
            "message": "预测完成",
            "data": prediction_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.get("/results/patient/{patient_id}", response_model=dict)
async def get_patient_ai_results(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取患者的AI分析结果 (F-CD-03)
    """
    try:
        result = await db.execute(
            select(AIAnalysisResult).where(
                AIAnalysisResult.patient_id == patient_id
            )
        )
        results = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "analysis_type": r.analysis_type,
                    "tumor_volume": r.tumor_volume,
                    "prognosis_score": r.prognosis_score,
                    "risk_level": r.risk_level,
                    "recurrence_probability": r.recurrence_probability,
                    "survival_prediction": r.survival_prediction,
                    "report_text": r.report_text,
                    "findings": r.findings,
                    "diagnosis_suggestions": r.diagnosis_suggestions,
                    "model_name": r.model_name,
                    "model_version": r.model_version,
                    "inference_time": r.inference_time,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询AI结果失败: {str(e)}")


# ==================== MedGemma 端点 ====================

@router.get("/medgemma/health", response_model=dict)
async def medgemma_health():
    """
    检查 MedGemma 推理服务器状态
    """
    status = await medgemma_service.health_check()
    return {"success": True, "data": status}


@router.post("/medgemma/analyze-image", response_model=dict)
async def medgemma_analyze_image(
    data: MedGemmaImageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
):
    """
    MedGemma 影像分析 - 子宫内膜癌 MRI 专项报告
    从 MinIO 加载影像后发送到 MedGemma 进行分析
    """
    try:
        cached = await cache.get_ai_result(data.series_id, "medgemma_report")
        if cached:
            return {"success": True, "message": "使用缓存结果", "data": cached}

        result = await db.execute(
            select(MRISeries).where(MRISeries.id == data.series_id)
        )
        series = result.scalar_one_or_none()
        if not series:
            raise HTTPException(status_code=404, detail="影像序列不存在")

        # TODO: 从 MinIO 加载真实 DICOM 影像并转换
        # 当前使用模拟影像用于开发测试
        demo_image = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
        image_b64 = medgemma_service.numpy_to_base64(demo_image)

        analysis = await medgemma_service.analyze_mri_for_endometrial_cancer(
            image_base64=image_b64,
            clinical_context=data.clinical_context,
        )

        if not analysis.get("success"):
            raise HTTPException(
                status_code=502,
                detail=f"MedGemma 分析失败: {analysis.get('error', '未知错误')}",
            )

        result_data = {
            "series_id": data.series_id,
            "patient_id": data.patient_id,
            "report": analysis["content"],
            "inference_time": analysis.get("inference_time", 0),
            "model_id": analysis.get("model_id", ""),
        }

        await cache.set_ai_result(data.series_id, "medgemma_report", result_data)

        background_tasks.add_task(
            save_medgemma_report_to_db,
            db, data.patient_id, data.series_id,
            analysis["content"], data.clinical_context,
            analysis.get("inference_time", 0),
        )

        return {"success": True, "message": "MedGemma 分析完成", "data": result_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MedGemma 影像分析失败: {str(e)}")


@router.post("/medgemma/analyze-prognosis", response_model=dict)
async def medgemma_analyze_prognosis(
    data: MedGemmaPrognosisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
):
    """
    MedGemma 预后分析 - 基于临床数据的 LLM 预后评估
    """
    try:
        cached = await cache.get_ai_result(data.patient_id, "medgemma_prognosis")
        if cached:
            return {"success": True, "message": "使用缓存结果", "data": cached}

        analysis = await medgemma_service.predict_prognosis_with_llm(
            clinical_data=data.clinical_data,
        )

        if not analysis.get("success"):
            raise HTTPException(
                status_code=502,
                detail=f"MedGemma 预后分析失败: {analysis.get('error', '未知错误')}",
            )

        report_text = analysis["content"]
        parsed = _parse_prognosis_report(report_text)

        result_data = {
            "patient_id": data.patient_id,
            "report": report_text,
            "inference_time": analysis.get("inference_time", 0),
            "model_id": analysis.get("model_id", ""),
            **parsed,
        }

        await cache.set_ai_result(data.patient_id, "medgemma_prognosis", result_data)

        background_tasks.add_task(
            save_medgemma_prognosis_to_db,
            db, data.patient_id,
            report_text, data.clinical_data,
            analysis.get("inference_time", 0),
        )

        return {"success": True, "message": "MedGemma 预后分析完成", "data": result_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MedGemma 预后分析失败: {str(e)}")


@router.post("/medgemma/ask", response_model=dict)
async def medgemma_freeform(data: MedGemmaFreeformRequest):
    """
    MedGemma 自由医学问答
    支持纯文本问答或附带影像的问答
    """
    try:
        if data.image_base64:
            analysis = await medgemma_service.analyze_image(
                image_base64=data.image_base64,
                prompt=data.question,
            )
        else:
            analysis = await medgemma_service.analyze_text(prompt=data.question)

        if not analysis.get("success"):
            raise HTTPException(
                status_code=502,
                detail=f"MedGemma 问答失败: {analysis.get('error', '未知错误')}",
            )

        return {
            "success": True,
            "data": {
                "answer": analysis["content"],
                "inference_time": analysis.get("inference_time", 0),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MedGemma 问答失败: {str(e)}")


# ==================== LLM 输出结构化解析 ====================

def _parse_prognosis_report(text: str) -> dict:
    """
    Best-effort extraction of structured numbers from MedGemma prognosis text.
    Returns keys: risk_level, risk_score, survival, recurrence
    """
    result: dict = {}

    level_match = re.search(r"风险[等级]*[：:\s]*(低|中|高)", text)
    if level_match:
        mapping = {"低": "low", "中": "medium", "高": "high"}
        result["risk_level"] = mapping.get(level_match.group(1), "medium")
        result["risk_score"] = {"low": 0.2, "medium": 0.5, "high": 0.8}.get(result["risk_level"], 0.5)

    survival: dict = {}
    for label, key in [("1年", "1_year"), ("3年", "3_year"), ("5年", "5_year")]:
        m = re.search(rf"{label}[总生存率]*[：:\s]*(?:约)?(\d{{1,3}})[\s]*[%％]", text)
        if m:
            survival[key] = min(int(m.group(1)), 100) / 100.0
    if survival:
        result["survival"] = survival

    recurrence: dict = {}
    for label, key in [("2年", "2_year"), ("5年", "5_year")]:
        m = re.search(rf"(?:复发)[^。]*{label}[^。]*?(\d{{1,3}})[\s]*[%％]", text)
        if m:
            recurrence[key] = min(int(m.group(1)), 100) / 100.0
    if recurrence:
        result["recurrence"] = recurrence

    return result


# ==================== 后台任务函数 ====================

async def save_ai_result_to_db(
    db: AsyncSession,
    patient_id: int,
    series_id: int,
    analysis_type: str,
    result_data: dict
):
    """保存 U-Net AI 结果到数据库"""
    try:
        ai_result = AIAnalysisResult(
            patient_id=patient_id,
            series_id=series_id,
            analysis_type=analysis_type,
            tumor_volume=result_data.get("tumor_volume"),
            model_name="U-Net",
            model_version="1.0",
        )
        
        db.add(ai_result)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        print(f"保存AI结果失败: {e}")


async def save_prognosis_to_db(
    db: AsyncSession,
    patient_id: int,
    prediction_result: dict
):
    """保存传统回归预后预测结果到数据库"""
    try:
        ai_result = AIAnalysisResult(
            patient_id=patient_id,
            analysis_type="prediction",
            prognosis_score=prediction_result.get("prognosis_score"),
            risk_level=prediction_result.get("risk_level"),
            recurrence_probability=prediction_result.get("recurrence_probability", {}).get("2_year"),
            survival_prediction=prediction_result.get("survival_prediction"),
            model_name="LinearRegression",
            model_version="1.0",
        )
        
        db.add(ai_result)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        print(f"保存预后预测失败: {e}")


async def save_medgemma_report_to_db(
    db: AsyncSession,
    patient_id: int,
    series_id: int,
    report_text: str,
    clinical_context: Optional[str],
    inference_time: float,
):
    """保存 MedGemma 影像分析报告到数据库"""
    try:
        from app.config import settings
        ai_result = AIAnalysisResult(
            patient_id=patient_id,
            series_id=series_id,
            analysis_type="medgemma_report",
            report_text=report_text,
            clinical_context=clinical_context,
            model_name="MedGemma",
            model_version=settings.MEDGEMMA_MODEL_ID,
            inference_time=inference_time,
        )

        db.add(ai_result)
        await db.commit()

    except Exception as e:
        await db.rollback()
        print(f"保存 MedGemma 报告失败: {e}")


async def save_medgemma_prognosis_to_db(
    db: AsyncSession,
    patient_id: int,
    report_text: str,
    clinical_data: dict,
    inference_time: float,
):
    """保存 MedGemma 预后分析结果到数据库"""
    try:
        from app.config import settings
        ai_result = AIAnalysisResult(
            patient_id=patient_id,
            analysis_type="medgemma_prognosis",
            report_text=report_text,
            findings=clinical_data,
            model_name="MedGemma",
            model_version=settings.MEDGEMMA_MODEL_ID,
            inference_time=inference_time,
        )

        db.add(ai_result)
        await db.commit()

    except Exception as e:
        await db.rollback()
        print(f"保存 MedGemma 预后分析失败: {e}")

