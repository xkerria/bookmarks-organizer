import pytest
from pathlib import Path
from src.data.converter import BookmarkConverter
from src.tests.utils.test_data_generator import TestDataGenerator

class TestBookmarkConverter:
    def test_conversion(self, test_data_dir, cleanup_test_files):
        # 准备测试文件
        test_file = test_data_dir / "test_bookmarks.html"
        output_file = test_data_dir / "test_fasttext.txt"
        
        # 生成测试数据
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=10)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 执行转换
        converter = BookmarkConverter()
        converter.convert_to_fasttext(test_file, output_file)
        
        # 验证结果
        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) > 0 