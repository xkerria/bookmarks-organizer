import pytest
from pathlib import Path
from src.data.analyzer import BookmarkAnalyzer
from src.data.converter import BookmarkConverter
from src.tests.utils.test_data_generator import TestDataGenerator

class TestWorkflow:
    def test_full_workflow(self, test_data_dir, cleanup_test_files):
        # 1. 准备测试数据
        test_file = test_data_dir / "test_bookmarks.html"
        fasttext_file = test_data_dir / "fasttext_output.txt"
        analysis_file = test_data_dir / "analysis_output.json"
        
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=10)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 2. 执行分析
        analyzer = BookmarkAnalyzer(test_file)
        stats = analyzer.analyze()
        assert stats["总书签数"] == 10
        
        # 3. 执行转换
        converter = BookmarkConverter()
        converter.convert_to_fasttext(test_file, fasttext_file)
        assert fasttext_file.exists() 