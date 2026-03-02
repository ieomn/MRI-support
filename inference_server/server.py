"""
MedGemma 推理服务器
部署到 AutoDL 等云 GPU 平台，加载 MedGemma 27B 并暴露 HTTP API
硬件要求：A100 GPU (40GB+ VRAM)，建议使用 4-bit 量化以降低显存需求
"""
import io
import time
import base64
from contextlib import asynccontextmanager
from typing import Optional

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel, Field
from loguru import logger

MODEL_ID = "google/medgemma-27b-it"
USE_QUANTIZATION = True

model = None
processor = None


def load_medgemma():
    """加载 MedGemma 模型和处理器"""
    global model, processor
    from transformers import AutoModelForImageTextToText, AutoProcessor

    logger.info(f"正在加载模型: {MODEL_ID} (量化={USE_QUANTIZATION})")

    model_kwargs = dict(
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    if USE_QUANTIZATION:
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)

    model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, **model_kwargs)
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    logger.info("MedGemma 模型加载完成")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_medgemma()
    yield
    logger.info("推理服务关闭")


app = FastAPI(title="MedGemma Inference Server", version="1.0.0", lifespan=lifespan)


# ==================== 请求/响应模型 ====================

class AnalyzeImageRequest(BaseModel):
    """影像分析请求"""
    image_base64: str = Field(..., description="Base64 编码的医学影像")
    prompt: str = Field(
        default="请分析这张医学影像，描述你观察到的所有发现。",
        description="分析指令",
    )
    system_prompt: str = Field(
        default="你是一位经验丰富的放射科医师，擅长 MRI 影像分析，特别是妇科肿瘤影像诊断。请用中文回答。",
        description="系统角色指令",
    )
    max_new_tokens: int = Field(default=2048, ge=64, le=4096)


class AnalyzeTextRequest(BaseModel):
    """纯文本医学问答请求"""
    prompt: str = Field(..., description="医学问题或患者临床数据")
    system_prompt: str = Field(
        default="你是一位经验丰富的妇科肿瘤专科医师，擅长子宫内膜癌的诊断和预后评估。请用中文回答。",
        description="系统角色指令",
    )
    max_new_tokens: int = Field(default=2048, ge=64, le=4096)


class MultiImageAnalyzeRequest(BaseModel):
    """多图影像分析请求（用于多切片 MRI）"""
    images_base64: list[str] = Field(..., description="Base64 编码的多张影像", min_length=1, max_length=20)
    prompt: str = Field(
        default="请综合分析这组 MRI 序列影像，描述病灶位置、大小、信号特征及诊断建议。",
        description="分析指令",
    )
    system_prompt: str = Field(
        default="你是一位经验丰富的放射科医师，擅长 MRI 影像分析，特别是妇科肿瘤影像诊断。请用中文回答。",
        description="系统角色指令",
    )
    max_new_tokens: int = Field(default=3072, ge=64, le=4096)


class AnalysisResponse(BaseModel):
    """分析响应"""
    success: bool
    content: str = ""
    inference_time: float = 0.0
    model_id: str = MODEL_ID
    error: Optional[str] = None


# ==================== 工具函数 ====================

def decode_base64_image(b64_string: str) -> Image.Image:
    """解码 Base64 图片"""
    image_bytes = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


@torch.inference_mode()
def run_inference(messages: list[dict], max_new_tokens: int) -> str:
    """执行模型推理"""
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device, dtype=torch.bfloat16)

    generation = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)

    decoded = processor.decode(generation[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    return decoded.strip()


# ==================== API 端点 ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_id": MODEL_ID,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.1f} GB" if torch.cuda.is_available() else "N/A",
    }


@app.post("/v1/analyze/image", response_model=AnalysisResponse)
async def analyze_image(req: AnalyzeImageRequest):
    """单张影像分析"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        image = decode_base64_image(req.image_base64)

        messages = [
            {"role": "system", "content": [{"type": "text", "text": req.system_prompt}]},
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": req.prompt},
                ],
            },
        ]

        start = time.time()
        content = run_inference(messages, req.max_new_tokens)
        elapsed = time.time() - start

        return AnalysisResponse(success=True, content=content, inference_time=elapsed)

    except Exception as e:
        logger.error(f"影像分析失败: {e}")
        return AnalysisResponse(success=False, error=str(e))


@app.post("/v1/analyze/text", response_model=AnalysisResponse)
async def analyze_text(req: AnalyzeTextRequest):
    """纯文本医学问答"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        messages = [
            {"role": "system", "content": [{"type": "text", "text": req.system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": req.prompt}]},
        ]

        start = time.time()
        content = run_inference(messages, req.max_new_tokens)
        elapsed = time.time() - start

        return AnalysisResponse(success=True, content=content, inference_time=elapsed)

    except Exception as e:
        logger.error(f"文本分析失败: {e}")
        return AnalysisResponse(success=False, error=str(e))


@app.post("/v1/analyze/multi-image", response_model=AnalysisResponse)
async def analyze_multi_image(req: MultiImageAnalyzeRequest):
    """多切片 MRI 序列分析"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        images = [decode_base64_image(b64) for b64 in req.images_base64]

        user_content: list[dict] = []
        for i, img in enumerate(images):
            user_content.append({"type": "image", "image": img})
        user_content.append({"type": "text", "text": req.prompt})

        messages = [
            {"role": "system", "content": [{"type": "text", "text": req.system_prompt}]},
            {"role": "user", "content": user_content},
        ]

        start = time.time()
        content = run_inference(messages, req.max_new_tokens)
        elapsed = time.time() - start

        return AnalysisResponse(success=True, content=content, inference_time=elapsed)

    except Exception as e:
        logger.error(f"多图分析失败: {e}")
        return AnalysisResponse(success=False, error=str(e))


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8080, workers=1)
