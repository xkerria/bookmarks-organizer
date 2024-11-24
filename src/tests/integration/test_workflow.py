import pytest
from pathlib import Path
from src.data.analyzer import BookmarkAnalyzer
from src.data.converter import BookmarkConverter
from src.tests.utils.test_data_generator import TestDataGenerator

class TestWorkflow:
    def test_full_workflow(self, test_data_dir, cleanup_test_files):
        # 1. 准备测试数据
        test_file = test_data_dir / "test_bookmarks.html"
        output_dir = test_data_dir / "fasttext_output"
        analysis_file = test_data_dir / "analysis_output.json"
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=10)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 2. 执行分析
        analyzer = BookmarkAnalyzer(test_file)
        stats = analyzer.analyze()
        assert stats["总书签数"] == 10
        
        # 3. 执行转换
        converter = BookmarkConverter()
        converter.convert_to_fasttext(test_file, output_dir)
        
        # 4. 验证输出文件
        train_file = output_dir / "train.txt"
        test_file = output_dir / "test.txt"
        
        assert train_file.exists()
        assert test_file.exists()
        
        # 5. 验证文件内容
        train_data = train_file.read_text(encoding="utf-8").splitlines()
        test_data = test_file.read_text(encoding="utf-8").splitlines()
        
        assert len(train_data) + len(test_data) == 10  # 总数应该等于输入书签数
        assert all(line.startswith("__label__") for line in train_data)
        assert all(line.startswith("__label__") for line in test_data)