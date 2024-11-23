import unittest
from pathlib import Path
from src.bookmark_processor import BookmarkProcessor
from src.clients.ernie_client import ErnieClient
from src.clients.chatgpt_client import ChatGPTClient
from src.tests.test_data_generator import TestDataGenerator
from src.config import Config

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.processor = BookmarkProcessor()
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成测试数据
        self.test_bookmarks = TestDataGenerator.generate_test_bookmarks(
            count=self.config.testing.get('bookmarks_count', 5)
        )
        self.test_file = self.test_data_dir / "test_bookmarks.html"
        TestDataGenerator.generate_test_html(self.test_bookmarks, self.test_file)
    
    def test_full_process_ernie(self):
        """测试使用文心一言的完整处理流程"""
        try:
            # 1. 加载书签
            self.processor.load_bookmarks(str(self.test_file))
            bookmarks = self.processor.get_simplified_bookmarks()
            self.assertGreater(len(bookmarks), 0)
            
            # 2. 调用API进行分类（使用模拟数据）
            organized = {
                "folders": [
                    {
                        "name": "测试分类",
                        "bookmarks": [
                            {"title": "Test", "url": "http://test.com"}
                        ],
                        "subfolders": []
                    }
                ]
            }
            
            # 3. 更新和保存
            self.processor.update_bookmarks_data([organized])
            output_file = self.test_data_dir / "test_output.html"
            self.processor.save_bookmarks(str(output_file))
            
            self.assertTrue(output_file.exists())
            
        except Exception as e:
            self.fail(f"集成测试失败：{str(e)}")
    
    def test_full_process_chatgpt(self):
        """测试使用ChatGPT的完整处理流程"""
        # 类似的测试流程，但使用ChatGPT客户端
        pass
    
    def tearDown(self):
        """清理测试文件"""
        if hasattr(self, 'test_file') and self.test_file.exists():
            self.test_file.unlink()
        output_file = self.test_data_dir / "test_output.html"
        if output_file.exists():
            output_file.unlink() 