from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import re
from bs4 import BeautifulSoup
from .preprocessor import BookmarkDataPreprocessor

class BookmarkDataCollector:
    def __init__(self):
        self.preprocessor = BookmarkDataPreprocessor()
        self.training_data = []
    
    def collect_from_api_logs(self, logs_dir: Path) -> List[Dict]:
        """从API调用日志中收集训练数据"""
        collected_data = []
        
        print(f"正在从目录收集数据: {logs_dir}")
        # 遍历所有日志文件
        for log_file in logs_dir.glob("**/*.json"):
            try:
                print(f"处理日志文件: {log_file}")
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                
                print(f"日志条目数量: {len(logs)}")
                for log in logs:
                    # 提取请求中的书签数据
                    bookmarks = []
                    if 'request' in log and 'messages' in log['request']:
                        bookmarks = self._extract_bookmarks_from_prompt(
                            log['request']['messages'][0]['content']
                        )
                        print(f"从请求中提取到 {len(bookmarks)} 个书签")
                    
                    # 提取响应中的分类结果
                    if 'response' in log and not log.get('error'):
                        categories = self._extract_categories_from_response(
                            log['response']
                        )
                        print(f"从响应中提取到 {len(categories)} 个分类")
                        
                        # 将书签和分类结果配对
                        for bookmark in bookmarks:
                            category = self._find_category_for_bookmark(
                                bookmark, categories
                            )
                            if category:
                                # 添加特征
                                features = self.preprocessor.extract_features(
                                    bookmark['title'], 
                                    bookmark['url']
                                )
                                collected_data.append({
                                    'input': {
                                        'title': bookmark['title'],
                                        'url': bookmark['url'],
                                        'features': features
                                    },
                                    'label': category
                                })
            
            except Exception as e:
                print(f"处理日志文件 {log_file} 时出错：{str(e)}")
                continue
        
        print(f"总共收集到 {len(collected_data)} 条数据")
        return collected_data
    
    def collect_from_html(self, html_file: Path) -> List[Dict]:
        """从已分类的书签HTML文件中收集训练数据"""
        collected_data = []
        
        try:
            print(f"正在处理HTML文件: {html_file}")
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            def process_folder(element, current_path=""):
                # 获取文件夹名称
                folder_name = element.find_previous('h3')
                if folder_name:
                    current_path = f"{current_path}/{folder_name.text}" if current_path else folder_name.text
                    print(f"处理文件夹: {current_path}")
                
                # 处理当前文件夹中的书签
                links = element.find_all('a')
                print(f"找到 {len(links)} 个书签")
                for link in links:
                    bookmark = {
                        'title': link.text,
                        'url': link.get('href', '')
                    }
                    # 添加特征
                    features = self.preprocessor.extract_features(
                        bookmark['title'], 
                        bookmark['url']
                    )
                    collected_data.append({
                        'input': {
                            'title': bookmark['title'],
                            'url': bookmark['url'],
                            'features': features
                        },
                        'label': current_path
                    })
                
                # 递归处理子文件夹
                for dl in element.find_all('dl'):
                    process_folder(dl, current_path)
            
            # 从根目录开始处理
            root_dl = soup.find('dl')
            if root_dl:
                process_folder(root_dl)
                
        except Exception as e:
            print(f"处理HTML文件 {html_file} 时出错：{str(e)}")
            import traceback
            print(traceback.format_exc())
        
        print(f"总共收集到 {len(collected_data)} 条数据")
        return collected_data
    
    def _extract_bookmarks_from_prompt(self, prompt: str) -> List[Dict]:
        """从提示词中提取书签数据"""
        bookmarks = []
        lines = prompt.split('\n')
        current_title = None
        
        for line in lines:
            if line.startswith('标题:'):
                current_title = line[3:].strip()
            elif line.startswith('网址:') and current_title:
                url = line[3:].strip()
                bookmarks.append({
                    'title': current_title,
                    'url': url
                })
                current_title = None
                
        return bookmarks
    
    def _extract_categories_from_response(self, response: Any) -> Dict[str, str]:
        """从响应中提取分类信息"""
        categories = {}
        try:
            # 处理JSON格式的响应
            if isinstance(response, str):
                data = json.loads(response)
            else:
                data = response
            
            # 如果响应中有 result 字段，提取它
            if isinstance(data, dict) and 'result' in data:
                data = data['result']
            
            # 如果是字典类型，直接使用
            if isinstance(data, dict):
                for category, items in data.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'title' in item:
                                categories[item['title']] = category
            
            # 打印调试信息
            print(f"响应数据类型：{type(data)}")
            print(f"响应内容：{data}")
            print(f"提取的分类信息：{categories}")
                                
        except Exception as e:
            print(f"提取分类信息时出错：{str(e)}")
            print(f"响应数据类型：{type(response)}")
            print(f"响应内容：{response}")
            
        return categories
    
    def _find_category_for_bookmark(self, bookmark: Dict, categories: Dict[str, str]) -> Optional[str]:
        """为书签找到对应的分类"""
        return categories.get(bookmark['title'])
    
    def save_training_data(self, output_file: Path):
        """保存训练数据"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.training_data, f, ensure_ascii=False, indent=2) 