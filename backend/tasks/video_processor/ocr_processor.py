"""
OCR处理模块
负责处理视频关键帧的OCR文字识别
"""

import os
from flask import current_app
from utils.ocr_engine import CnOcrEngine, TencentOCR, PaddleOCREngine

class OCRProcessor:
    """OCR处理器类"""
    
    def __init__(self, ocr_engine=None):
        """
        初始化OCR处理器
        
        参数:
            ocr_engine: OCR引擎实例，默认为None，将根据配置选择引擎
        """
        if ocr_engine:
            self.ocr_engine = ocr_engine
        else:
            # 根据配置选择OCR引擎
            ocr_type = current_app.config.get('OCR_ENGINE', 'cnocr').lower()
            if ocr_type == 'tencent':
                self.ocr_engine = TencentOCR()
            elif ocr_type == 'paddle':
                # 支持额外的PaddleOCR配置
                use_gpu = current_app.config.get('PADDLE_OCR_USE_GPU', False)
                lang = current_app.config.get('PADDLE_OCR_LANG', 'ch')
                use_angle_cls = current_app.config.get('PADDLE_OCR_USE_ANGLE_CLS', True)
                self.ocr_engine = PaddleOCREngine(
                    use_angle_cls=use_angle_cls,
                    lang=lang,
                    use_gpu=use_gpu
                )
            else:
                self.ocr_engine = CnOcrEngine()
        
    def perform_ocr(self, keyframes_data, output_folder):
        """
        对关键帧进行OCR处理，提取文字信息
        
        参数:
            keyframes_data: 关键帧数据列表
            output_folder: 输出文件夹路径
            
        返回:
            处理后的关键帧数据列表
        """
        return self.ocr_engine.perform_ocr(keyframes_data, output_folder)