import unittest
from unittest.mock import Mock, patch
from src.clients.ernie_client import ErnieClient
from src.clients.chatgpt_client import ChatGPTClient
from src.bookmark_processor import BookmarkProcessor
from src.utils.logger import APILogger

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.processor = BookmarkProcessor()
        self.ernie_client = ErnieClient()
        self.chatgpt_client = ChatGPTClient()
    
    def test_invalid_file_handling(self):
        """测试无效文件处理"""
        with self.assertRaises(Exception):
            self.processor.load_bookmarks("non_existent_file.html")
    
    def test_api_error_handling(self):
        """测试API错误处理"""
        with patch('qianfan.ChatCompletion') as mock_chat:
            # 模拟API错误
            mock_chat.return_value.do.side_effect = Exception("API Error")
            
            # 验证错误处理
            bookmarks = [{"title": "test", "url": "http://test.com"}]
            result = self.ernie_client.categorize_bookmarks(bookmarks)
            
            # 应该返回原始书签而不是失败
            self.assertEqual(result, bookmarks)
    
    def test_invalid_json_handling(self):
        """测试无效JSON响应处理"""
        with patch('qianfan.ChatCompletion') as mock_chat:
            # 模拟无效的JSON响应
            mock_chat.return_value.do.return_value = {"result": "Invalid JSON"}
            
            bookmarks = [{"title": "test", "url": "http://test.com"}]
            result = self.ernie_client.categorize_bookmarks(bookmarks)
            
            # 应该返回原始书签
            self.assertEqual(result, bookmarks)
    
    def test_logger_error_handling(self):
        """测试日志记录错误处理"""
        logger = APILogger("test")
        
        # 测试无效数据的日志记录
        circular_ref = {}
        circular_ref['self'] = circular_ref
        
        # 不应该抛出异常
        logger.log_api_call(
            request_data=circular_ref,
            response_data={"test": "data"},
            error="Test error"
        ) 