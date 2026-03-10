"""
NIfTI 文件处理服务
将 .nii/.nii.gz 3D 体积数据提取为 2D 切片供 MedGemma 分析
"""
import io
import base64
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import nibabel as nib
import numpy as np
from PIL import Image
from loguru import logger


class NIfTIService:
    """NIfTI 3D 医学影像处理"""

    SUPPORTED_EXTENSIONS = {".nii", ".nii.gz"}

    @staticmethod
    def is_nifti(filename: str) -> bool:
        name = filename.lower()
        return name.endswith(".nii") or name.endswith(".nii.gz")

    def load_volume(self, file_bytes: bytes, filename: str) -> Tuple[np.ndarray, dict]:
        """
        读取 NIfTI 文件字节为 3D numpy 数组 + 元数据。
        返回 (volume_3d, metadata_dict)
        """
        suffix = ".nii.gz" if filename.lower().endswith(".nii.gz") else ".nii"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            img = nib.load(tmp_path)
            volume = np.asanyarray(img.dataobj, dtype=np.float32)
            header = img.header

            pixdim = header.get_zooms()
            metadata = {
                "shape": list(volume.shape),
                "voxel_size": [float(d) for d in pixdim[:3]] if len(pixdim) >= 3 else [],
                "dtype": str(volume.dtype),
                "format": "NIfTI",
                "filename": filename,
            }

            logger.info(f"NIfTI 加载成功: {filename}, shape={volume.shape}, voxel={metadata['voxel_size']}")
            return volume, metadata
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def extract_center_slices(
        self,
        volume: np.ndarray,
        num_slices: int = 3,
    ) -> List[Tuple[np.ndarray, str]]:
        """
        提取多平面中心切片（轴位、冠状位、矢状位）。
        返回 [(slice_2d, plane_label), ...]
        """
        slices: List[Tuple[np.ndarray, str]] = []

        if volume.ndim == 4:
            volume = volume[..., 0]

        if volume.ndim != 3:
            raise ValueError(f"期望 3D 体积，实际维度 {volume.ndim}")

        d, h, w = volume.shape

        axial = volume[d // 2, :, :]
        slices.append((axial, "axial"))

        coronal = volume[:, h // 2, :]
        slices.append((coronal, "coronal"))

        sagittal = volume[:, :, w // 2]
        slices.append((sagittal, "sagittal"))

        if num_slices > 3:
            offsets = [d // 4, 3 * d // 4]
            for off in offsets[: num_slices - 3]:
                slices.append((volume[off, :, :], f"axial_{off}"))

        return slices

    def normalize_slice(self, arr: np.ndarray) -> np.ndarray:
        """窗宽窗位自适应归一化到 0-255 uint8"""
        arr = arr.astype(np.float64)
        p2, p98 = np.percentile(arr, (2, 98))
        if p98 - p2 < 1e-6:
            return np.zeros_like(arr, dtype=np.uint8)
        arr = np.clip((arr - p2) / (p98 - p2) * 255.0, 0, 255)
        return arr.astype(np.uint8)

    def slice_to_base64(self, arr: np.ndarray) -> str:
        """2D numpy 切片 -> Base64 PNG"""
        normalized = self.normalize_slice(arr)
        img = Image.fromarray(normalized, mode="L")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def process_nifti_for_medgemma(
        self,
        file_bytes: bytes,
        filename: str,
        num_slices: int = 3,
    ) -> dict:
        """
        完整流程：NIfTI 字节 -> 多平面切片 Base64 列表。
        返回 {"images_base64": [...], "planes": [...], "metadata": {...}}
        """
        volume, metadata = self.load_volume(file_bytes, filename)
        slices = self.extract_center_slices(volume, num_slices)

        images_b64 = []
        planes = []
        for arr, plane in slices:
            images_b64.append(self.slice_to_base64(arr))
            planes.append(plane)

        logger.info(f"NIfTI -> {len(images_b64)} 切片已提取: {planes}")

        return {
            "images_base64": images_b64,
            "planes": planes,
            "metadata": metadata,
        }


nifti_service = NIfTIService()
