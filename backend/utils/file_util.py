import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt'}

def allowed_file(filename):
    """
    检查文件扩展名是否被允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    """
    检查视频文件扩展名是否被允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_document_file(filename):
    """
    检查文档文件扩展名是否被允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOCUMENT_EXTENSIONS

def get_upload_base_path():
    """
    获取文件上传的基础路径，优先从环境变量读取
    """
    from config.config import Config
    return Config.get_upload_base_path()

def get_upload_folder(file_type):
    """
    根据文件类型获取上传文件夹路径
    
    Args:
        file_type: 文件类型 (image, video, document, avatar)
        
    Returns:
        文件夹路径
    """
    from config.config import Config
    base_path = Config.get_upload_base_path()
    folder_name = Config.get_upload_folder(file_type)
    return os.path.join(base_path, folder_name)

def save_file(file, file_type='image'):
    """
    保存上传的文件
    
    Args:
        file: FileStorage对象
        file_type: 文件类型 (image, video, document, avatar)
        
    Returns:
        保存后的文件URL路径
    """
    # 获取原始文件名和扩展名
    original_filename = file.filename
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        # 只对文件名部分使用secure_filename，保留扩展名
        safe_name = secure_filename(name)
        # 如果secure_filename移除了所有字符，使用默认名称
        if not safe_name or safe_name.strip() == '':
            safe_name = 'document'
        filename = f"{safe_name}.{ext}"
    else:
        filename = secure_filename(original_filename)
        # 如果secure_filename移除了所有字符，使用默认名称
        if not filename or filename.strip() == '':
            filename = 'document'
    
    # 根据文件类型获取上传文件夹路径（支持环境变量配置）
    upload_folder = get_upload_folder(file_type)
    
    # 确保目录存在
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # 保存文件
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # 返回文件的URL路径（相对于基础路径）
    base_path = get_upload_base_path()
    folder_name = os.path.basename(upload_folder)
    
    # 如果基础路径不是当前目录，需要调整返回的URL路径
    if base_path == '.':
        return f"/{folder_name}/{unique_filename}"
    else:
        # 相对于项目根目录的路径
        return f"/{folder_name}/{unique_filename}"

def get_full_path(file_url, file_type='document'):
    """
    根据文件URL和类型获取完整的本地文件路径
    
    Args:
        file_url: 文件URL路径（如 "/temp_docs/xxx.pdf"）
        file_type: 文件类型 (document, video, image, avatar)
        
    Returns:
        完整的本地文件路径
    """
    # 如果file_url已经是系统的绝对路径，直接返回
    if os.path.isabs(file_url) and not file_url.startswith('/'):
        return file_url
    
    # 移除开头的斜杠（Unix风格路径）
    clean_url = file_url.lstrip('/')
    
    # 获取基础路径
    base_path = get_upload_base_path()
    
    # 如果基础路径是相对路径，转换为绝对路径
    if not os.path.isabs(base_path):
        base_path = os.path.abspath(base_path)
    
    # 拼接完整路径
    full_path = os.path.join(base_path, clean_url)
    
    return full_path
