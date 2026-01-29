#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分词缓存服务
基于Redis持久化存储文档和视频的分词结果，提升检索性能
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any
from services.redis_service import redis_service
import jieba

logger = logging.getLogger(__name__)

class TokenizationCacheService:
    """分词缓存服务类"""
    
    def __init__(self):
        self.redis = redis_service
        # 缓存键前缀
        self.CACHE_PREFIX = "tokenization:"
        # 缓存过期时间（7天）
        self.CACHE_EXPIRE_SECONDS = 7 * 24 * 3600
        # 版本号，用于缓存失效
        self.CACHE_VERSION = "v1.0"
    
    def _generate_cache_key(self, content: str, content_type: str = "text") -> str:
        """
        生成缓存键
        
        Args:
            content: 文本内容
            content_type: 内容类型（text, document, video等）
            
        Returns:
            缓存键
        """
        # 使用内容的MD5哈希作为键的一部分，确保唯一性
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"{self.CACHE_PREFIX}{self.CACHE_VERSION}:{content_type}:{content_hash}"
    
    def _tokenize_with_jieba(self, text: str) -> List[str]:
        """
        使用jieba进行分词
        
        Args:
            text: 待分词文本
            
        Returns:
            分词结果列表
        """
        if not text:
            return []
        return list(jieba.cut_for_search(text))
    
    def get_cached_tokens(self, content: str, content_type: str = "text",cache_key="") -> Optional[List[str]]:
        """
        获取缓存的分词结果
        
        Args:
            content: 文本内容
            content_type: 内容类型
            cache_key: 缓存键
            
        Returns:
            分词结果列表，如果缓存不存在则返回None
        """
        try:
            if cache_key=="":
                cache_key = self._generate_cache_key(content, content_type)
            cached_data = self.redis.get_with_metadata(cache_key)
            
            if cached_data is not None:
                tokens = cached_data.get('value')
                if isinstance(tokens, list):
                    logger.debug(f"分词缓存命中: {content_type}, 长度: {len(content)}")
                    return tokens
            
            return None
        except Exception as e:
            logger.error(f"获取分词缓存失败: {str(e)}")
            return None
    
    def cache_tokens(self, content: str, tokens: List[str], content_type: str = "text") -> bool:
        """
        缓存分词结果
        
        Args:
            content: 原始文本内容
            tokens: 分词结果
            content_type: 内容类型
            
        Returns:
            是否缓存成功
        """
        try:
            cache_key = self._generate_cache_key(content, content_type)
            metadata = {
                'content_type': content_type,
                'content_length': len(content),
                'token_count': len(tokens),
                'jieba_version': jieba.__version__ if hasattr(jieba, '__version__') else 'unknown'
            }
            
            success = self.redis.set_with_metadata(
                cache_key, 
                tokens, 
                expire_seconds=self.CACHE_EXPIRE_SECONDS,
                metadata=metadata
            )
            
            if success:
                logger.debug(f"分词结果已缓存: {content_type}, 长度: {len(content)}, 词数: {len(tokens)}")
            
            return success
        except Exception as e:
            logger.error(f"缓存分词结果失败: {str(e)}")
            return False
    
    def get_or_create_tokens(self, content: str, content_type: str = "text",cache_key="") -> List[str]:
        """
        获取或创建分词结果（带缓存）
        
        Args:
            content: 文本内容
            content_type: 内容类型
            
        Returns:
            分词结果列表
        """
        # 先尝试从缓存获取
        cached_tokens = self.get_cached_tokens(content, content_type)
        if cached_tokens is not None:
            return cached_tokens
        
        # 缓存未命中，执行分词
        tokens = self._tokenize_with_jieba(content)
        
        # 缓存结果
        self.cache_tokens(content, tokens, content_type)
        
        logger.debug(f"新分词结果: {content_type}, 长度: {len(content)}, 词数: {len(tokens)}")
        return tokens
    
    def batch_cache_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量缓存文档分词结果
        
        Args:
            documents: 文档列表，每个文档包含id和content字段
            
        Returns:
            统计信息：{'cached': 缓存数量, 'skipped': 跳过数量, 'failed': 失败数量}
        """
        stats = {'cached': 0, 'skipped': 0, 'failed': 0}
        
        for doc in documents:
            try:
                doc_id = doc.get('id')
                content = doc.get('content', '')
                
                if not content:
                    stats['skipped'] += 1
                    continue
                
                # 检查是否已缓存
                if self.get_cached_tokens(content, 'document') is not None:
                    stats['skipped'] += 1
                    continue
                
                # 执行分词并缓存
                tokens = self._tokenize_with_jieba(content)
                if self.cache_tokens(content, tokens, 'document'):
                    stats['cached'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"批量缓存文档失败 {doc.get('id', 'unknown')}: {str(e)}")
                stats['failed'] += 1
        
        logger.info(f"批量缓存完成: {stats}")
        return stats
    
    def invalidate_cache(self, content_type: Optional[str] = None) -> int:
        """
        清除分词缓存
        
        Args:
            content_type: 内容类型，如果为None则清除所有分词缓存
            
        Returns:
            清除的缓存数量
        """
        try:
            if content_type:
                pattern = f"{self.CACHE_PREFIX}{self.CACHE_VERSION}:{content_type}:*"
            else:
                pattern = f"{self.CACHE_PREFIX}*"
            
            count = self.redis.invalidate_pattern(pattern)
            logger.info(f"清除分词缓存: {content_type or 'all'}, 数量: {count}")
            return count
        except Exception as e:
            logger.error(f"清除分词缓存失败: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        try:
            total_keys = self.redis.count_keys(f"{self.CACHE_PREFIX}*")
            current_version_keys = self.redis.count_keys(f"{self.CACHE_PREFIX}{self.CACHE_VERSION}:*")
            
            # 按内容类型统计
            type_stats = {}
            for content_type in ['text', 'document', 'video']:
                pattern = f"{self.CACHE_PREFIX}{self.CACHE_VERSION}:{content_type}:*"
                count = self.redis.count_keys(pattern)
                type_stats[content_type] = count
            
            return {
                'total_cache_keys': total_keys,
                'current_version_keys': current_version_keys,
                'cache_version': self.CACHE_VERSION,
                'type_distribution': type_stats,
                'redis_connected': self.redis.is_connected()
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {'error': str(e)}
    
    def warm_up_cache(self) -> Dict[str, int]:
        """
        预热缓存：为现有文档和视频内容创建分词缓存
        
        Returns:
            预热统计信息
        """
        try:
            from models.models import Document, DocumentSegment, Video, VideoKeyframe
            
            stats = {'documents': 0, 'video_segments': 0, 'failed': 0}
            
            # 预热文档内容
            documents = Document.query.filter(
                Document.is_deleted == False,
                Document.markitdown_content.isnot(None)
            ).all()
            
            for doc in documents:
                try:
                    if doc.markitdown_content:
                        self.get_or_create_tokens(doc.markitdown_content, 'document')
                        stats['documents'] += 1
                except Exception as e:
                    logger.error(f"预热文档缓存失败 {doc.id}: {str(e)}")
                    stats['failed'] += 1
            
            # 预热文档段落
            segments = DocumentSegment.query.filter(
                DocumentSegment.content.isnot(None)
            ).all()
            
            for segment in segments:
                try:
                    if segment.content:
                        self.get_or_create_tokens(segment.content, 'document_segment')
                        stats['documents'] += 1
                except Exception as e:
                    logger.error(f"预热文档段落缓存失败 {segment.id}: {str(e)}")
                    stats['failed'] += 1
            
            # 预热视频关键帧内容
            keyframes = VideoKeyframe.query.filter(
                VideoKeyframe.ocr_text.isnot(None)
            ).all()
            
            for keyframe in keyframes:
                try:
                    if keyframe.ocr_text:
                        self.get_or_create_tokens(keyframe.ocr_text, 'video_ocr')
                        stats['video_segments'] += 1
                    if keyframe.asr_text:
                        self.get_or_create_tokens(keyframe.asr_text, 'video_asr')
                        stats['video_segments'] += 1
                except Exception as e:
                    logger.error(f"预热视频缓存失败 {keyframe.id}: {str(e)}")
                    stats['failed'] += 1
            
            logger.info(f"缓存预热完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"缓存预热失败: {str(e)}")
            return {'error': str(e)}

# 全局分词缓存服务实例
tokenization_cache_service = TokenizationCacheService()