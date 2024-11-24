from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from pathlib import Path
import re
from urllib.parse import urlparse


class BookmarkDataProcessor:
    def __init__(self):
        # 资源类型标签定义
        self.resource_types = {
            "doc:": "文档类资源",  # 文档、指南、教程
            "pkg:": "可复用组件",  # 库、框架、工具
            "api:": "接口服务",  # API、服务接口
            "ref:": "参考资料",  # 最佳实践、示例代码
            "tool:": "工具软件",  # 独立工具、应用
            "res:": "资源素材",  # 素材、资源
            "blog:": "博客文章",  # 新增：博客类内容
            "read:": "阅读材料",  # 新增：文章、新闻等
            "note:": "笔记资料",  # 新增：个人笔记、总结
            "vid:": "视频内容",  # 新增：视频资源
        }

        # 扩展领域分类
        self.content_domains = {
            # 技术相关
            "tech": {
                "frontend": ["react", "vue", "angular", "css", "javascript"],
                "backend": ["python", "java", "nodejs", "database"],
                "devops": ["docker", "kubernetes", "ci/cd", "monitoring"],
                "ai": ["machine-learning", "deep-learning", "nlp"],
            },
            # 媒体内容
            "media": {
                "video": ["youtube", "bilibili", "video", "course"],
                "audio": ["podcast", "music", "radio"],
                "reading": ["article", "blog", "news", "paper"],
            },
            # 工具资源
            "tools": {
                "productivity": ["todo", "notes", "calendar", "workflow"],
                "design": ["ui", "ux", "design", "figma", "sketch"],
                "collaboration": ["team", "project", "management"],
            },
            # 知识学习
            "learning": {
                "courses": ["course", "learn", "tutorial", "education"],
                "research": ["paper", "research", "study", "thesis"],
                "resources": ["book", "ebook", "pdf", "material"],
            },
            # 生活相关
            "lifestyle": {
                "shopping": ["shop", "store", "buy", "price"],
                "entertainment": ["game", "movie", "music", "fun"],
                "social": ["community", "forum", "social", "group"],
            },
        }

    def process_bookmarks_file(self, file_path: Path) -> List[Dict]:
        """处理书签文件，生成训练数据"""
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        training_data = []

        def process_folder(element, current_path=""):
            folder_name = element.find_previous_sibling("h3")
            if folder_name:
                folder_name = folder_name.text.strip()
                current_path = (
                    f"{current_path}/{folder_name}" if current_path else folder_name
                )

            for link in element.find_all("a"):
                original_title = link.text.strip()
                url = link.get("href", "")

                # 提取资源类型和清理后的标题
                resource_type, clean_title = self._extract_resource_type(original_title)

                if resource_type:  # 只处理有资源类型标记的书签
                    # 提取特征
                    type_features, context_features = self.extract_features(
                        clean_title, url
                    )

                    training_data.append(
                        {
                            "original": {
                                "title": original_title,
                                "url": url,
                                "folder_path": current_path,
                            },
                            "processed": {
                                "clean_title": clean_title,
                                "resource_type": resource_type,
                                "folder_path": current_path,
                            },
                            "features": {
                                "type_features": type_features,
                                "context_features": context_features,
                            },
                        }
                    )

            # 递归处理子文件夹
            for dl in element.find_all("dl"):
                process_folder(dl, current_path)

        # 从根目录开始处理
        root_dl = soup.find("dl")
        if root_dl:
            process_folder(root_dl)

        return training_data

    def _extract_resource_type(self, title: str) -> Tuple[str, str]:
        """提取资源类型和清理后的标题"""
        for prefix in self.resource_types:
            if title.startswith(prefix):
                return prefix.rstrip(":"), title[len(prefix) :].strip()
        return None, title

    def extract_features(self, title: str, url: str) -> Tuple[Dict, Dict]:
        """提取资源类型特征和上下文特征"""
        # 资源类型特征
        type_features = {
            "is_documentation": self._is_documentation(url, title),
            "is_tool": self._is_tool(url, title),
            "is_api": self._is_api(url, title),
            "is_reference": self._is_reference(url, title),
            "is_media": self._is_media(url, title),  # 新增
            "is_learning": self._is_learning(url, title),  # 新增
            "is_lifestyle": self._is_lifestyle(url, title),  # 新增
        }

        # 上下文特征
        context_features = {
            "domain_category": self._extract_domain_category(title, url),
            "content_type": self._extract_content_type(url),
            "url_structure": self._analyze_url_structure(url),
            "language_hint": self._detect_language(title, url),  # 新增：语言检测
        }

        return type_features, context_features

    def _is_documentation(self, url: str, title: str) -> bool:
        """判断是否为文档类资源"""
        indicators = [
            "docs." in url,
            "documentation" in url.lower(),
            any(
                kw in title.lower()
                for kw in ["documentation", "docs", "guide", "tutorial"]
            ),
        ]
        return any(indicators)

    def _is_tool(self, url: str, title: str) -> bool:
        """判断是否为工具类资源"""
        return "github.com" in url or any(
            kw in title.lower() for kw in ["tool", "package", "library", "framework"]
        )

    def _is_api(self, url: str, title: str) -> bool:
        """判断是否为API类资源"""
        return (
            "api." in url
            or "/api/" in url
            or any(kw in title.lower() for kw in ["api", "service", "endpoint"])
        )

    def _is_reference(self, url: str, title: str) -> bool:
        """判断是否为参考类资源"""
        return any(
            kw in title.lower()
            for kw in ["reference", "example", "best practice", "sample"]
        )

    def _extract_domain_category(self, title: str, url: str) -> Dict[str, List[str]]:
        """提取内容所属领域"""
        categories = {}
        text = f"{title} {url}".lower()

        for main_category, subcategories in self.content_domains.items():
            matches = []
            for subcat, keywords in subcategories.items():
                if any(kw in text for kw in keywords):
                    matches.append(subcat)
            if matches:
                categories[main_category] = matches

        return categories

    def _is_media(self, url: str, title: str) -> bool:
        """判断是否为媒体内容"""
        media_domains = ["youtube.com", "bilibili.com", "vimeo.com"]
        media_indicators = ["video", "watch", "stream", "podcast"]
        return any(domain in url for domain in media_domains) or any(
            ind in title.lower() for ind in media_indicators
        )

    def _is_learning(self, url: str, title: str) -> bool:
        """判断是否为学习资源"""
        learning_indicators = ["course", "learn", "study", "tutorial", "教程", "课程"]
        return any(ind in title.lower() for ind in learning_indicators)

    def _is_lifestyle(self, url: str, title: str) -> bool:
        """判断是否为生活相关内容"""
        lifestyle_indicators = ["shop", "game", "movie", "music", "社区", "购物"]
        return any(ind in title.lower() for ind in lifestyle_indicators)

    def _detect_language(self, title: str, url: str) -> str:
        """检测内容语言（简单实现）"""
        # 检测中文
        if re.search(r"[\u4e00-\u9fff]", title):
            return "zh"
        # 检测日文
        if re.search(r"[\u3040-\u30ff]", title):
            return "ja"
        # 默认英文
        return "en"

    def _analyze_url_structure(self, url: str) -> Dict:
        """分析URL结构"""
        parsed = urlparse(url)
        return {
            "domain": parsed.netloc,
            "path_depth": len([p for p in parsed.path.split("/") if p]),
            "has_query": bool(parsed.query),
            "has_fragment": bool(parsed.fragment),
        }

    def _extract_content_type(self, url: str) -> str:
        """提取内容类型"""
        # 视频网站
        if any(
            domain in url.lower()
            for domain in ["youtube.com", "bilibili.com", "vimeo.com"]
        ):
            return "video"

        # 代码仓库
        if any(
            domain in url.lower()
            for domain in ["github.com", "gitlab.com", "bitbucket.org"]
        ):
            return "code"

        # 文档网站
        if "docs." in url.lower() or "/docs/" in url.lower():
            return "documentation"

        # API 相关
        if "api." in url.lower() or "/api/" in url.lower():
            return "api"

        # 博客平台
        if any(
            domain in url.lower()
            for domain in ["medium.com", "dev.to", "blog.", "wordpress"]
        ):
            return "blog"

        # 社交平台
        if any(
            domain in url.lower()
            for domain in ["twitter.com", "linkedin.com", "facebook.com"]
        ):
            return "social"

        # 默认为网页
        return "webpage"
