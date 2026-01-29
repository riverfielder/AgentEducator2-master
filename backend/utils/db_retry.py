import time
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError, InternalError, StatementError

logger = logging.getLogger(__name__)

def db_retry(max_retries=3, delay=1.0, backoff=2.0):
    """数据库操作重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # 在每次重试前确保数据库连接是干净的
                    if attempt > 0:
                        try:
                            from models.models import db
                            db.session.rollback()
                            db.session.close()
                        except Exception as cleanup_error:
                            logger.warning(f"数据库连接清理失败: {cleanup_error}")
                    
                    # 执行函数
                    result = func(*args, **kwargs)
                    
                    # 如果成功，提交事务
                    try:
                        from models.models import db
                        db.session.commit()
                    except Exception as commit_error:
                        logger.warning(f"事务提交失败: {commit_error}")
                        from models.models import db
                        db.session.rollback()
                        raise commit_error
                    
                    return result
                    
                except (OperationalError, InternalError, StatementError) as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    logger.warning(f"数据库操作失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                    
                    # 强制回滚事务
                    try:
                        from models.models import db
                        db.session.rollback()
                    except Exception:
                        pass
                    
                    # 如果是最后一次尝试，不再等待
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.info(f"等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)
                    
                except Exception as e:
                    # 其他异常直接抛出，不重试
                    logger.error(f"非数据库异常，不重试: {e}")
                    try:
                        from models.models import db
                        db.session.rollback()
                    except Exception:
                        pass
                    raise e
            
            # 所有重试都失败了
            logger.error(f"数据库操作失败，已重试 {max_retries} 次: {last_exception}")
            raise last_exception
            
        return wrapper
    return decorator

def safe_db_query(query_func, *args, **kwargs):
    """安全的数据库查询包装器"""
    try:
        return query_func(*args, **kwargs)
    except (OperationalError, InternalError, StatementError) as e:
        logger.error(f"数据库查询失败: {e}")
        try:
            from models.models import db
            db.session.rollback()
        except Exception:
            pass
        raise e
    except Exception as e:
        logger.error(f"查询执行异常: {e}")
        try:
            from models.models import db
            db.session.rollback()
        except Exception:
            pass
        raise e

def ensure_connection():
    """确保数据库连接可用"""
    try:
        from models.models import db
        # 执行一个简单的查询来测试连接
        db.session.execute("SELECT 1")
        db.session.commit()
        return True
    except Exception as e:
        logger.warning(f"数据库连接测试失败: {e}")
        try:
            from models.models import db
            db.session.rollback()
            db.session.close()
        except Exception:
            pass
        return False 