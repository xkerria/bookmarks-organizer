import pytest
from unittest.mock import Mock, patch
from src.clients.ernie_client import ErnieClient
from src.clients.chatgpt_client import ChatGPTClient

class TestErnieClient:
    def test_api_call(self):
        with patch('qianfan.ChatCompletion') as mock_chat:
            # 模拟API响应
            mock_response = {
                "result": '''{"技术/文档": [
                    {"title": "test1", "url": "http://test1.com"}
                ]}'''
            }
            mock_chat.return_value.do.return_value = mock_response
            
            client = ErnieClient()
            result = client.categorize_bookmarks([
                {"title": "test1", "url": "http://test1.com"}
            ])
            
            assert result is not None
            assert len(result) > 0

class TestChatGPTClient:
    def test_api_call(self):
        with patch('openai.OpenAI') as mock_openai:
            # 模拟API响应
            mock_response = Mock()
            mock_response.choices = [
                Mock(message=Mock(content='''{"技术/文档": [
                    {"title": "test1", "url": "http://test1.com"}
                ]}'''))
            ]
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            
            client = ChatGPTClient()
            result = client.categorize_bookmarks([
                {"title": "test1", "url": "http://test1.com"}
            ])
            
            assert result is not None
            assert len(result) > 0 