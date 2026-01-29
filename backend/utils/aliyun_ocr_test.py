# -*- coding: utf-8 -*-
import os
import sys
import base64
import json
from typing import List, Optional
from PIL import Image
import io

from alibabacloud_ocr_api20210707.client import Client as ocr_api20210707Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ocr_api20210707 import models as ocr_api_20210707_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from utils.ocr_engine import OCREngine


class AliyunOCREngine(OCREngine):
    def __init__(self, access_key_id: str, access_key_secret: str):
        """
        初始化阿里云OCR客户端
        :param access_key_id: 访问密钥ID
        :param access_key_secret: 访问密钥密码
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id='cn-hangzhou'
        )
        config.endpoint = 'ocr-api.cn-hangzhou.aliyuncs.com'
        self.client = ocr_api20210707Client(config)

    def perform_ocr(self, keyframes_data, output_folder):
        """对关键帧列表执行OCR处理，返回更新后的关键帧数据"""
        for frame_info in keyframes_data:
            image_path = os.path.join(output_folder, frame_info.get("file_name", ""))
            result = self.recognize_general(image_path=image_path)
            texts = []
            raw = []
            if result and result.get("Data") and result["Data"].get("Blocks"):
                for block in result["Data"]["Blocks"]:
                    text = block.get("Text", "")
                    texts.append(text)
                    raw.append(block)
            frame_info["ocr_result"] = texts
            frame_info["ocr_result_raw"] = raw
        return keyframes_data

    def recognize_general(self, image_url: str = None, image_path: str = None) -> Optional[dict]:
        """
        通用文字识别
        :param image_url: 图片URL
        :param image_path: 图片路径
        :return: 识别结果
        """
        try:
            # 构建请求
            recognize_request = ocr_api_20210707_models.RecognizeAllTextRequest(
                url=image_url or 'https://img.alicdn.com/tfs/TB1q5IeXAvoK1RjSZFNXXcxMVXa-483-307.jpg',  # 使用示例图片URL
                type='General'  # 使用通用文字识别类型
            )
            
            runtime = util_models.RuntimeOptions(
                connect_timeout=10000,
                read_timeout=10000,
                autoretry=True,
                ignore_ssl=False,
                max_attempts=3
            )

            # 打印请求信息
            print("\n请求配置信息：")
            print(f"Endpoint: {self.client._endpoint}")
            print(f"Region ID: {self.client._region_id}")
            print(f"图片URL: {recognize_request.url}")

            # 发送请求
            print("\n正在发送请求到阿里云OCR服务...")
            response = self.client.recognize_all_text_with_options(recognize_request, runtime)
            print("收到响应...")

            # 转换响应为字典并返回
            result = response.body.to_map()
            return result

        except Exception as error:
            print(f"\nOCR识别出错:")
            print(f"错误类型: {type(error).__name__}")
            print(f"错误信息: {error.message if hasattr(error, 'message') else str(error)}")
            
            # 打印详细的错误信息
            if hasattr(error, 'data') and isinstance(error.data, dict):
                print("\n详细错误信息：")
                print(json.dumps(error.data, ensure_ascii=False, indent=2))
                print(f"\n诊断链接: {error.data.get('Recommend', '无')}")
            
            return None