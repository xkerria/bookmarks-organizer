# src/tests/test_data_processor.py
import unittest
from pathlib import Path
from src.data.processor import BookmarkDataProcessor

class TestBookmarkDataProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = BookmarkDataProcessor()
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试用的书签文件
        self.test_bookmarks = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
        <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
        <TITLE>Bookmarks</TITLE>
        <H1>Bookmarks</H1>
        <DL><p>
            <DT><H3>技术文档</H3>
            <DL><p>
                <DT><A HREF="https://docs.python.org">doc: Python 文档</A>
                <DT><A HREF="https://fastapi.tiangolo.com">doc: FastAPI 文档</A>
            </DL><p>
            <DT><H3>开发工具</H3>
            <DL><p>
                <DT><A HREF="https://github.com/python/cpython">pkg: CPython</A>
            </DL><p>
        </DL><p>"""
        
        self.test_file = self.test_data_dir / "test_bookmarks.html"
        self.test_file.write_text(self.test_bookmarks, encoding='utf-8')
    
    def test_process_bookmarks_file(self):
        """测试书签文件处理"""
        data = self.processor.process_bookmarks_file(self.test_file)
        self.assertIsNotNone(data)
        self.assertTrue(len(data) > 0)
        
        # 验证数据结构
        for item in data:
            self.assertIn('text', item)  # FastText 输入文本
            self.assertIn('label', item)  # FastText 标签
            self.assertIn('features', item)  # 原始特征
    
    def test_extract_features(self):
        """测试特征提取"""
        bookmark = {
            'title': 'doc: Python 文档',
            'url': 'https://docs.python.org',
            'folder': '技术文档'
        }
        
        features = self.processor.extract_features(bookmark)
        
        # 验证新的特征结构
        self.assertIn('prefixes', features)  # 前缀列表
        self.assertIn('has_prefix', features)  # 是否有前缀
        self.assertIn('clean_title', features)  # 清理后的标题
        self.assertIn('domain', features)  # 域名
        self.assertIn('folder', features)  # 文件夹
        self.assertIn('keywords', features)  # 关键词
        
        # 验证前缀处理
        self.assertTrue(features['has_prefix'])
        self.assertEqual(features['prefixes'], ['文档'])
        self.assertEqual(features['clean_title'], 'Python 文档')
        
        # 验证其他特征
        self.assertEqual(features['domain'], 'docs.python.org')
        self.assertEqual(features['folder'], '技术文档')
    
    def test_extract_multiple_prefixes(self):
        """测试多前缀提取"""
        bookmark = {
            'title': 'res:pkg: FastText 库',
            'url': 'https://example.com',
            'folder': '开发工具'
        }
        
        features = self.processor.extract_features(bookmark)
        
        # 验证多前缀处理
        self.assertTrue(features['has_prefix'])
        self.assertEqual(set(features['prefixes']), {'资源', '库'})
        self.assertEqual(features['clean_title'], 'FastText 库')
    
    def tearDown(self):
        """清理测试文件"""
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)