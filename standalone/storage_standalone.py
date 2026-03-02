"""
单机版存储 - 使用本地文件系统替代MinIO
"""
import shutil
from pathlib import Path
from typing import BinaryIO
from config_standalone import settings


class LocalStorage:
    """本地文件存储管理器"""
    
    def __init__(self):
        self.dicom_dir = settings.DICOM_DIR
        self.reports_dir = settings.REPORTS_DIR
        self.thumbnails_dir = settings.THUMBNAILS_DIR
    
    def save_dicom(self, patient_id: int, series_uid: str, filename: str, content: bytes) -> str:
        """保存DICOM文件"""
        # 构建存储路径
        path = self.dicom_dir / str(patient_id) / series_uid
        path.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = path / filename
        file_path.write_bytes(content)
        
        return str(file_path.relative_to(self.dicom_dir))
    
    def get_dicom(self, relative_path: str) -> bytes:
        """获取DICOM文件"""
        file_path = self.dicom_dir / relative_path
        return file_path.read_bytes()
    
    def save_thumbnail(self, patient_id: int, series_uid: str, content: bytes) -> str:
        """保存缩略图"""
        path = self.thumbnails_dir / str(patient_id)
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / f"{series_uid}.png"
        file_path.write_bytes(content)
        
        return str(file_path.relative_to(self.thumbnails_dir))
    
    def get_thumbnail(self, relative_path: str) -> bytes:
        """获取缩略图"""
        file_path = self.thumbnails_dir / relative_path
        return file_path.read_bytes()
    
    def save_report(self, patient_id: int, filename: str, content: bytes) -> str:
        """保存患者报告"""
        path = self.reports_dir / str(patient_id)
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / filename
        file_path.write_bytes(content)
        
        return str(file_path.relative_to(self.reports_dir))
    
    def delete_patient_files(self, patient_id: int):
        """删除患者的所有文件"""
        for base_dir in [self.dicom_dir, self.reports_dir, self.thumbnails_dir]:
            patient_dir = base_dir / str(patient_id)
            if patient_dir.exists():
                shutil.rmtree(patient_dir)
    
    def get_storage_stats(self) -> dict:
        """获取存储统计信息"""
        def get_dir_size(path: Path) -> int:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        return {
            "dicom_size_mb": get_dir_size(self.dicom_dir) / 1024 / 1024,
            "reports_size_mb": get_dir_size(self.reports_dir) / 1024 / 1024,
            "total_size_mb": get_dir_size(settings.STORAGE_DIR) / 1024 / 1024,
        }


# 全局存储实例
storage = LocalStorage()

