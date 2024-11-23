import qianfan
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from src.clients.base_client import BaseAIClient

class ErnieClient(BaseAIClient):
    def __init__(self):
        super().__init__("ernie")
        load_dotenv()
        self.client = qianfan.ChatCompletion(
            ak=os.getenv("QIANFAN_AK"),
            sk=os.getenv("QIANFAN_SK")
        )
    
    def _call_api(self, prompt: str) -> Dict:
        """调用文心一言 API"""
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "ernie-speed",
            "temperature": 0.1,
            "top_p": 0.95
        }
        
        return self.client.do(**request_data)
    
    def _build_prompt(self, bookmarks: List[Dict]) -> str:
        """构建发送给文心一言的提示词"""
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
            if hasattr(response, 'body'):
                return response.body.get("result", "")
            elif isinstance(response, dict):
                return response.get("result", "")
            return str(response)
        except Exception as e:
            print(f"提取响应数据时出错：{str(e)}")
            return ""
    