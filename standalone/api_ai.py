"""
AI分析API - 单机版
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database_standalone import get_db
from models_standalone import AIAnalysisResult
from pydantic import BaseModel
import random

router = APIRouter()


class SegmentationRequest(BaseModel):
    series_id: int
    threshold: float = 0.5


class PrognosisRequest(BaseModel):
    patient_id: int
    clinical_data: dict


@router.post("/segment")
def run_segmentation(data: SegmentationRequest, db: Session = Depends(get_db)):
    """运行AI分割（演示版）"""
    # 生成模拟结果
    result = AIAnalysisResult(
        patient_id=1,  # 演示用
        series_id=data.series_id,
        analysis_type="segmentation",
        tumor_volume=round(random.uniform(2.5, 15.0), 2),
        model_name="U-Net",
    )
    
    db.add(result)
    db.commit()
    
    return {
        "success": True,
        "message": "AI分割完成",
        "data": {
            "tumor_volume": result.tumor_volume,
            "confidence": 0.85,
        }
    }


@router.post("/predict-prognosis")
def predict_prognosis(data: PrognosisRequest, db: Session = Depends(get_db)):
    """预后预测（演示版）"""
    risk_score = random.uniform(0.3, 0.8)
    
    result = AIAnalysisResult(
        patient_id=data.patient_id,
        analysis_type="prediction",
        prognosis_score=risk_score,
        risk_level="medium" if 0.3 < risk_score < 0.7 else "high",
        model_name="LinearRegression",
    )
    
    db.add(result)
    db.commit()
    
    return {
        "success": True,
        "message": "预测完成",
        "data": {
            "prognosis_score": round(risk_score, 3),
            "risk_level": result.risk_level,
            "risk_level_zh": "中风险" if result.risk_level == "medium" else "高风险",
        }
    }


@router.get("/results/patient/{patient_id}")
def get_patient_ai_results(patient_id: int, db: Session = Depends(get_db)):
    """获取患者AI结果"""
    results = db.query(AIAnalysisResult).filter(
        AIAnalysisResult.patient_id == patient_id
    ).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "analysis_type": r.analysis_type,
                "tumor_volume": r.tumor_volume,
                "prognosis_score": r.prognosis_score,
                "risk_level": r.risk_level,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]
    }

