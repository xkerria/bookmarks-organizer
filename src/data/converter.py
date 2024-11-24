from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json
from typing import List, Dict, Set, Tuple
import html
from src.config import config
import random
from tqdm import tqdm

class BookmarkConverter:
    def __init__(self):
        self.config = config.config["converter"]
        self.domains = self.config["domains"]
        self.content_types = self.config["content_types"]
        self.feature_config = self.config["feature_extraction"]
        self.output_format = self.config["output_format"]

    def convert_to_fasttext(self, input_file: Path, output_dir: Path, test_size: float = 0.2):
        """将书签文件转换为 FastText 训练格式"""
        if not input_file.exists():
            raise FileNotFoundError(f"输入文件不存在：{input_file}")
            
        try:
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            bookmarks = self._load_bookmarks(input_file)
            print(f"加载书签数：{len(bookmarks)}")
            
            if not bookmarks:
                raise ValueError("未找到任何书签数据")
                
            # 去重处理
            bookmarks = self.deduplicate_bookmarks(bookmarks)
            print(f"去重后书签数：{len(bookmarks)}")
            
            training_data = []
            skipped = 0
            no_labels = 0
            
            with tqdm(total=len(bookmarks), desc="处理书签") as pbar:
                for bookmark in bookmarks:
                    try:
                        labels, features = self._process_bookmark(bookmark)
                        
                        # 确保至少有一个标签
                        if not labels:
                            no_labels += 1
                            # 添加默认标签
                            labels.add("type_other")
                            labels.add("domain_other")
                            labels.add("content_other")
                        
                        if features:
                            label_str = " ".join([f"{self.output_format['label_prefix']}_{label}" for label in labels])
                            training_data.append(f"{label_str} {features}")
                        else:
                            skipped += 1
                            print(f"警告：跳过无特征的书签：{bookmark.get('title', '未知')}")
                        
                        pbar.update(1)
                    except Exception as e:
                        skipped += 1
                        print(f"警告：处理书签时出错，已跳过：{bookmark.get('title', '未知')} - {str(e)}")
                        continue

            if not training_data:
                raise ValueError("没有生成任何有效的训练数据")

            # 分割数据集
            train_data, test_data = self.split_dataset(training_data, test_size)
            
            # 保存训练集
            train_file = output_dir / "train.txt"
            with open(train_file, "w", encoding="utf-8") as f:
                f.write("\n".join(train_data))
                
            # 保存测试集
            test_file = output_dir / "test.txt"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("\n".join(test_data))
                
            print(f"\n数据集分割:")
            print(f"训练集样本数：{len(train_data)}")
            print(f"测试集样本数：{len(test_data)}")
            
        except Exception as e:
            raise RuntimeError(f"转换过程中出错：{str(e)}")

    def _load_bookmarks(self, file_path: Path) -> List[Dict]:
        """加载书签文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        
        bookmarks = []
        for link in soup.find_all("a"):
            bookmarks.append({
                "title": link.text.strip(),
                "url": link.get("href", ""),
                "add_date": link.get("add_date", ""),
                "last_modified": link.get("last_modified", "")
            })
        return bookmarks

    def _process_bookmark(self, bookmark: Dict) -> Tuple[Set[str], str]:
        """处理单个书签，返回标签集合和特征文本"""
        title = bookmark["title"]
        url = bookmark["url"]
        
        # 清理和标准化文本
        clean_title = self._clean_text(title)
        domain = urlparse(url).netloc
        
        # 收集标签
        labels = set()
        
        # 1. 处理前缀标签
        prefix_label = self._extract_prefix_label(title)
        if prefix_label:
            labels.add(prefix_label)
        
        # 2. 领域标签
        domain_label = self._get_domain_label(clean_title, url)
        if domain_label:
            labels.add(domain_label)
        
        # 3. 内容形式标签
        content_label = self._get_content_type_label(clean_title, url)
        if content_label:
            labels.add(content_label)
        
        # 构建特征文本
        features = []
        
        # 1. 清理后的标题
        features.append(clean_title)
        
        # 2. 域名特征
        features.append(f"domain_{domain.replace('.', '_')}")
        
        # 3. URL 路径关键词
        path_keywords = self._extract_path_keywords(url)
        features.extend(path_keywords)
        
        return labels, " ".join(features)

    def _clean_text(self, text: str) -> str:
        """清理和标准化文本"""
        # 移除 HTML 实体
        text = html.unescape(text)
        
        # 移除前缀标记
        text = re.sub(r'^(doc|pkg|api|ref|tool|res|blog):\s*', '', text.lower())
        
        # 移除特殊字符，但保留中文
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除常见无意义词
        stop_words = {'的', '了', '和', '与', '或', '及', '等', 'the', 'a', 'an', 'and', 'or'}
        words = text.split()
        words = [w for w in words if w not in stop_words]
        
        return ' '.join(words).strip()

    def _extract_prefix_label(self, title: str) -> str:
        """提取前缀标签"""
        match = re.match(r'^(doc|pkg|api|ref|tool|res|blog):', title.lower())
        if match:
            prefix = match.group(1)
            return f"type_{prefix}"
        return ""

    def _get_domain_label(self, title: str, url: str) -> str:
        """获取领域签"""
        text = f"{title} {url}".lower()
        for domain_name, domain_info in self.domains.items():
            if (any(kw in text for kw in domain_info["keywords"]) or
                any(d in url for d in domain_info["domains"])):
                return f"domain_{domain_name}"
        return ""

    def _get_content_type_label(self, title: str, url: str) -> str:
        """获取内容形式标签"""
        text = f"{title} {url}".lower()
        for type_name, keywords in self.content_types.items():
            if any(kw in text for kw in keywords):
                return f"content_{type_name}"
        return ""

    def _extract_path_keywords(self, url: str) -> List[str]:
        """从 URL 路径中提取关键词"""
        path = urlparse(url).path
        keywords = []
        
        # 分割路径
        parts = [p for p in path.split('/') if p]
        
        for part in parts:
            # 移除文件扩展名
            part = re.sub(r'\.[a-z]+$', '', part.lower())
            
            # 分割驼峰命名
            part = re.sub(r'([a-z])([A-Z])', r'\1 \2', part).lower()
            
            # 分割数字和字母
            part = re.sub(r'(\d+)([a-z])', r'\1 \2', part)
            part = re.sub(r'([a-z])(\d+)', r'\1 \2', part)
            
            # 移除特殊字符
            clean_parts = re.split(r'[-_]', part)
            
            for clean_part in clean_parts:
                if clean_part and len(clean_part) > 1:  # 忽略单字符
                    keywords.append(f"path_{clean_part}")
                
        return keywords[:5]  # 限制关键词数量

    def deduplicate_bookmarks(self, bookmarks: List[Dict]) -> List[Dict]:
        """去重并统一标签"""
        # 用 URL 作为唯一键
        url_map = {}
        duplicates = 0
        unified = 0
        
        for bookmark in bookmarks:
            url = bookmark.get("url")
            if not url:
                continue
            
            if url in url_map:
                duplicates += 1
                # 如果已存在的没有标签，但新的有标签，则更新
                existing_labels = self._process_bookmark(url_map[url])[0]
                new_labels = self._process_bookmark(bookmark)[0]
                
                if not existing_labels and new_labels:
                    url_map[url] = bookmark
                    unified += 1
            else:
                url_map[url] = bookmark
                
        print(f"\n去重统计:")
        print(f"重复书签数：{duplicates}")
        print(f"标签统一数：{unified}")
        
        return list(url_map.values())

    def split_dataset(self, training_data: List[str], test_size: float = 0.2, random_seed: int = 42) -> Tuple[List[str], List[str]]:
        """将数据集分割为训练集和测试集"""
        random.seed(random_seed)
        random.shuffle(training_data)
        
        split_point = int(len(training_data) * (1 - test_size))
        train_set = training_data[:split_point]
        test_set = training_data[split_point:]
        
        return train_set, test_set


def main():
    # 设置输入输出路径
    input_file = Path("data/input/bookmarks.html")
    output_dir = Path("data/training")
    
    # 转换数据
    converter = BookmarkConverter()
    converter.convert_to_fasttext(input_file, output_dir)


if __name__ == "__main__":
    main() 