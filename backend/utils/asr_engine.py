from abc import ABC, abstractmethod
from flask import current_app
import os
import subprocess
import json
try:
    import whisper
except ImportError:
    whisper = None

try:
    from funasr import AutoModel
except ImportError:
    AutoModel = None

class ASREngine(ABC):
    @abstractmethod
    def perform_asr(self, video_path):
        """对视频执行ASR处理，返回识别结果列表"""
        pass

class WhisperASREngine(ASREngine):
    def __init__(self, model_name="base"):
        if whisper is None:
            current_app.logger.error("Whisper库未安装，无法进行ASR处理")
            self.model = None
        else:
            try:
                self.model = whisper.load_model(model_name)
            except Exception as e:
                current_app.logger.error(f"加载Whisper模型失败: {e}")
                self.model = None

    def perform_asr(self, video_path):
        if not self.model:
            return None
        audio_path = video_path.replace('.mp4', '.wav')
        try:
            cmd = f"ffmpeg -i \"{video_path}\" -ab 160k -ac 2 -ar 44100 -vn \"{audio_path}\""
            subprocess.call(cmd, shell=True)
        except Exception as e:
            current_app.logger.error(f"提取音频失败: {e}")
            return None
        try:
            result = self.model.transcribe(
                audio_path,
                fp16=False,
                verbose=True
            )
            segments = result.get("segments", [])
        except Exception as e:
            current_app.logger.error(f"语音识别出错: {e}")
            segments = []
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        return segments

class FunASREngine(ASREngine):
    def __init__(self, model_name="paraformer-zh", cache_dir="/root/.cache/modelscope"):
        if AutoModel is None:
            current_app.logger.error("FunASR库未安装，无法进行ASR处理")
            self.model = None
        else:
            try:
                # 确保缓存目录存在
                os.makedirs(cache_dir, exist_ok=True)
                
                # 初始化FunASR模型
                self.model = AutoModel(
                    model=model_name,
                    vad_model="fsmn-vad",
                    punc_model="ct-punc",
                    ncpu=4,
                    device="cpu",
                    disable_update=True,
                    cache_dir=cache_dir,
                )
                current_app.logger.info(f"FunASR模型 {model_name} 加载成功")
            except Exception as e:
                current_app.logger.error(f"加载FunASR模型失败: {e}")
                self.model = None

    def perform_asr(self, video_path):
        if not self.model:
            return None
            
        audio_path = video_path.replace('.mp4', '.wav')
        try:
            # 提取音频
            cmd = f"ffmpeg -i \"{video_path}\" -ab 160k -ac 2 -ar 16000 -vn \"{audio_path}\""
            subprocess.call(cmd, shell=True)
        except Exception as e:
            current_app.logger.error(f"提取音频失败: {e}")
            return None
            
        try:
            # 使用FunASR进行语音识别
            result = self.model.generate(
                input=audio_path,
                batch_size_s=120,
                sentence_timestamp=True,
            )
            
            # 转换FunASR格式为Whisper兼容格式
            segments = self._convert_funasr_to_whisper_format(result)
            current_app.logger.info(f"FunASR识别完成，共 {len(segments)} 个片段")
            
        except Exception as e:
            current_app.logger.error(f"FunASR语音识别出错: {e}")
            segments = []
        finally:
            # 清理临时音频文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
        return segments
    
    def _convert_funasr_to_whisper_format(self, funasr_result):
        """
        将FunASR的输出格式转换为Whisper兼容的格式
        
        FunASR输出示例:
        [{'key': 'asr_example', 'text': '欢迎大家来到魔搭社区进行体验。', 
          'timestamp': [[1080, 1320], [1320, 1560], ...], 
          'sentence_info': [{'text': '欢迎大家来到魔搭社区进行体验。', 'start': 1080, 'end': 4375, ...}]}]
        
        Whisper输出格式:
        [{'start': 1.08, 'end': 4.375, 'text': '欢迎大家来到魔搭社区进行体验。', 'id': 0}]
        """
        segments = []
        segment_id = 0
        
        for item in funasr_result:
            if 'sentence_info' in item and item['sentence_info']:
                # 使用sentence_info中的信息，这里包含了完整的句子级别信息
                for sentence in item['sentence_info']:
                    segment = {
                        'id': segment_id,
                        'start': sentence['start'] / 1000.0,  # 转换毫秒为秒
                        'end': sentence['end'] / 1000.0,      # 转换毫秒为秒  
                        'text': sentence['text'].strip(),
                    }
                    segments.append(segment)
                    segment_id += 1
            elif 'text' in item and 'timestamp' in item:
                # 如果没有sentence_info，使用整体的text和时间戳
                timestamps = item['timestamp']
                if timestamps:
                    start_time = timestamps[0][0] / 1000.0  # 第一个词的开始时间
                    end_time = timestamps[-1][1] / 1000.0   # 最后一个词的结束时间
                    
                    segment = {
                        'id': segment_id,
                        'start': start_time,
                        'end': end_time,
                        'text': item['text'].strip(),
                    }
                    segments.append(segment)
                    segment_id += 1
        
        return segments

class JsonASREngine(ASREngine):
    def perform_asr(self, video_path):
        """从视频同名JSON文件读取字幕信息"""
        json_path = video_path.replace('.mp4', '.json')
        
        if not os.path.exists(json_path):
            current_app.logger.error(f"JSON文件不存在: {json_path}")
            return None
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            body = data.get('body', [])
            segments = []
            
            for item in body:
                segment = {
                    'start': item.get('from', 0),
                    'end': item.get('to', 0),
                    'text': item.get('content', ''),
                    'id': item.get('sid', 0)
                }
                segments.append(segment)
            
            current_app.logger.info(f"成功从JSON文件读取 {len(segments)} 个字幕段落")
            return segments
            
        except Exception as e:
            current_app.logger.error(f"读取JSON文件失败: {e}")
            return None

