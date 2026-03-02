"""
DICOM影像处理服务
"""
import pydicom
import numpy as np
from PIL import Image
import io
from pathlib import Path
from typing import Optional, Dict, List
from minio import Minio
from app.config import settings
from loguru import logger


class DicomService:
    """DICOM处理服务"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """确保存储桶存在"""
        for bucket in [settings.MINIO_BUCKET_DICOM, settings.MINIO_BUCKET_REPORTS]:
            if not self.minio_client.bucket_exists(bucket):
                self.minio_client.make_bucket(bucket)
                logger.info(f"创建MinIO存储桶: {bucket}")
    
    async def parse_dicom_metadata(self, file_content: bytes) -> Dict:
        """
        解析DICOM文件元数据
        :param file_content: DICOM文件二进制内容
        :return: 元数据字典
        """
        try:
            # 使用pydicom读取DICOM
            ds = pydicom.dcmread(io.BytesIO(file_content))
            
            metadata = {
                "patient_name": str(ds.get("PatientName", "Unknown")),
                "patient_id": str(ds.get("PatientID", "")),
                "study_uid": str(ds.get("StudyInstanceUID", "")),
                "series_uid": str(ds.get("SeriesInstanceUID", "")),
                "modality": str(ds.get("Modality", "")),
                "series_description": str(ds.get("SeriesDescription", "")),
                "series_number": int(ds.get("SeriesNumber", 0)),
                "study_date": str(ds.get("StudyDate", "")),
                "acquisition_date": str(ds.get("AcquisitionDate", "")),
                
                # 影像参数
                "rows": int(ds.get("Rows", 0)),
                "columns": int(ds.get("Columns", 0)),
                "slice_thickness": float(ds.get("SliceThickness", 0)),
                "pixel_spacing": str(ds.get("PixelSpacing", "")),
                "window_center": str(ds.get("WindowCenter", "")),
                "window_width": str(ds.get("WindowWidth", "")),
                
                # 设备信息
                "manufacturer": str(ds.get("Manufacturer", "")),
                "institution_name": str(ds.get("InstitutionName", "")),
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"DICOM元数据解析失败: {e}")
            raise ValueError(f"无效的DICOM文件: {e}")
    
    async def generate_thumbnail(
        self,
        file_content: bytes,
        size: tuple = (256, 256)
    ) -> bytes:
        """
        生成DICOM影像缩略图
        :param file_content: DICOM文件内容
        :param size: 缩略图尺寸
        :return: PNG格式缩略图二进制数据
        """
        try:
            ds = pydicom.dcmread(io.BytesIO(file_content))
            
            # 获取像素数据
            pixel_array = ds.pixel_array
            
            # 归一化到0-255
            pixel_array = pixel_array.astype(float)
            pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min())
            pixel_array = (pixel_array * 255).astype(np.uint8)
            
            # 创建PIL图像
            image = Image.fromarray(pixel_array)
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 转换为PNG
            output = io.BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"缩略图生成失败: {e}")
            raise
    
    async def upload_dicom_to_storage(
        self,
        file_content: bytes,
        patient_id: int,
        series_uid: str,
        filename: str
    ) -> str:
        """
        上传DICOM文件到MinIO
        :return: 存储路径
        """
        try:
            # 构建存储路径: patients/{patient_id}/series/{series_uid}/{filename}
            object_name = f"patients/{patient_id}/series/{series_uid}/{filename}"
            
            # 上传到MinIO
            self.minio_client.put_object(
                settings.MINIO_BUCKET_DICOM,
                object_name,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type="application/dicom"
            )
            
            logger.info(f"DICOM文件上传成功: {object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"DICOM文件上传失败: {e}")
            raise
    
    async def upload_thumbnail(
        self,
        thumbnail_data: bytes,
        patient_id: int,
        series_uid: str
    ) -> str:
        """上传缩略图"""
        try:
            object_name = f"patients/{patient_id}/thumbnails/{series_uid}.png"
            
            self.minio_client.put_object(
                settings.MINIO_BUCKET_DICOM,
                object_name,
                data=io.BytesIO(thumbnail_data),
                length=len(thumbnail_data),
                content_type="image/png"
            )
            
            return object_name
            
        except Exception as e:
            logger.error(f"缩略图上传失败: {e}")
            raise
    
    async def get_dicom_file(self, object_name: str) -> bytes:
        """从MinIO获取DICOM文件"""
        try:
            response = self.minio_client.get_object(
                settings.MINIO_BUCKET_DICOM,
                object_name
            )
            return response.read()
        except Exception as e:
            logger.error(f"DICOM文件获取失败: {e}")
            raise
    
    async def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600
    ) -> str:
        """
        生成预签名URL（用于前端直接下载）
        :param object_name: 对象名称
        :param expires: 有效期(秒)
        """
        try:
            url = self.minio_client.presigned_get_object(
                settings.MINIO_BUCKET_DICOM,
                object_name,
                expires=expires
            )
            return url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {e}")
            raise
    
    async def batch_process_dicom_series(
        self,
        files: List[bytes],
        patient_id: int
    ) -> Dict:
        """
        批量处理DICOM序列
        :param files: DICOM文件列表
        :param patient_id: 患者ID
        :return: 处理结果
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "series_uid": None,
            "metadata": None,
            "thumbnail_path": None,
        }
        
        try:
            # 解析第一个文件获取序列信息
            first_metadata = await self.parse_dicom_metadata(files[0])
            series_uid = first_metadata["series_uid"]
            results["series_uid"] = series_uid
            results["metadata"] = first_metadata
            
            # 生成缩略图（使用中间切片）
            middle_index = len(files) // 2
            thumbnail = await self.generate_thumbnail(files[middle_index])
            thumbnail_path = await self.upload_thumbnail(thumbnail, patient_id, series_uid)
            results["thumbnail_path"] = thumbnail_path
            
            # 上传所有DICOM文件
            for idx, file_content in enumerate(files):
                try:
                    filename = f"slice_{idx:04d}.dcm"
                    await self.upload_dicom_to_storage(
                        file_content,
                        patient_id,
                        series_uid,
                        filename
                    )
                    results["success_count"] += 1
                except Exception as e:
                    logger.error(f"文件上传失败 (索引 {idx}): {e}")
                    results["failed_count"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"批量处理DICOM序列失败: {e}")
            raise


# 全局实例
dicom_service = DicomService()

