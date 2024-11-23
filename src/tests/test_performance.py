import unittest
import time
from src.utils.performance import monitor_performance, setup_logging
from src.config import Config

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        setup_logging()
    
    def test_performance_monitoring(self):
        """测试性能监控装饰器"""
        @monitor_performance(threshold=0.1)
        def slow_function():
            time.sleep(0.2)  # 故意延迟
            return True
        
        @monitor_performance(threshold=1.0)
        def fast_function():
            return True
        
        # 测试超过阈值的情况
        result = slow_function()
        self.assertTrue(result)
        
        # 测试正常情况
        result = fast_function()
        self.assertTrue(result)
    
    def test_disabled_monitoring(self):
        """测试禁用性能监控的情况"""
        # 临时禁用监控
        self.config.config['monitoring']['enabled'] = False
        
        @monitor_performance()
        def test_function():
            time.sleep(0.1)
            return True
        
        result = test_function()
        self.assertTrue(result) 