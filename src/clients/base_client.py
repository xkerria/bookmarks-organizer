from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import re
from src.utils.logger import APILogger

class BaseAIClient(ABC):
    def __init__(self, name: str):
        self.logger = APILogger(name)
    
    @abstractmethod
    def _call_api(self, prompt: str) -> Dict:
        """调用具体的 API"""
        pass
    
    def categorize_bookmarks(self, bookmarks: List[Dict]) -> List[Dict]:
        """对书签进行分类和整理"""
        try:
            # 构建提示词
            prompt = self._build_prompt(bookmarks)
            
            # 调用 API
            response = self._call_api(prompt)
            
            # 记录 API 调用
            self.logger.log_api_call(
                request_data={"prompt": prompt},
                response_data=response
            )
            
            # 解析响应
            result = self._extract_response_data(response)
            if not result:
                return bookmarks
                
            # 解析结果
            organized_bookmarks = self._parse_response(result)
            return organized_bookmarks if organized_bookmarks else bookmarks
            
        except Exception as e:
            print(f"API 调用出错：{str(e)}")
            self.logger.log_api_call(
                request_data={"prompt": prompt} if 'prompt' in locals() else {},
                response_data={},
                error=str(e)
            )
            return bookmarks
    
    @abstractmethod
    def _build_prompt(self, bookmarks: List[Dict]) -> str:
        """构建提示词"""
        pass
    
    @abstractmethod
    def _extract_response_data(self, response: Any) -> str:
        """从响应中提取有效数据"""
        pass
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """解析响应文本为书签结构"""
        try:
            # 1. 清理响应文本
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)
            response_text = re.sub(r'根据您提供的信息.*?JSON格式：', '', response_text, flags=re.DOTALL)
            response_text = response_text.strip()
            
            # 2. 提取 JSON 部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print("未找到有效的 JSON 结构")
                return []
            
            json_text = json_match.group()
            
            # 3. 清理 JSON 文本
            json_text = re.sub(r'\s+', ' ', json_text)  # 替换所有空白字符为单个空格
            json_text = re.sub(r',\s*([}\]])', r'\1', json_text)  # 移除尾随逗号
            
            # 4. 解析 JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as je:
                print(f"JSON 解析错误：{str(je)}")
                print(f"错误位置：{je.pos}")
                print(f"问题文本：{json_text[max(0, je.pos-50):min(len(json_text), je.pos+50)]}")
                return []
            
            # 5. 转换为文件夹结构
            result = {'folders': []}
            for category, bookmarks in data.items():
                # 分割分类路径
                path_parts = category.split('/')
                current_level = result['folders']
                
                # 创建或查找每一级文件夹
                for i, part in enumerate(path_parts):
                    folder = next((f for f in current_level if f['name'] == part), None)
                    if not folder:
                        folder = {
                            'name': part,
                            'bookmarks': [] if i == len(path_parts)-1 else [],
                            'subfolders': [] if i < len(path_parts)-1 else []
                        }
                        current_level.append(folder)
                    
                    if i == len(path_parts)-1:
                        folder['bookmarks'].extend(bookmarks)
                    else:
                        current_level = folder['subfolders']
            
            return [result]
                
        except Exception as e:
            print(f"解析响应时出错：{str(e)}")
            print(f"原始响应：{response_text}")
            return [] 