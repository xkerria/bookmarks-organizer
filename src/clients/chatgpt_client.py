from openai import OpenAI
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from src.clients.base_client import BaseAIClient

class ChatGPTClient(BaseAIClient):
    def __init__(self):
        super().__init__("chatgpt")
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def _call_api(self, prompt: str) -> Dict:
        """调用 ChatGPT API"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的书签整理助手，擅长对网页书签进行分类和组织。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000
        )
        return response
    
    def _build_prompt(self, bookmarks: List[Dict]) -> str:
        """构建发送给 ChatGPT 的提示词"""
        bookmark_texts = []
        for bookmark in bookmarks:
            title = bookmark.get('title', '')
            url = bookmark.get('url', '')
            bookmark_texts.append(f"标题: {title}\n网址: {url}")
        
        prompt = '''请将以下书签按类别整理，直接返回JSON格式，不要包含任何其他内容。

书签列表：
{0}

返回格式：
{{
    "技术/文档": [
        {{"title": "原始标题", "url": "原始URL"}}
    ],
    "技术/工具": [
        {{"title": "原始标题", "url": "原始URL"}}
    ]
}}

注意：
1. 保持原始标题和URL不变
2. 使用"/"分隔的路径表示层级，如"技术/文档"
3. 确保URL完整，不要截断
4. 不要包含任何其他内容'''.format("\n".join(bookmark_texts))
        
        return prompt
    
    def _extract_response_data(self, response: Any) -> str:
        """从响应对象中提取有用的数据"""
        try:
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            return str(response)
        except Exception as e:
            print(f"提取响应数据时出错：{str(e)}")
            return "" 