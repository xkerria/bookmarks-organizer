import pytest
from pathlib import Path
from src.data.analyzer import BookmarkAnalyzer
from src.tests.utils.test_data_generator import TestDataGenerator
import time

class TestAnalyzerPerformance:
    @pytest.mark.performance
    def test_large_file_performance(self, test_data_dir, cleanup_test_files):
        # 生成大量测试数据
        test_file = test_data_dir / "large_bookmarks.html"
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=1000)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 测量分析时间
        start_time = time.time()
        
        analyzer = BookmarkAnalyzer(test_file)
        stats = analyzer.analyze()
        
        duration = time.time() - start_time
        
        # 验证性能
        assert duration < 5.0  # 处理1000个书签应该在5秒内完成
        assert stats["总书签数"] == 1000 