from bs4 import BeautifulSoup
from typing import List, Dict
from pathlib import Path
import re
from urllib.parse import urlparse

class BookmarkDataProcessor:
    def __init__(self):
        # 扩展特征提取规则
        self.prefix_patterns = {
            'doc:': '文档',
            'pkg:': '库',
            'tip:': '提示',
            'entry:': '入口',
            'site:': '站点',
            'home:': '主页',
            'api:': '接口',
            'res:': '资源',
            'tool:': '工具',
            'lib:': '库',
            'sdk:': 'SDK',
            'app:': '应用',
            'demo:': '示例',
            'ref:': '参考',
            'guide:': '指南',
            'blog:': '博客',
            'forum:': '论坛',
            'course:': '课程',
            'book:': '书籍',
            'video:': '视频',
            'news:': '新闻',
            'oss:': '对象存储',
            'cloud:': '云服务'
        }
    
    def process_bookmarks_file(self, file_path: Path) -> List[Dict]:
        """处理书签文件,返回训练数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        training_data = []
        
        def process_folder(element, current_folder=""):
            # 获取文件夹名称
            folder_name = element.find_previous_sibling('h3')
            if folder_name:
                current_folder = folder_name.text.strip()
            
            # 处理当前文件夹中的书签
            for link in element.find_all('a'):
                bookmark = {
                    'title': link.text.strip(),
                    'url': link.get('href', ''),
                    'folder': current_folder
                }
                
                # 提取特征
                features = self.extract_features(bookmark)
                
                # 生成训练数据
                text = self._generate_training_text(bookmark, features)
                label = self._generate_label(current_folder)
                
                if current_folder:
                    training_data.append({
                        'text': text,
                        'label': label,
                        'features': features
                    })
            
            # 递归处理子文件夹
            for dl in element.find_all('dl'):
                process_folder(dl, current_folder)
        
        # 从根目录开始处理
        root_dl = soup.find('dl')
        if root_dl:
            process_folder(root_dl)
        
        return training_data
    
    def extract_features(self, bookmark: Dict) -> Dict:
        """提取特征"""
        features = {
            'prefixes': [],        # 存储所有前缀
            'has_prefix': False,   # 是否有前缀标记
            'clean_title': '',     # 清理前缀后的标题
            'domain': '',          # 域名
            'folder': bookmark['folder'],  # 所在文件夹
            'keywords': []         # 关键词
        }
        
        # 处理标题和前缀
        title = bookmark['title']
        prefixes = self._extract_prefixes(title)
        if prefixes:
            features['has_prefix'] = True
            features['prefixes'] = prefixes
            features['clean_title'] = self._remove_prefixes(title)
        else:
            features['clean_title'] = title
        
        # 提取域名
        url = bookmark['url']
        if url:
            domain = urlparse(url).netloc
            features['domain'] = domain
        
        # 提取关键词
        features['keywords'] = self._extract_keywords(features['clean_title'])
        
        return features
    
    def _extract_prefixes(self, title: str) -> List[str]:
        """提取所有有效的前缀"""
        prefixes = []
        parts = title.split(':')
        
        # 处理每个可能的前缀
        current = ''
        for part in parts[:-1]:  # 最后一部分不是前缀
            # 如果当前部分已经是一个完整的前缀
            if part + ':' in self.prefix_patterns:
                if current:  # 如果有累积的前缀，先添加它
                    if current + ':' in self.prefix_patterns:
                        prefixes.append(self.prefix_patterns[current + ':'])
                    else:
                        prefixes.append(current.lower())
                # 添加当前前缀
                prefixes.append(self.prefix_patterns[part + ':'])
                current = ''
            else:
                if current:
                    current = current + ':' + part
                else:
                    current = part
        
        # 处理最后累积的前缀
        if current and current + ':' in self.prefix_patterns:
            prefixes.append(self.prefix_patterns[current + ':'])
        elif current:
            prefixes.append(current.lower())
        
        return prefixes
    
    def _remove_prefixes(self, title: str) -> str:
        """移除所有前缀"""
        parts = title.split(':')
        if len(parts) > 1:
            return parts[-1].strip()
        return title
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从清理后的标题中提取关键词"""
        # 简单的分词（可以后续改进）
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if len(w) > 1]  # 过滤掉单字符
    
    def _generate_training_text(self, bookmark: Dict, features: Dict) -> str:
        """生成训练文本"""
        text_parts = []
        
        # 添加清理后的标题
        if features.get('clean_title'):
            text_parts.append(features['clean_title'])
        
        # 添加域名
        if features.get('domain'):
            text_parts.append(f"domain={features['domain']}")
        
        # 添加文件夹
        if features.get('folder'):
            text_parts.append(f"folder={features['folder']}")
        
        # 添加前缀信息
        if features.get('has_prefix') and features.get('prefixes'):
            for prefix in features['prefixes']:
                text_parts.append(f"prefix={prefix}")
        
        # 添加关键词
        if features.get('keywords'):
            for keyword in features['keywords']:
                text_parts.append(f"keyword={keyword}")
        
        return ' '.join(text_parts)
    
    def _generate_label(self, folder: str) -> str:
        """生成标签"""
        # 清理和标准化文件夹名称
        label = re.sub(r'[^\w\s-]', '', folder)
        label = label.strip().replace(' ', '_').lower()
        return f"__label__{label}"
    
    def analyze_prefixes(self, file_path: Path) -> Dict:
        """分析书签中的前缀使用情况"""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        prefix_stats = {}  # 存储前缀统计信息
        
        # 遍历所有书签
        for link in soup.find_all('a'):
            title = link.text.strip()
            parts = title.split(':')
            
            # 收集所有以冒号结尾的前缀
            current = ''
            for part in parts[:-1]:
                if current:
                    current = current + ':' + part
                else:
                    current = part
                prefix = current + ':'
                prefix_stats[prefix] = prefix_stats.get(prefix, 0) + 1
        
        return prefix_stats