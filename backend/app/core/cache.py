"""
Redis缓存管理模块
实现多级缓存策略
"""
import json
import pickle
from typing import Any, Optional, Union
from redis import asyncio as aioredis
from app.config import settings
from loguru import logger


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """连接Redis"""
        self.redis = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            password=settings.REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=False,  # 支持二进制数据
            max_connections=50,
        )
        logger.info("Redis缓存连接成功")
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis缓存连接关闭")
    
    # ==================== 通用缓存操作 ====================
    
    async def get(self, key: str, deserialize: str = "json") -> Optional[Any]:
        """
        获取缓存
        :param key: 缓存键
        :param deserialize: 反序列化方式 (json/pickle/none)
        """
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            if deserialize == "json":
                return json.loads(value)
            elif deserialize == "pickle":
                return pickle.loads(value)
            else:
                return value
        except Exception as e:
            logger.error(f"缓存读取失败 {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 0,
        serialize: str = "json"
    ) -> bool:
        """
        设置缓存
        :param key: 缓存键
        :param value: 缓存值
        :param ttl: 过期时间(秒), 0表示永不过期
        :param serialize: 序列化方式 (json/pickle/none)
        """
        try:
            if serialize == "json":
                value = json.dumps(value, ensure_ascii=False)
            elif serialize == "pickle":
                value = pickle.dumps(value)
            
            if ttl > 0:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"缓存写入失败 {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """删除缓存"""
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.redis.exists(key) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        return await self.redis.expire(key, ttl)
    
    # ==================== 业务专用缓存方法 ====================
    
    async def get_patient_info(self, patient_id: int) -> Optional[dict]:
        """获取患者信息缓存"""
        key = f"patient:info:{patient_id}"
        return await self.get(key, deserialize="json")
    
    async def set_patient_info(self, patient_id: int, data: dict) -> bool:
        """设置患者信息缓存"""
        key = f"patient:info:{patient_id}"
        return await self.set(
            key,
            data,
            ttl=settings.CACHE_PATIENT_INFO_TTL,
            serialize="json"
        )
    
    async def invalidate_patient_cache(self, patient_id: int):
        """清除患者相关的所有缓存"""
        keys = [
            f"patient:info:{patient_id}",
            f"patient:detail:{patient_id}",
            f"ai:prediction:{patient_id}",
        ]
        # 同时清除患者列表缓存
        list_keys = await self.redis.keys("patient:list:*")
        keys.extend([k.decode() if isinstance(k, bytes) else k for k in list_keys])
        await self.delete(*keys)
        logger.info(f"已清除患者 {patient_id} 的所有缓存")
    
    async def get_dicom_metadata(self, series_id: str) -> Optional[dict]:
        """获取DICOM元数据缓存"""
        key = f"dicom:meta:{series_id}"
        return await self.get(key, deserialize="json")
    
    async def set_dicom_metadata(self, series_id: str, metadata: dict) -> bool:
        """设置DICOM元数据缓存"""
        key = f"dicom:meta:{series_id}"
        return await self.set(
            key,
            metadata,
            ttl=settings.CACHE_DICOM_META_TTL,
            serialize="json"
        )
    
    async def get_ai_result(self, case_id: int, result_type: str) -> Optional[Any]:
        """
        获取AI分析结果缓存
        :param case_id: 病例ID
        :param result_type: 结果类型 (segmentation/prediction/features)
        """
        key = f"ai:{result_type}:{case_id}"
        # AI结果可能是大型numpy数组，使用pickle序列化
        return await self.get(key, deserialize="pickle")
    
    async def set_ai_result(
        self,
        case_id: int,
        result_type: str,
        result_data: Any
    ) -> bool:
        """设置AI分析结果缓存"""
        key = f"ai:{result_type}:{case_id}"
        return await self.set(
            key,
            result_data,
            ttl=settings.CACHE_AI_RESULT_TTL,
            serialize="pickle"
        )
    
    async def get_cached_list(
        self,
        list_type: str,
        page: int,
        page_size: int
    ) -> Optional[dict]:
        """获取列表缓存"""
        key = f"{list_type}:list:page:{page}:size:{page_size}"
        return await self.get(key, deserialize="json")
    
    async def set_cached_list(
        self,
        list_type: str,
        page: int,
        page_size: int,
        data: dict,
        ttl: int = 600
    ) -> bool:
        """设置列表缓存"""
        key = f"{list_type}:list:page:{page}:size:{page_size}"
        return await self.set(key, data, ttl=ttl, serialize="json")
    
    # ==================== 缓存预热 ====================
    
    async def warmup_patient_cache(self, patient_ids: list[int]):
        """批量预热患者缓存"""
        logger.info(f"开始预热 {len(patient_ids)} 个患者的缓存")
        # 这里应该从数据库批量查询并写入缓存
        # 实际实现时需要注入数据库依赖
        pass


# 全局缓存管理器实例
cache_manager = CacheManager()


async def get_cache() -> CacheManager:
    """依赖注入：获取缓存管理器"""
    return cache_manager

