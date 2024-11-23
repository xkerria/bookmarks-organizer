import time
import logging
from functools import wraps
from typing import Callable
from src.config import Config

config = Config()

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/performance.log'),
            logging.StreamHandler()
        ]
    )

def monitor_performance(threshold: float = None):
    """性能监控装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not config.monitoring.get('enabled', False):
                return func(*args, **kwargs)
            
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 获取配置的阈值
            perf_threshold = threshold or config.monitoring.get('performance_threshold', 5.0)
            
            # 记录性能日志
            logger = logging.getLogger('performance')
            logger.info(f"{func.__name__} took {duration:.2f} seconds")
            
            # 如果执行时间超过阈值，记录警告
            if duration > perf_threshold:
                logger.warning(
                    f"Performance warning: {func.__name__} took {duration:.2f} seconds "
                    f"(threshold: {perf_threshold}s)"
                )
            
            return result
        return wrapper
    return decorator 