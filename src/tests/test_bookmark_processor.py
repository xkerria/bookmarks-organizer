import unittest
from pathlib import Path
from src.bookmark_processor import BookmarkProcessor
from src.config import Config

class TestBookmarkProcessor(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.processor = BookmarkProcessor()
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.test_data_path = self.test_data_dir / "bookmarks_test.html"
        
        # 创建测试数据
        test_data = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://test.com">Test Bookmark</A>
</DL><p>"""
        self.test_data_path.write_text(test_data)
    
    def test_load_bookmarks(self):
        """测试加载书签文件"""
        self.processor.load_bookmarks(str(self.test_data_path))
        bookmarks = self.processor.get_bookmarks_data()
        self.assertIsNotNone(bookmarks)
        self.assertGreater(len(bookmarks), 0)
    
    def test_simplified_bookmarks(self):
        """测试简化书签数据"""
        self.processor.load_bookmarks(str(self.test_data_path))
        simplified = self.processor.get_simplified_bookmarks()
        self.assertIsNotNone(simplified)
        for bookmark in simplified:
            self.assertIn('title', bookmark)
            self.assertIn('url', bookmark)
    
    def test_folder_structure(self):
        """测试文件夹结构处理"""
        test_data = {
            'folders': [{
                'name': 'Test Folder',
                'bookmarks': [
                    {'title': 'Test', 'url': 'http://test.com'}
                ],
                'subfolders': []
            }]
        }
        self.processor.update_bookmarks_data([test_data])
        html = self.processor._generate_bookmarks_html()
        self.assertIn('Test Folder', html)
        self.assertIn('http://test.com', html) 