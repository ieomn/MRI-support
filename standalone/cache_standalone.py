"""
单机版缓存 - 使用diskcache替代Redis
"""
from diskcache import Cache
from typing import Any, Optional
import pickle
import json
from config_standalone import settings


class LocalCache:
    """本地文件缓存管理器"""
    
    def __init__(self):
        self.cache = Cache(
            str(settings.CACHE_DIR),
            size_limit=settings.CACHE_SIZE_LIMIT
        )
    
    def get(self, key: str, default=None) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key, default)
    
    def set(self, key: str, value: Any, ttl: int = 0):
        """设置缓存"""
        if ttl > 0:
            self.cache.set(key, value, expire=ttl)
        else:
            self.cache.set(key, value)
    
    def delete(self, *keys: str):
        """删除缓存"""
        for key in keys:
            self.cache.delete(key)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self.cache
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    # 业务专用方法
    def get_patient_info(self, patient_id: int) -> Optional[dict]:
        """获取患者信息缓存"""
        return self.get(f"patient:info:{patient_id}")
    
    def set_patient_info(self, patient_id: int, data: dict, ttl: int = 3600):
        """设置患者信息缓存"""
        self.set(f"patient:info:{patient_id}", data, ttl)
    
    def get_ai_result(self, case_id: int, result_type: str) -> Optional[Any]:
        """获取AI结果缓存"""
        return self.get(f"ai:{result_type}:{case_id}")
    
    def set_ai_result(self, case_id: int, result_type: str, result_data: Any):
        """设置AI结果缓存（永久）"""
        self.set(f"ai:{result_type}:{case_id}", result_data)
    
    def invalidate_patient_cache(self, patient_id: int):
        """清除患者相关缓存"""
        keys = [
            f"patient:info:{patient_id}",
            f"patient:detail:{patient_id}",
        ]
        self.delete(*keys)


# 全局缓存实例
cache = LocalCache()

