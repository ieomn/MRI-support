"""
MedGemma 远程推理客户端
通过 HTTP 调用部署在 AutoDL 云 GPU 上的 MedGemma 推理服务器
"""
import base64
import io
from typing import Optional

import httpx
import numpy as np
from loguru import logger
from PIL import Image

from app.config import settings


class MedGemmaService:
    """MedGemma 推理服务客户端"""

    def __init__(self):
        self.base_url = settings.MEDGEMMA_API_URL
        self.timeout = settings.MEDGEMMA_API_TIMEOUT
        self.max_retries = settings.MEDGEMMA_MAX_RETRIES
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10.0),
        )
        logger.info(f"MedGemma 客户端已连接: {self.base_url}")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("MedGemma 客户端已断开")

    async def _ensure_client(self):
        if self._client is None:
            await self.connect()

    # ==================== 健康检查 ====================

    async def health_check(self) -> dict:
        """检查推理服务器状态"""
        await self._ensure_client()
        try:
            resp = await self._client.get("/health")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"MedGemma 健康检查失败: {e}")
            return {"status": "unreachable", "error": str(e)}

    # ==================== 图像编码工具 ====================

    @staticmethod
    def numpy_to_base64(image_array: np.ndarray) -> str:
        """numpy 数组 -> Base64 PNG"""
        if image_array.dtype != np.uint8:
            arr = image_array.astype(np.float64)
            arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255
            image_array = arr.astype(np.uint8)

        if len(image_array.shape) == 2:
            pil_img = Image.fromarray(image_array, mode="L").convert("RGB")
        else:
            pil_img = Image.fromarray(image_array)

        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def pil_to_base64(image: Image.Image) -> str:
        """PIL Image -> Base64 PNG"""
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def bytes_to_base64(image_bytes: bytes) -> str:
        """原始图片字节 -> Base64"""
        return base64.b64encode(image_bytes).decode("utf-8")

    # ==================== 核心分析接口 ====================

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str = "请分析这张医学影像，描述你观察到的所有发现，包括病灶位置、大小、信号特征、以及初步诊断建议。",
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 2048,
    ) -> dict:
        """
        单张影像分析
        返回: {"success": bool, "content": str, "inference_time": float, ...}
        """
        await self._ensure_client()

        payload = {
            "image_base64": image_base64,
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt

        return await self._post_with_retry("/v1/analyze/image", payload)

    async def analyze_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 2048,
    ) -> dict:
        """
        纯文本医学问答 / 基于临床数据的预后分析
        """
        await self._ensure_client()

        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt

        return await self._post_with_retry("/v1/analyze/text", payload)

    async def analyze_multi_image(
        self,
        images_base64: list[str],
        prompt: str = "请综合分析这组 MRI 序列影像，描述病灶位置、大小、信号特征及诊断建议。",
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 3072,
    ) -> dict:
        """
        多切片 MRI 序列分析
        """
        await self._ensure_client()

        payload = {
            "images_base64": images_base64,
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt

        return await self._post_with_retry("/v1/analyze/multi-image", payload)

    # ==================== 高级业务接口 ====================

    async def analyze_mri_for_endometrial_cancer(
        self,
        image_base64: str,
        clinical_context: Optional[str] = None,
    ) -> dict:
        """
        子宫内膜癌 MRI 专项分析
        结合临床信息给出结构化分析报告
        """
        prompt_parts = [
            "请对这张子宫 MRI 影像进行详细分析，按以下结构输出：",
            "1. 【影像描述】描述子宫形态、大小、信号特征",
            "2. 【病灶发现】病灶位置、大小（估计值）、信号特点、边界情况",
            "3. 【肌层浸润评估】评估肌层浸润深度（<50% 或 ≥50%）",
            "4. 【淋巴结评估】盆腔及腹主动脉旁淋巴结情况",
            "5. 【分期建议】基于影像特征的 FIGO 分期建议",
            "6. 【鉴别诊断】需要鉴别的其他疾病",
            "7. 【建议】进一步检查或随访建议",
        ]

        if clinical_context:
            prompt_parts.insert(0, f"临床信息：{clinical_context}")
            prompt_parts.insert(1, "")

        prompt = "\n".join(prompt_parts)

        return await self.analyze_image(
            image_base64=image_base64,
            prompt=prompt,
            system_prompt=(
                "你是一位经验丰富的妇科肿瘤放射诊断专家，"
                "擅长子宫内膜癌的 MRI 影像诊断。"
                "请基于影像特征给出专业、结构化的分析报告。用中文回答。"
            ),
            max_new_tokens=3072,
        )

    async def predict_prognosis_with_llm(
        self,
        clinical_data: dict,
    ) -> dict:
        """
        基于临床数据的 LLM 预后评估（替代/补充传统回归模型）
        """
        data_lines = []
        field_labels = {
            "age": "年龄",
            "bmi": "BMI",
            "stage": "FIGO分期",
            "grade": "病理分级",
            "tumor_size": "肿瘤大小(cm)",
            "lymph_node_positive": "阳性淋巴结数",
            "histology": "组织学类型",
            "myometrial_invasion": "肌层浸润深度",
            "lvsi": "淋巴血管间隙浸润",
            "molecular_subtype": "分子分型",
        }
        for key, label in field_labels.items():
            val = clinical_data.get(key)
            if val is not None:
                data_lines.append(f"- {label}: {val}")

        radiomics = clinical_data.get("radiomics_features", {})
        if radiomics:
            data_lines.append("- 影像组学特征:")
            for k, v in radiomics.items():
                data_lines.append(f"  - {k}: {v}")

        prompt = (
            "基于以下子宫内膜癌患者的临床和病理数据，请给出：\n"
            "1. 【风险评估】综合风险等级（低/中/高）及依据\n"
            "2. 【复发风险】2年和5年复发概率估计\n"
            "3. 【生存预测】1年、3年、5年总生存率估计\n"
            "4. 【关键风险因素】影响预后的主要因素分析\n"
            "5. 【治疗建议】基于风险分层的治疗方案建议\n"
            "\n患者数据：\n" + "\n".join(data_lines)
        )

        return await self.analyze_text(
            prompt=prompt,
            system_prompt=(
                "你是一位资深的妇科肿瘤专科医师，"
                "擅长子宫内膜癌的预后评估和治疗决策。"
                "请基于循证医学证据给出专业评估。"
                "对于数值估计，请给出合理范围而非精确数字。用中文回答。"
            ),
            max_new_tokens=2048,
        )

    # ==================== 内部方法 ====================

    async def _post_with_retry(self, endpoint: str, payload: dict) -> dict:
        """带重试的 POST 请求"""
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = await self._client.post(endpoint, json=payload)
                resp.raise_for_status()
                return resp.json()
            except httpx.TimeoutException:
                last_error = "推理超时，MedGemma 可能正在处理复杂内容"
                logger.warning(f"MedGemma 请求超时 (尝试 {attempt}/{self.max_retries})")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                logger.error(f"MedGemma HTTP 错误: {last_error}")
                if e.response.status_code < 500:
                    break
            except Exception as e:
                last_error = str(e)
                logger.error(f"MedGemma 请求异常: {e}")

        return {"success": False, "content": "", "error": last_error}


# 全局服务实例
medgemma_service = MedGemmaService()
