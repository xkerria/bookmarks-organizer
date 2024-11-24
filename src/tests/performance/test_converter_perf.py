import pytest
from pathlib import Path
from src.data.converter import BookmarkConverter
from src.tests.utils.test_data_generator import TestDataGenerator
import time

class TestConverterPerformance:
    @pytest.mark.performance
    def test_large_file_performance(self, test_data_dir, cleanup_test_files):
        # 生成大量测试数据
        test_file = test_data_dir / "large_bookmarks.html"
        output_file = test_data_dir / "large_fasttext.txt"
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=1000)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 测量转换时间
        start_time = time.time()
        
        converter = BookmarkConverter()
        converter.convert_to_fasttext(test_file, output_file)
        
        duration = time.time() - start_time
        
        # 验证性能
        assert duration < 5.0  # 处理1000个书签应该在5秒内完成
        assert output_file.exists() 