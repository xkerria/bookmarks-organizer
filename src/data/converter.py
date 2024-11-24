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
from collections import defaultdict
import logging

# 配置日志
logger = logging.getLogger(__name__)

class BookmarkConverter:
    def __init__(self):
        self.config = config.config["converter"]
        self.domains = self.config["domains"]
        self.content_types = self.config["content_types"]
        self.feature_config = self.config["feature_extraction"]
        self.output_format = self.config["output_format"]

    def convert_to_fasttext(self, input_file: Path, output_dir: Path):
        """转换书签为FastText训练数据"""
        try:
            # 加载书签
            bookmarks = self._load_bookmarks(input_file)
            logger.info(f"加载了 {len(bookmarks)} 个书签")
            
            # 去重
            bookmarks = self.deduplicate_bookmarks(bookmarks)
            logger.info(f"去重后剩余 {len(bookmarks)} 个书签")
            
            # 处理书签
            training_data = []
            for bookmark in tqdm(bookmarks, desc="处理书签"):
                try:
                    labels, text = self._process_bookmark(bookmark)
                    if labels and text:
                        # 格式化训练数据
                        label_str = " ".join(f"__label__{label}" for label in labels)
                        training_data.append(f"{label_str} {text}")
                except Exception as e:
                    logger.warning(f"处理书签时出错，已跳过：{bookmark.get('title', '')} - {str(e)}")
                    
            if not training_data:
                raise ValueError("没有生成任何有效的训练数据")
                
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 分割数据集
            train_data, test_data = self.split_dataset(training_data)
            
            # 保存数据集
            train_file = output_dir / "train.txt"
            test_file = output_dir / "test.txt"
            
            with open(train_file, "w", encoding="utf-8") as f:
                f.write("\n".join(train_data))
                
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("\n".join(test_data))
                
            logger.info(f"已生成训练集 ({len(train_data)} 条) 和测试集 ({len(test_data)} 条)")
            logger.info(f"数据已保存到: {output_dir}")
            
        except Exception as e:
            error_msg = f"转换过程中出错：{str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def split_dataset(self, data: List[str], test_size: float = 0.2) -> Tuple[List[str], List[str]]:
        """分割数据集为训练集和测试集"""
        random.shuffle(data)
        split_idx = int(len(data) * (1 - test_size))
        return data[:split_idx], data[split_idx:]

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

    def _process_bookmark(self, bookmark: Dict) -> Tuple[List[str], str]:
        """处理单个书签"""
        labels = []
        features = []
        
        # 1. 处理标题和URL
        title = bookmark.get("title", "").strip()
        url = bookmark.get("url", "").strip()
        
        # 2. 提取URL特征
        if url:
            domain = urlparse(url).netloc
            path = urlparse(url).path
            features.extend(self._extract_url_features(domain, path))
        
        # 3. 提取标题特征
        if title:
            # 处理标签前缀
            prefix_labels = self._extract_prefix_labels(title)
            if prefix_labels:
                labels.extend(prefix_labels)
                # 移除标题中的标签前缀
                title = self._remove_prefixes(title)
            
            # 提取标题特征
            features.extend(self._extract_title_features(title))
        
        # 4. 领域分类
        domain_labels = self._classify_domain(title, url)
        labels.extend(domain_labels)
        
        # 5. 内容类型分类
        content_labels = self._classify_content_type(title, url)
        labels.extend(content_labels)
        
        # 6. 确保标签唯一性
        labels = list(set(labels))
        
        # 7. 组合特征
        text = " ".join(features)
        
        return labels, text

    def _extract_url_features(self, domain: str, path: str) -> List[str]:
        """提取URL特征"""
        features = []
        
        # 域名特征 (修改格式)
        features.append(f"domain_{domain.replace('.', '_')}")
        
        # 子域名特征
        parts = domain.split(".")
        if len(parts) > 2:
            features.append(f"subdomain_{parts[0]}")
        
        # 路径特征
        path_parts = [p for p in path.split("/") if p]
        for i, part in enumerate(path_parts[:self.config["path_processing"]["max_segments"]]):
            if len(part) >= self.config["path_processing"]["min_segment_length"]:
                features.append(f"path_{part}")
        
        return features

    def _extract_title_features(self, title: str) -> List[str]:
        """提取标题特征"""
        features = []
        
        # 分词
        words = title.split()
        
        # 过滤短词
        words = [w for w in words if len(w) >= self.config["text_cleaning"]["min_word_length"]]
        
        # 添加词特征
        features.extend(words)
        
        # 添加词组特征
        if len(words) >= 2:
            for i in range(len(words)-1):
                features.append(f"{words[i]}_{words[i+1]}")
        
        return features

    def _extract_prefix_labels(self, title: str) -> List[str]:
        """提取标题中的前缀标签"""
        labels = []
        
        # 1. 处理连续前缀标签
        prefix_pattern = r'^((?:(?:doc|tip|res|entry|pkg|api|ref|tool|blog):)+)'
        prefix_match = re.match(prefix_pattern, title.lower())
        
        if prefix_match:
            # 获取所有前缀
            prefix_str = prefix_match.group(1)
            # 分割多个前缀
            prefixes = [p.rstrip(':') for p in prefix_str.split(':') if p]
            # 为每个前缀生成标签
            for prefix in prefixes:
                labels.append(f"type_{prefix}")
        
        # 2. 处理领域标签
        for domain, config in self.domains.items():
            if any(kw in title.lower() for kw in config["keywords"]):
                labels.append(f"domain_{domain}")
        
        # 3. 处理内容类型标签
        for content_type, keywords in self.content_types.items():
            if any(kw in title.lower() for kw in keywords):
                labels.append(f"content_{content_type}")
        
        return labels

    def _remove_prefixes(self, title: str) -> str:
        """移除标题中的标签前缀"""
        prefix_pattern = r'^((?:(?:doc|tip|res|entry|pkg|api|ref|tool|blog):)+)'
        return re.sub(prefix_pattern, '', title).strip()

    def _classify_domain(self, title: str, url: str) -> List[str]:
        """根据标题和URL分类领域"""
        domains = []
        
        # 1. 检查URL域名
        domain = urlparse(url).netloc
        for domain_name, config in self.domains.items():
            if any(d in domain for d in config["domains"]):
                domains.append(f"domain_{domain_name}")
                break
                
        # 2. 检查标题关键词
        if not domains:  # 如果通过域名没有找到匹配
            for domain_name, config in self.domains.items():
                if any(kw in title.lower() for kw in config["keywords"]):
                    domains.append(f"domain_{domain_name}")
                    break
                    
        # 3. 如果没有匹配到任何领域，添加其他类别
        if not domains:
            domains.append("domain_other")
            
        return domains

    def _classify_content_type(self, title: str, url: str) -> List[str]:
        """根据标题和URL分类内容类型"""
        content_types = []
        
        # 检查标题中的内容类型关键词
        for content_type, keywords in self.content_types.items():
            if any(kw in title.lower() for kw in keywords):
                content_types.append(f"content_{content_type}")
                
        # 如果没有匹配到任何内容类型，添加其他类别
        if not content_types:
            content_types.append("content_other")
            
        return content_types

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

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if self.config["text_cleaning"]["remove_html_tags"]:
            text = re.sub(r'<[^>]+>', '', text)
        
        if self.config["text_cleaning"]["remove_punctuation"]:
            text = re.sub(r'[^\w\s]', ' ', text)
        
        if self.config["text_cleaning"]["lowercase"]:
            text = text.lower()
        
        # 处理多余空格
        text = ' '.join(text.split())
        
        # 截断长文本
        max_length = self.config["text_cleaning"]["max_text_length"]
        if len(text) > max_length:
            text = text[:max_length]
        
        return text

    def _extract_path_keywords(self, url: str) -> List[str]:
        """提取URL路径关键词"""
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]
        
        # 过滤配置中定义的忽略扩展名和片段
        ignore_exts = self.config["path_processing"]["ignore_extensions"]
        ignore_segs = self.config["path_processing"]["ignore_segments"]
        
        keywords = []
        for segment in segments:
            # 移除扩展名
            segment = segment.split('.')[0]
            
            # 跳过忽略的片段
            if segment in ignore_segs:
                continue
            
            # 检查最小长度
            if len(segment) >= self.config["path_processing"]["min_segment_length"]:
                keywords.append(segment)
                
        # 限制关键词数量
        max_keywords = self.config["path_processing"]["max_segments"]
        return keywords[:max_keywords]


def main():
    # 设置输入输出路径
    input_file = Path("data/input/bookmarks.html")
    output_dir = Path("data/training")
    
    # 转换数据
    converter = BookmarkConverter()
    converter.convert_to_fasttext(input_file, output_dir)


if __name__ == "__main__":
    main() 