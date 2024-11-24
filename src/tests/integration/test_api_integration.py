import pytest
from pathlib import Path
from src.clients.ernie_client import ErnieClient
from src.clients.chatgpt_client import ChatGPTClient
from src.data.analyzer import BookmarkAnalyzer
from src.tests.utils.test_data_generator import TestDataGenerator

class TestAPIIntegration:
    @pytest.mark.api  # 标记为 API 测试
    def test_ernie_classification(self, test_data_dir, cleanup_test_files):
        # 准备测试数据
        test_file = test_data_dir / "test_bookmarks.html"
        test_bookmarks = TestDataGenerator.generate_test_bookmarks(count=5)
        TestDataGenerator.generate_test_html(test_bookmarks, test_file)
        
        # 分析书签
        analyzer = BookmarkAnalyzer(test_file)
        stats = analyzer.analyze()
        
        # 使用文心一言分类
        client = ErnieClient()
        result = client.categorize_bookmarks(test_bookmarks)
        
        assert result is not None
        # 验证分类结果的合理性
        
    @pytest.mark.api  # 标记为 API 测试
    def test_chatgpt_classification(self, test_data_dir, cleanup_test_files):
        # 类似的 ChatGPT 测��
        pass 