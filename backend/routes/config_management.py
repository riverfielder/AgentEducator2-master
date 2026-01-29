"""配置管理路由模块"""
from flask import Blueprint, request, jsonify, current_app
from config.config import Config

config_bp = Blueprint('config', __name__, url_prefix='/api/config')

@config_bp.route('/get', methods=['GET'])
def get_config():
    """获取当前配置"""
    try:
        # 获取配置键
        key = request.args.get('key')
        
        if key:
            # 获取单个配置值
            value = Config.get_config_value(key)
            return jsonify({
                'success': True,
                'key': key,
                'value': value
            })
        else:
            # 获取所有覆盖的配置
            overrides = Config.get_all_overrides()
            
            # 获取一些常用配置的当前值
            common_configs = {
                'OPENAI_API_KEY': Config.get_openai_api_key(),
                'SILICON_API_BASE': Config.get_silicon_api_base(),
                'NEO4J_URI': Config.get_neo4j_uri(),
                'NEO4J_USERNAME': Config.get_neo4j_username(),
                'NEO4J_PASSWORD': Config.get_neo4j_password(),
                'UPLOAD_BASE_PATH': Config.get_upload_base_path(),
                'UPLOAD_IMAGE_FOLDER': Config.get_upload_folder('image'),
                'UPLOAD_VIDEO_FOLDER': Config.get_upload_folder('video'),
                'UPLOAD_DOCUMENT_FOLDER': Config.get_upload_folder('document'),
                'UPLOAD_AVATAR_FOLDER': Config.get_upload_folder('avatar'),
                'UPLOAD_DEFAULT_FOLDER': Config.get_upload_folder('default'),
                'AGENT_MODE_ENABLED': Config.is_agent_mode_enabled(),
                'AGENT_MAX_ITERATIONS': Config.get_agent_max_iterations(),
                'AGENT_HANDLE_PARSING_ERRORS': Config.is_agent_handle_parsing_errors(),
                'AGENT_VERBOSE': Config.is_agent_verbose(),
            }
            
            return jsonify({
                'success': True,
                'current_values': common_configs,
                'runtime_overrides': overrides
            })
            
    except Exception as e:
        current_app.logger.error(f"获取配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500

@config_bp.route('/set', methods=['POST'])
def set_config():
    """设置配置值"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
            
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return jsonify({
                'success': False,
                'message': 'key参数不能为空'
            }), 400
        
        # 设置配置值
        Config.set_config_value(key, value)
        
        current_app.logger.info(f"配置已更新: {key} = {value}")
        
        return jsonify({
            'success': True,
            'message': f'配置 {key} 已成功更新',
            'key': key,
            'value': value
        })
        
    except Exception as e:
        current_app.logger.error(f"设置配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'设置配置失败: {str(e)}'
        }), 500

@config_bp.route('/reset', methods=['POST'])
def reset_config():
    """重置配置值"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
            
        key = data.get('key')
        
        if not key:
            return jsonify({
                'success': False,
                'message': 'key参数不能为空'
            }), 400
        
        # 重置配置值
        Config.reset_config_value(key)
        
        current_app.logger.info(f"配置已重置: {key}")
        
        return jsonify({
            'success': True,
            'message': f'配置 {key} 已重置为默认值',
            'key': key
        })
        
    except Exception as e:
        current_app.logger.error(f"重置配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重置配置失败: {str(e)}'
        }), 500

@config_bp.route('/clear-all', methods=['POST'])
def clear_all_config():
    """清除所有运行时配置覆盖"""
    try:
        Config.clear_all_overrides()
        
        current_app.logger.info("所有运行时配置覆盖已清除")
        
        return jsonify({
            'success': True,
            'message': '所有运行时配置覆盖已清除'
        })
        
    except Exception as e:
        current_app.logger.error(f"清除配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清除配置失败: {str(e)}'
        }), 500

@config_bp.route('/batch-set', methods=['POST'])
def batch_set_config():
    """批量设置配置值"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
            
        configs = data.get('configs', {})
        
        if not isinstance(configs, dict):
            return jsonify({
                'success': False,
                'message': 'configs必须是一个对象'
            }), 400
        
        # 批量设置配置值
        for key, value in configs.items():
            Config.set_config_value(key, value)
        
        current_app.logger.info(f"批量配置已更新: {list(configs.keys())}")
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {len(configs)} 个配置项',
            'updated_configs': configs
        })
        
    except Exception as e:
        current_app.logger.error(f"批量设置配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量设置配置失败: {str(e)}'
        }), 500

@config_bp.route('/validate', methods=['POST'])
def validate_config():
    """验证配置值是否有效"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
            
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return jsonify({
                'success': False,
                'message': 'key参数不能为空'
            }), 400
        
        # 进行配置验证
        validation_result = _validate_config_value(key, value)
        
        return jsonify({
            'success': True,
            'valid': validation_result['valid'],
            'message': validation_result['message'],
            'key': key,
            'value': value
        })
        
    except Exception as e:
        current_app.logger.error(f"验证配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'验证配置失败: {str(e)}'
        }), 500

def _validate_config_value(key: str, value) -> dict:
    """验证配置值的有效性"""
    import os
    from urllib.parse import urlparse
    
    try:
        if key in ['OPENAI_API_KEY']:
            if not value or not isinstance(value, str):
                return {'valid': False, 'message': 'API Key 必须是非空字符串'}
            return {'valid': True, 'message': 'API Key 格式有效'}
        
        elif key in ['SILICON_API_BASE', 'NEO4J_URI']:
            if not value or not isinstance(value, str):
                return {'valid': False, 'message': 'URL 必须是非空字符串'}
            try:
                parsed = urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    return {'valid': False, 'message': 'URL 格式无效'}
                return {'valid': True, 'message': 'URL 格式有效'}
            except Exception:
                return {'valid': False, 'message': 'URL 解析失败'}
        
        elif key in ['NEO4J_USERNAME', 'NEO4J_PASSWORD']:
            if not value or not isinstance(value, str):
                return {'valid': False, 'message': '用户名/密码必须是非空字符串'}
            return {'valid': True, 'message': '用户名/密码格式有效'}
        
        elif key.startswith('UPLOAD_') and key.endswith('_FOLDER'):
            if not value or not isinstance(value, str):
                return {'valid': False, 'message': '文件夹路径必须是非空字符串'}
            # 检查路径是否包含不安全字符
            unsafe_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
            if any(char in value for char in unsafe_chars):
                return {'valid': False, 'message': '文件夹名包含不安全字符'}
            return {'valid': True, 'message': '文件夹路径格式有效'}
        
        elif key == 'UPLOAD_BASE_PATH':
            if not value or not isinstance(value, str):
                return {'valid': False, 'message': '基础路径必须是非空字符串'}
            return {'valid': True, 'message': '基础路径格式有效'}
        
        elif key == 'AGENT_MODE_ENABLED':
            if isinstance(value, bool):
                return {'valid': True, 'message': '布尔值有效'}
            elif isinstance(value, str) and value.lower() in ['true', 'false']:
                return {'valid': True, 'message': '布尔字符串有效'}
            else:
                return {'valid': False, 'message': '必须是布尔值或 "true"/"false" 字符串'}
        
        elif key == 'AGENT_MAX_ITERATIONS':
            try:
                int_val = int(value)
                if int_val <= 0:
                    return {'valid': False, 'message': '最大迭代次数必须大于0'}
                if int_val > 50:
                    return {'valid': False, 'message': '最大迭代次数不应超过50'}
                return {'valid': True, 'message': '迭代次数有效'}
            except (ValueError, TypeError):
                return {'valid': False, 'message': '必须是有效的整数'}
        
        elif key in ['AGENT_HANDLE_PARSING_ERRORS', 'AGENT_VERBOSE']:
            if isinstance(value, bool):
                return {'valid': True, 'message': '布尔值有效'}
            elif isinstance(value, str) and value.lower() in ['true', 'false']:
                return {'valid': True, 'message': '布尔字符串有效'}
            else:
                return {'valid': False, 'message': '必须是布尔值或 "true"/"false" 字符串'}
        
        else:
            return {'valid': True, 'message': '配置项未定义特殊验证规则'}
    
    except Exception as e:
        return {'valid': False, 'message': f'验证过程中出错: {str(e)}'}
