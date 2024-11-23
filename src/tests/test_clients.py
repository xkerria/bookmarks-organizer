import unittest
from unittest.mock import Mock, patch
from src.clients.ernie_client import ErnieClient
from src.clients.chatgpt_client import ChatGPTClient
from src.config import Config

class TestErnieClient(unittest.TestCase):
    def setUp(self):
        self.client = ErnieClient()
        self.test_bookmarks = [
            {"title": "test1", "url": "http://test1.com"},
            {"title": "test2", "url": "http://test2.com"}
        ]
    
    @patch('qianfan.ChatCompletion')
    def test_api_call(self, mock_chat):
        # 模拟API响应
        mock_response = {
            "result": '''{"技术/文档": [
                {"title": "test1", "url": "http://test1.com"}
            ]}'''
        }
        mock_chat.return_value.do.return_value = mock_response
        
        result = self.client.categorize_bookmarks(self.test_bookmarks)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)

    def test_build_prompt(self):
        prompt = self.client._build_prompt(self.test_bookmarks)
        self.assertIn("test1", prompt)
        self.assertIn("http://test1.com", prompt)
        self.assertIn("JSON", prompt)

class TestChatGPTClient(unittest.TestCase):
    def setUp(self):
        self.client = ChatGPTClient()
        self.test_bookmarks = [
            {"title": "test1", "url": "http://test1.com"},
            {"title": "test2", "url": "http://test2.com"}
        ]
    
    @patch('openai.OpenAI')
    def test_api_call(self, mock_openai):
        # 模拟API响应
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='''{"技术/文档": [
                {"title": "test1", "url": "http://test1.com"}
            ]}'''))
        ]
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = self.client.categorize_bookmarks(self.test_bookmarks)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0) 