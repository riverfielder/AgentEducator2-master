from abc import ABC, abstractmethod
import os
import json
import base64
from flask import current_app
try:
    from cnocr import CnOcr
except ImportError:
    CnOcr = None

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PaddleOCR = None
    PADDLE_AVAILABLE = False

try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.ocr.v20181119 import ocr_client, models
    TENCENT_AVAILABLE = True
except ImportError:
    TENCENT_AVAILABLE = False

class OCREngine(ABC):
    @abstractmethod
    def perform_ocr(self, keyframes_data, output_folder):
        """对关键帧列表执行OCR处理，返回更新后的关键帧数据"""
        pass

class CnOcrEngine(OCREngine):
    def __init__(self):
        if CnOcr is None:
            current_app.logger.error("cnocr库未安装，无法进行OCR处理")
            self.ocr = None
        else:
            self.ocr = CnOcr(rec_model_name="ch_PP-OCRv4_server")

    def perform_ocr(self, keyframes_data, output_folder):
        if not self.ocr:
            return keyframes_data
        for frame_info in keyframes_data:
            image_path = os.path.join(output_folder, frame_info["file_name"])
            try:
                result = self.ocr.ocr(image_path)
                texts = []
                serializable_result = []
                for item in result:
                    if isinstance(item, dict) and 'position' in item and 'text' in item:
                        position_list = item['position'].tolist() if hasattr(item['position'], 'tolist') else item['position']
                        serializable_item = {
                            'position': position_list,
                            'score': float(item.get('score', 0.0)),
                            'text': item['text']
                        }
                        serializable_result.append(serializable_item)
                        texts.append(item['text'])
                frame_info["ocr_result"] = texts
                frame_info["ocr_result_raw"] = serializable_result
            except Exception as e:
                current_app.logger.error(f"OCR处理图片出错: {str(e)}")
                frame_info["ocr_result"] = []
        return keyframes_data

class PaddleOCREngine(OCREngine):
    """PaddleOCR引擎实现"""
    
    def __init__(self, use_angle_cls=True, lang='ch', use_gpu=False):
        """
        初始化PaddleOCR引擎
        
        参数:
            use_angle_cls: 是否使用角度分类模型
            lang: 语言，默认为中文
            use_gpu: 是否使用GPU
        """
        if not PADDLE_AVAILABLE:
            current_app.logger.error("PaddleOCR库未安装，无法进行OCR处理")
            self.ocr = None
            return
            
        try:
            # 初始化PaddleOCR
            # 根据PaddleOCR v2.7+的API调整参数
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang
            )
            current_app.logger.info("PaddleOCR引擎初始化成功")
        except Exception as e:
            current_app.logger.error(f"PaddleOCR引擎初始化失败: {str(e)}")
            self.ocr = None

    def perform_ocr(self, keyframes_data, output_folder):
        """
        对关键帧进行OCR处理
        
        参数:
            keyframes_data: 关键帧数据列表
            output_folder: 输出文件夹路径
            
        返回:
            处理后的关键帧数据列表
        """
        if not self.ocr:
            return keyframes_data
            
        for frame_info in keyframes_data:
            image_path = os.path.join(output_folder, frame_info["file_name"])
            try:
                # 调用PaddleOCR进行识别
                result = self.ocr.predict(image_path)
                #result = self.ocr.ocr(image_path, cls=True)
                
                texts = []
                serializable_result = []
                
                # 处理PaddleOCR的结果
                # 根据实际输出格式，result可能有两种格式：
                # 1. 新版本：{'res': {...}} 格式
                # 2. 旧版本：[[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)] 格式
                print(f"PaddleOCR识别结果: {result}")
                
                # PaddleOCR返回的是一个列表，每个元素包含一个页面的识别结果
                if result and len(result) > 0:
                    for page_result in result:
                        if page_result is None:
                            continue
                            
                        # 只处理新版本格式（字典格式）
                        if isinstance(page_result, dict):
                            rec_texts = page_result.get('rec_texts', [])
                            rec_scores = page_result.get('rec_scores', [])
                            rec_polys = page_result.get('rec_polys', [])
                            
                            # 确保所有数组长度一致
                            min_length = min(len(rec_texts), len(rec_scores), len(rec_polys))
                            
                            for i in range(min_length):
                                text = rec_texts[i]
                                confidence = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                                position = rec_polys[i].tolist() if hasattr(rec_polys[i], 'tolist') else rec_polys[i]
                                
                                # 跳过空文本
                                if not text or text.strip() == "":
                                    continue
                                    
                                texts.append(text)
                                
                                # 构建与其他OCR引擎兼容的格式
                                serializable_item = {
                                    'position': position,
                                    'score': confidence,
                                    'text': text
                                }
                                serializable_result.append(serializable_item)
                frame_info["ocr_result"] = texts
                frame_info["ocr_result_raw"] = serializable_result
                
                current_app.logger.debug(f"PaddleOCR处理完成，识别到{len(texts)}个文本")
                
            except Exception as e:
                current_app.logger.error(f"PaddleOCR处理图片出错: {str(e)}")
                frame_info["ocr_result"] = []
                frame_info["ocr_result_raw"] = []
                
        return keyframes_data

class TencentOCR(OCREngine):
    def __init__(self):
        self.secret_id = current_app.config.get("TENCENT_OCR_SECRET_ID")
        self.secret_key = current_app.config.get("TENCENT_OCR_SECRET_KEY")
        self.region = current_app.config.get("TENCENT_OCR_REGION", "")
        self.client = None
        
        if not TENCENT_AVAILABLE:
            current_app.logger.error("腾讯云OCR SDK未安装，无法进行OCR处理")
            return
            
        if not all([self.secret_id, self.secret_key]):
            current_app.logger.error("腾讯OCR配置不完整，无法进行OCR处理")
            return
            
        try:
            # 实例化认证对象
            cred = credential.Credential(self.secret_id, self.secret_key)
            
            # 实例化http选项
            httpProfile = HttpProfile()
            httpProfile.endpoint = "ocr.tencentcloudapi.com"
            
            # 实例化client选项
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            # 实例化OCR客户端
            self.client = ocr_client.OcrClient(cred, self.region, clientProfile)
            
        except Exception as e:
            current_app.logger.error(f"腾讯OCR客户端初始化失败: {str(e)}")
            self.client = None

    def _image_to_base64(self, image_path):
        """将图片转换为base64编码"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"图片转换base64失败: {str(e)}")
            return None

    def perform_ocr(self, keyframes_data, output_folder):
        if not self.client:
            return keyframes_data
            
        for frame_info in keyframes_data:
            image_path = os.path.join(output_folder, frame_info["file_name"])
            try:
                # 转换图片为base64
                image_base64 = self._image_to_base64(image_path)
                if not image_base64:
                    frame_info["ocr_result"] = []
                    frame_info["ocr_result_raw"] = []
                    continue
                
                # 实例化请求对象
                req = models.GeneralFastOCRRequest()
                params = {
                    "ImageBase64": image_base64
                }
                req.from_json_string(json.dumps(params))
                
                # 调用OCR接口
                resp = self.client.GeneralFastOCR(req)
                response_data = json.loads(resp.to_json_string())
                
                # 处理响应结果
                texts = []
                serializable_result = []
                
                if "Response" in response_data and "TextDetections" in response_data["Response"]:
                    for detection in response_data["Response"]["TextDetections"]:
                        text = detection.get("DetectedText", "")
                        texts.append(text)
                        
                        # 构建与CnOCR兼容的格式
                        polygon = detection.get("Polygon", [])
                        position = [[point["X"], point["Y"]] for point in polygon] if polygon else []
                        
                        serializable_item = {
                            'position': position,
                            'score': detection.get("Confidence", 0) / 100.0,  # 转换为0-1范围
                            'text': text
                        }
                        serializable_result.append(serializable_item)
                
                frame_info["ocr_result"] = texts
                frame_info["ocr_result_raw"] = serializable_result
                
            except TencentCloudSDKException as e:
                current_app.logger.error(f"腾讯OCR API调用失败: {str(e)}")
                frame_info["ocr_result"] = []
                frame_info["ocr_result_raw"] = []
            except Exception as e:
                current_app.logger.error(f"OCR处理图片出错: {str(e)}")
                frame_info["ocr_result"] = []
                frame_info["ocr_result_raw"] = []
                
        return keyframes_data