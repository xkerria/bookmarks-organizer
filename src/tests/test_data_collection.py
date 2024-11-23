import unittest
from pathlib import Path
import json
from src.data.collector import BookmarkDataCollector
from src.data.preprocessor import BookmarkDataPreprocessor

class TestDataCollection(unittest.TestCase):
    def setUp(self):
        self.collector = BookmarkDataCollector()
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试用的API日志
        self.test_log_file = self.test_data_dir / "test_api_log.json"
        self._create_test_log_file()
        
        # 创建测试用的书签HTML文件
        self.test_html_file = self.test_data_dir / "test_bookmarks.html"
        self._create_test_html_file()
    
    def _create_test_log_file(self):
        """创建测试用的API日志文件"""
        test_log = [{
            "request": {
                "messages": [{
                    "role": "user",
                    "content": """标题: doc: FastAPI 中文文档
网址: https://fastapi.tiangolo.com/zh/

标题: pkg: FakerPHP/Faker
网址: https://github.com/FakerPHP/Faker"""
                }]
            },
            "response": {
                "result": {
                    "技术/文档": [
                        {"title": "doc: FastAPI 中文文档", "url": "https://fastapi.tiangolo.com/zh/"}
                    ],
                    "技术/工具": [
                        {"title": "pkg: FakerPHP/Faker", "url": "https://github.com/FakerPHP/Faker"}
                    ]
                }
            }
        }]
        
        with open(self.test_log_file, 'w', encoding='utf-8') as f:
            json.dump(test_log, f, ensure_ascii=False, indent=2)
    
    def _create_test_html_file(self):
        """创建测试用的书签HTML文件"""
        html_content = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>技术文档</H3>
    <DL><p>
        <DT><A HREF="https://fastapi.tiangolo.com/zh/">doc: FastAPI 中文文档</A>
        <DT><A HREF="https://github.com/FakerPHP/Faker">pkg: FakerPHP/Faker</A>
    </DL><p>
</DL><p>"""
        
        with open(self.test_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def test_collect_from_api_logs(self):
        """测试从API日志收集数据"""
        collected_data = self.collector.collect_from_api_logs(self.test_data_dir)
        
        self.assertGreater(len(collected_data), 0)
        for item in collected_data:
            self.assertIn('input', item)
            self.assertIn('label', item)
            self.assertIn('title', item['input'])
            self.assertIn('url', item['input'])
    
    def test_collect_from_html(self):
        """测试从HTML文件收集数据"""
        collected_data = self.collector.collect_from_html(self.test_html_file)
        
        self.assertGreater(len(collected_data), 0)
        for item in collected_data:
            self.assertIn('input', item)
            self.assertIn('label', item)
            self.assertIn('title', item['input'])
            self.assertIn('url', item['input'])
    
    def test_data_preprocessing(self):
        """测试数据预处理"""
        preprocessor = BookmarkDataPreprocessor()
        
        test_bookmark = {
            "title": "doc: FastAPI 中文文档",
            "url": "https://fastapi.tiangolo.com/zh/"
        }
        
        features = preprocessor.extract_features(test_bookmark['title'], test_bookmark['url'])
        
        self.assertEqual(features['prefix'], '文档')
        self.assertIn('domain_type', features)
        self.assertIn('path_segments', features)
        self.assertIn('keywords', features)
    
    def tearDown(self):
        """清理测试文件"""
        if self.test_log_file.exists():
            self.test_log_file.unlink()
        if self.test_html_file.exists():
            self.test_html_file.unlink() 