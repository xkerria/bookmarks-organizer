import unittest
import time
from pathlib import Path
from src.config import Config
from src.utils.performance import monitor_performance, setup_logging
from src.bookmark_processor import BookmarkProcessor
from src.tests.test_data_generator import TestDataGenerator

class TestConfigIntegration(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        setup_logging()
        
        # 生成测试数据
        self.test_bookmarks = TestDataGenerator.generate_test_bookmarks(
            count=self.config.testing.get('bookmarks_count', 5)
        )
    
    @monitor_performance(threshold=0.5)
    def test_config_with_performance(self):
        """测试配置和性能监控的集成"""
        # 1. 验证API配置
        api_settings = self.config.api_settings
        self.assertIn('ernie', api_settings)
        self.assertIn('chatgpt', api_settings)
        
        # 2. 验证性能监控
        time.sleep(0.1)  # 模拟处理时间
        
        # 3. 验证监控配置
        monitoring = self.config.config.get('monitoring', {})
        self.assertIsNotNone(monitoring)
        self.assertIn('enabled', monitoring)
        self.assertIn('log_level', monitoring)
        
        # 4. 测试文件操作性能
        processor = BookmarkProcessor()
        test_file = self.test_data_dir / "perf_test.html"
        TestDataGenerator.generate_test_html(self.test_bookmarks, test_file)
        
        @monitor_performance(threshold=0.1)
        def load_and_process():
            processor.load_bookmarks(str(test_file))
            return processor.get_simplified_bookmarks()
        
        bookmarks = load_and_process()
        self.assertGreater(len(bookmarks), 0)
    
    def test_config_paths(self):
        """测试配置中的路径设置"""
        # 只检查基本目录
        required_dirs = [
            'data/input',
            'data/output',
            'data/logs',
            'tests/data'
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            self.assertTrue(
                path.exists(), 
                f"目录不存在: {dir_path}"
            )
    
    def tearDown(self):
        """清理测试文件"""
        test_file = self.test_data_dir / "perf_test.html"
        if test_file.exists():
            test_file.unlink() 