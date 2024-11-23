from typing import List, Dict, Tuple
from pathlib import Path
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class BookmarkDataPreprocessor:
    def __init__(self):
        self.prefix_patterns = {
            r'^doc:': '文档',
            r'^pkg:': '工具',
            r'^tip:': '教程',
            r'^res:': '资源',
            r'^entry:': '入口',
            r'^site:': '站点'
        }
        
        self.domain_patterns = {
            r'github.com': '开源项目',
            r'docs?\.(.*?)\.': '文档',
            r'help\.(.*?)\.': '帮助文档'
        }
    
    def extract_features(self, title: str, url: str) -> Dict:
        """提取特征"""
        features = {
            'prefix': self._extract_prefix(title),
            'domain_type': self._extract_domain_type(url),
            'path_segments': self._extract_path_segments(url),
            'keywords': self._extract_keywords(title)
        }
        return features
    
    def _extract_prefix(self, title: str) -> str:
        """提取标题前缀"""
        for pattern, category in self.prefix_patterns.items():
            if re.match(pattern, title, re.I):
                return category
        return 'unknown'
    
    def _extract_domain_type(self, url: str) -> str:
        """提取域名类型"""
        domain = urlparse(url).netloc
        for pattern, category in self.domain_patterns.items():
            if re.search(pattern, domain, re.I):
                return category
        return 'unknown'
    
    def _extract_path_segments(self, url: str) -> List[str]:
        """提取URL路径段"""
        path = urlparse(url).path
        return [seg for seg in path.split('/') if seg]
    
    def _extract_keywords(self, title: str) -> List[str]:
        """提取关键词"""
        # 移除前缀
        for pattern in self.prefix_patterns:
            title = re.sub(pattern, '', title, flags=re.I)
        
        # 分词（简单实现，后续可以改进）
        words = re.findall(r'\w+', title.lower())
        return words
    
    def process_bookmark(self, bookmark: Dict) -> Dict:
        """处理单个书签"""
        title = bookmark['title']
        url = bookmark['url']
        
        features = self.extract_features(title, url)
        return {
            'input': {
                'title': title,
                'url': url,
                'features': features
            },
            'label': None  # 需要从已分类数据中获取
        } 