from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json
from typing import List, Dict, Set, Tuple

class BookmarkConverter:
    def __init__(self):
        # 从分析器加载分类规则
        self.domains = {
            "技术": {
                "keywords": [
                    "编程", "开发", "python", "java", "javascript", 
                    "github", "代码", "框架", "数据库", "运维", "部署",
                ],
                "domains": [
                    "github.com", "stackoverflow.com", "leetcode.com",
                    "developer.", "docs.", ".dev", 
                ]
            },
            "游戏娱乐": {
                "keywords": [
                    "游戏", "攻略", "娱乐", "动漫", "直播", "steam",
                    "ps5", "xbox", "switch", "moba", "rpg",
                ],
                "domains": [
                    "miyoushe.com", "steam.com", "xbox.com", 
                    "nintendo.com", "playstation.com", "bilibili.com",
                ]
            },
            # ... (其他领域定义保持不变)
        }
        
        self.content_types = {
            "官方文档": ["docs", "document", "文档", "手册", "指南", "reference"],
            "教程指南": ["tutorial", "guide", "教程", "指南", "入门", "课程"],
            "工具应用": ["tool", "app", "工具", "应用", "软件", "插件"],
            "社区讨论": ["forum", "community", "社区", "讨论", "问答", "交流"],
            "博客文章": ["blog", "article", "博客", "文章", "专栏", "post"],
            "视频内容": ["video", "视频", "直播", "live", "课程", "教学"],
            "资源素材": ["resource", "material", "资源", "素材", "模板", "源码"],
        }

    def convert_to_fasttext(self, input_file: Path, output_file: Path):
        """将书签文件转换为 FastText 训练格式"""
        if not input_file.exists():
            raise FileNotFoundError(f"输入文件不存在：{input_file}")
            
        try:
            bookmarks = self._load_bookmarks(input_file)
            if not bookmarks:
                raise ValueError("未找到任何书签数据")
                
            training_data = []
            for bookmark in bookmarks:
                try:
                    labels, features = self._process_bookmark(bookmark)
                    if labels and features:
                        label_str = " ".join([f"__label__{label}" for label in labels])
                        training_data.append(f"{label_str} {features}")
                except Exception as e:
                    print(f"警告：处理书签时出错，已跳过：{bookmark.get('title', '未知')} - {str(e)}")
                    continue

            if not training_data:
                raise ValueError("没有生成任何有效的训练数据")

            # 写入文件
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(training_data))
            except PermissionError:
                raise PermissionError(f"无法写入输出文件，请检查权限：{output_file}")

            print(f"已生成训练数据：{output_file}")
            print(f"总样本数：{len(training_data)}")
            
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
        # 移除前缀标记
        text = re.sub(r'^(doc|pkg|api|ref|tool|res|blog):\s*', '', text.lower())
        # 移除特殊字符
        text = re.sub(r'[^\w\s]', ' ', text)
        # 替换连续空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_prefix_label(self, title: str) -> str:
        """提取前缀标签"""
        match = re.match(r'^(doc|pkg|api|ref|tool|res|blog):', title.lower())
        if match:
            prefix = match.group(1)
            return f"type_{prefix}"
        return ""

    def _get_domain_label(self, title: str, url: str) -> str:
        """获取领域标签"""
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
        # 分割路径并清理
        keywords = []
        for part in path.split('/'):
            if part:
                # 移除非字母数字字符
                clean_part = re.sub(r'[^\w]', '', part.lower())
                if clean_part:
                    keywords.append(f"path_{clean_part}")
        return keywords


def main():
    # 设置输入输出路径
    input_file = Path("data/input/bookmarks.html")
    output_file = Path("data/training/bookmarks_fasttext.txt")
    
    # 转换数据
    converter = BookmarkConverter()
    converter.convert_to_fasttext(input_file, output_file)


if __name__ == "__main__":
    main() 