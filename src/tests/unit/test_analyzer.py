import pytest
from pathlib import Path
from src.data.analyzer import BookmarkAnalyzer
from src.tests.utils.test_data_generator import TestDataGenerator

class TestBookmarkAnalyzer:
    def test_analyze(self, test_data_dir, cleanup_test_files):
        # 生成测试数据
        test_file = test_data_dir / "test_bookmarks.html"
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=10)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 执行分析
        analyzer = BookmarkAnalyzer(test_file)
        stats = analyzer.analyze()
        
        # 验证结果
        assert stats is not None
        assert stats["总书签数"] == 10
        assert "资源类型分布" in stats
        assert "领域分布" in stats
        
    def test_error_handling(self, test_data_dir):
        # 测试文件不存在的情况
        with pytest.raises(FileNotFoundError):
            analyzer = BookmarkAnalyzer(Path("nonexistent.html"))
            analyzer.analyze() 