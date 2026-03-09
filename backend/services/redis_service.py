#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存服务
提供统一的Redis操作接口，支持序列化和反序列化
"""

import redis
import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class RedisService:
    """Redis缓存服务类"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, password: str = None, db: int = 0):
        """
        初始化Redis连接
        
        Args:
            host: Redis主机地址
            port: Redis端口
            password: Redis密码
            db: Redis数据库编号
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=False,  # 使用二进制模式以支持pickle
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=False,
                health_check_interval=30
            )
            
            # 测试连接
            try:
                self.redis_client.ping()
                logger.info(f"Redis连接成功: {host}:{port}")
            except Exception as ping_error:
                # Ping失败也视为连接失败，降级到内存模式
                raise ping_error
            
        except Exception as e:
            # 打印详细错误信息到控制台，确保看到
            print(f"[RedisService] Redis连接失败，切换到内存模式: {str(e)}")
            logger.error(f"Redis连接失败: {str(e)}")
            # 使用内存字典作为降级方案
            self.redis_client = None
            self._memory_cache = {}
            logger.warning("使用内存缓存作为Redis降级方案")
    
    def is_connected(self) -> bool:
        """检查Redis连接状态"""
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _serialize_value(self, value: Any) -> bytes:
        """序列化值"""
        if isinstance(value, (str, int, float, bool)):
            # 简单类型使用JSON
            return json.dumps(value).encode('utf-8')
        else:
            # 复杂类型使用pickle
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """反序列化值"""
        try:
            # 先尝试JSON反序列化
            return json.loads(value.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # JSON失败则使用pickle
            return pickle.loads(value)
    
    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_seconds: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            serialized_value = self._serialize_value(value)
            
            if self.redis_client:
                return self.redis_client.set(key, serialized_value, ex=expire_seconds)
            else:
                self._memory_cache[key] = {
                    'value': value,
                    'expire_at': datetime.now() + timedelta(seconds=expire_seconds) if expire_seconds else None
                }
                return True
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False

    def get(self, key: str) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return self._deserialize_value(value)
                return None
            else:
                item = self._memory_cache.get(key)
                if not item:
                    return None
                
                if item['expire_at'] and datetime.now() > item['expire_at']:
                    del self._memory_cache[key]
                    return None
                
                return item['value']
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None


    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            if self.redis_client is not None:
                return self.redis_client.delete(key) > 0
            else:
                # 降级到内存缓存
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Redis删除失败 {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            if self.redis_client is not None:
                return self.redis_client.exists(key) > 0
            else:
                # 降级到内存缓存
                cache_item = self._memory_cache.get(key)
                if cache_item is None:
                    return False
                
                # 检查是否过期
                if cache_item['expire_time'] and datetime.now() > cache_item['expire_time']:
                    del self._memory_cache[key]
                    return False
                
                return True
        except Exception as e:
            logger.error(f"Redis检查存在失败 {key}: {str(e)}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            if self.redis_client is not None:
                return self.redis_client.expire(key, seconds)
            else:
                # 降级到内存缓存
                if key in self._memory_cache:
                    self._memory_cache[key]['expire_time'] = datetime.now() + timedelta(seconds=seconds)
                    return True
                return False
        except Exception as e:
            logger.error(f"Redis设置过期时间失败 {key}: {str(e)}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        try:
            if self.redis_client is not None:
                return self.redis_client.ttl(key)
            else:
                # 降级到内存缓存
                cache_item = self._memory_cache.get(key)
                if cache_item is None:
                    return -2
                
                if cache_item['expire_time'] is None:
                    return -1
                
                remaining = cache_item['expire_time'] - datetime.now()
                if remaining.total_seconds() <= 0:
                    del self._memory_cache[key]
                    return -2
                
                return int(remaining.total_seconds())
        except Exception as e:
            logger.error(f"Redis获取TTL失败 {key}: {str(e)}")
            return -2
    
    def keys(self, pattern: str = '*') -> List[str]:
        """
        获取匹配模式的所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            键列表
        """
        try:
            if self.redis_client is not None:
                keys = self.redis_client.keys(pattern)
                return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
            else:
                # 降级到内存缓存（简单实现）
                import fnmatch
                return [key for key in self._memory_cache.keys() if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            logger.error(f"Redis获取键列表失败 {pattern}: {str(e)}")
            return []
    
    def flush_db(self) -> bool:
        """
        清空当前数据库
        
        Returns:
            是否清空成功
        """
        try:
            if self.redis_client is not None:
                return self.redis_client.flushdb()
            else:
                # 降级到内存缓存
                self._memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Redis清空数据库失败: {str(e)}")
            return False
    
    def set_with_metadata(self, key: str, value: Any, expire_seconds: Optional[int] = None, 
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        设置带元数据的缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_seconds: 过期时间（秒）
            metadata: 元数据字典
            
        Returns:
            是否设置成功
        """
        cache_data = {
            'value': value,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        return self.set(key, cache_data, expire_seconds)
    
    def get_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取带元数据的缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            包含value、created_at、metadata的字典，不存在则返回None
        """
        cache_data = self.get(key)
        if cache_data is None:
            return None
        
        # 兼容旧格式
        if not isinstance(cache_data, dict) or 'value' not in cache_data:
            return {
                'value': cache_data,
                'created_at': datetime.now().isoformat(),
                'metadata': {}
            }
        
        return cache_data
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            删除的键数量
        """
        try:
            keys_to_delete = self.keys(pattern)
            if not keys_to_delete:
                return 0
            
            count = 0
            for key in keys_to_delete:
                if self.delete(key):
                    count += 1
            
            logger.info(f"删除缓存模式 {pattern}: {count} 个键")
            return count
        except Exception as e:
            logger.error(f"删除缓存模式失败 {pattern}: {str(e)}")
            return 0
    
    def count_keys(self, pattern: str = '*') -> int:
        """
        统计匹配模式的键数量
        
        Args:
            pattern: 匹配模式
            
        Returns:
            匹配的键数量
        """
        try:
            keys = self.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"统计键数量失败 {pattern}: {str(e)}")
            return 0
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取Redis内存使用情况
        
        Returns:
            内存使用统计信息
        """
        try:
            if self.redis_client is not None:
                info = self.redis_client.info('memory')
                return {
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'used_memory_peak': info.get('used_memory_peak', 0),
                    'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                    'total_system_memory': info.get('total_system_memory', 0),
                    'total_system_memory_human': info.get('total_system_memory_human', '0B')
                }
            else:
                # 降级到内存缓存统计
                import sys
                cache_size = sys.getsizeof(self._memory_cache)
                return {
                    'used_memory': cache_size,
                    'used_memory_human': f'{cache_size}B',
                    'cache_type': 'memory_fallback',
                    'cache_entries': len(self._memory_cache)
                }
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {str(e)}")
            return {'error': str(e)}
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取Redis连接信息
        
        Returns:
            连接信息统计
        """
        try:
            if self.redis_client is not None:
                info = self.redis_client.info('clients')
                server_info = self.redis_client.info('server')
                return {
                    'connected': True,
                    'connected_clients': info.get('connected_clients', 0),
                    'redis_version': server_info.get('redis_version', 'unknown'),
                    'uptime_in_seconds': server_info.get('uptime_in_seconds', 0),
                    'role': server_info.get('role', 'unknown')
                }
            else:
                return {
                    'connected': False,
                    'fallback_mode': 'memory_cache',
                    'cache_entries': len(self._memory_cache)
                }
        except Exception as e:
            logger.error(f"获取连接信息失败: {str(e)}")
            return {'connected': False, 'error': str(e)}

# 全局Redis服务实例
redis_service = RedisService()
