import pytest
from pathlib import Path
from src.data.converter import BookmarkConverter
from bs4 import BeautifulSoup

class TestBookmarkConverter:
    @pytest.fixture
    def converter(self):
        return BookmarkConverter()
        
    @pytest.fixture
    def sample_bookmarks(self):
        return [
            {
                "title": "doc: Python Documentation",
                "url": "https://docs.python.org/3/",
            },
            {
                "title": "pkg: FastText on GitHub",
                "url": "https://github.com/facebookresearch/fastText",
            },
            {
                "title": "Python 教程",
                "url": "https://www.runoob.com/python/",
            }
        ]
        
    def test_clean_text(self, converter):
        """测试文本清理功能"""
        text = "doc: Python & HTML 编程教程 (示例)"
        cleaned = converter._clean_text(text)
        assert "python" in cleaned.lower()
        assert "&" not in cleaned
        assert "(" not in cleaned
        assert ")" not in cleaned
        
    def test_extract_path_keywords(self, converter):
        """测试路径关键词提取"""
        url = "https://github.com/user/project/docs/api/v1/guide.html"
        keywords = converter._extract_path_keywords(url)
        assert len(keywords) <= 5  # 最多5个关键词
        assert "project" in keywords
        assert "docs" in keywords
        assert "api" in keywords
        
    def test_process_bookmark(self, converter, sample_bookmarks):
        """测试书签处理"""
        bookmark = sample_bookmarks[0]
        labels, features = converter._process_bookmark(bookmark)
        
        # 验证标签
        assert "type_doc" in labels
        assert any(l.startswith("domain_") for l in labels)
        
        # 验证特征
        assert "python" in features.lower()
        assert "documentation" in features.lower()
        assert "domain_docs_python_org" in features
        
    def test_deduplicate_bookmarks(self, converter):
        """测试书签去重"""
        bookmarks = [
            {"url": "http://example.com", "title": "Example 1"},
            {"url": "http://example.com", "title": "Example 2"},
            {"url": "http://other.com", "title": "Other"},
        ]
        
        deduped = converter.deduplicate_bookmarks(bookmarks)
        assert len(deduped) == 2  # 应该只剩两个书签
        
    def test_split_dataset(self, converter):
        """测试数据集分割"""
        data = [f"item_{i}" for i in range(100)]
        train, test = converter.split_dataset(data, test_size=0.2)
        
        assert len(train) == 80
        assert len(test) == 20
        assert len(set(train) & set(test)) == 0  # 确保没有重复