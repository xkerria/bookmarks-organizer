from pathlib import Path
from collections import Counter
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

class BookmarkAnalyzer:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.soup = None
        self.stats = {
            "总书签数": 0,
            "资源类型分布": Counter(),
            "语言分布": Counter(),
            "域名TOP10": Counter(),
            "领域分布": Counter(),
            "内容形式": Counter(),
            "用途分布": Counter(),
        }
        
        # 领域分类定义
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
            "媒体资讯": {
                "keywords": [
                    "新闻", "资讯", "博客", "专栏", "评论", "观点",
                    "报道", "杂志", "媒体",
                ],
                "domains": [
                    "zhihu.com", "jianshu.com", "csdn.net",
                    "medium.com", "juejin.cn", "weixin.qq.com",
                ]
            },
            "学习教育": {
                "keywords": [
                    "教程", "课程", "学习", "培训", "考试", "证书",
                    "文档", "指南", "教育", "知识",
                ],
                "domains": [
                    "coursera.org", "udemy.com", "edx.org",
                    "w3schools.com", "runoob.com", "tutorial",
                ]
            },
            "生活服务": {
                "keywords": [
                    "购物", "美食", "旅游", "健康", "生活", "服务",
                    "商城", "外卖", "订票", "酒店",
                ],
                "domains": [
                    "taobao.com", "jd.com", "meituan.com",
                    "ctrip.com", "12306.cn",
                ]
            },
            "设计创意": {
                "keywords": [
                    "设计", "创意", "UI", "UX", "素材", "图片",
                    "插画", "艺术", "灵感", "配色",
                ],
                "domains": [
                    "dribbble.com", "behance.net", "ui8.net",
                    "zcool.com.cn", "huaban.com",
                ]
            },
        }

        # 内容形式定义
        self.content_types = {
            "官方文档": ["docs", "document", "文档", "手册", "指南", "reference"],
            "教程指南": ["tutorial", "guide", "教程", "指南", "入门", "课程"],
            "工具应用": ["tool", "app", "工具", "应用", "软件", "插件"],
            "社区讨论": ["forum", "community", "社区", "讨论", "问答", "交流"],
            "博客文章": ["blog", "article", "博客", "文章", "专栏", "post"],
            "视频内容": ["video", "视频", "直播", "live", "课程", "教学"],
            "资源素材": ["resource", "material", "资源", "素材", "模板", "源码"],
        }

        # 用途分类定义
        self.usage_types = {
            "常用工具": ["tool", "工具", "常用", "必备", "实用", "效率"],
            "参考资料": ["reference", "参考", "示例", "demo", "样例", "案例"],
            "学习提升": ["learn", "study", "学习", "提升", "进阶", "深入"],
            "灵感创意": ["inspiration", "idea", "灵感", "创意", "设计", "参考"],
            "资源收藏": ["collection", "收藏", "资源", "汇总", "合集", "精选"],
        }

    def analyze(self):
        """执行完整的书签分析"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"书签文件不存在：{self.file_path}")
            
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.soup = BeautifulSoup(f, "html.parser")
            
            if not self.soup.find_all("a"):
                raise ValueError("未在文件中找到任何书签")
                
            self._analyze_bookmarks()
            return self.stats
        except UnicodeDecodeError:
            raise ValueError(f"文件编码错误，请确保文件为UTF-8编码：{self.file_path}")
        except Exception as e:
            raise RuntimeError(f"分析过程中出错：{str(e)}")

    def _analyze_bookmarks(self):
        """分析书签内容"""
        all_bookmarks = self.soup.find_all("a")
        self.stats["总书签数"] = len(all_bookmarks)

        # 分析每个书签
        for bookmark in all_bookmarks:
            title = bookmark.text.strip()
            url = bookmark.get("href", "")
            text = f"{title} {url}".lower()

            # 1. 统计资源类型
            self._analyze_resource_type(title, url)

            # 2. 统计域名
            domain = urlparse(url).netloc
            if domain:
                self.stats["域名TOP10"][domain] += 1

            # 3. 统计语言
            if re.search(r"[\u4e00-\u9fff]", title):
                self.stats["语言分布"]["zh"] += 1
            else:
                self.stats["语言分布"]["en"] += 1

            # 4. 分析领域
            for domain_name, domain_info in self.domains.items():
                if (any(kw in text for kw in domain_info["keywords"]) or
                    any(d in url for d in domain_info["domains"])):
                    self.stats["领域分布"][domain_name] += 1

            # 5. 分析内容形式
            for type_name, keywords in self.content_types.items():
                if any(kw in text for kw in keywords):
                    self.stats["内容形式"][type_name] += 1

            # 6. 分析用途
            for usage_name, keywords in self.usage_types.items():
                if any(kw in text for kw in keywords):
                    self.stats["用途分布"][usage_name] += 1

        # 后处理
        self.stats["域名TOP10"] = Counter(dict(self.stats["域名TOP10"].most_common(10)))

    def _analyze_resource_type(self, title: str, url: str):
        """分析资源类型"""
        type_found = False
        for prefix in ["doc:", "pkg:", "api:", "ref:", "tool:", "res:", "blog:"]:
            if title.lower().startswith(prefix):
                self.stats["资源类型分布"][prefix[:-1]] += 1
                type_found = True
                break

        if not type_found:
            if "github.com" in url:
                self.stats["资源类型分布"]["pkg"] += 1
            elif "docs." in url or "/docs/" in url or "文档" in title:
                self.stats["资源类型分布"]["doc"] += 1
            elif "api." in url or "/api/" in url:
                self.stats["资源类型分布"]["api"] += 1
            elif any(word in title.lower() for word in ["blog", "博客"]):
                self.stats["资源类型分布"]["blog"] += 1
            elif any(word in title.lower() for word in ["tool", "工具"]):
                self.stats["资源类型分布"]["tool"] += 1
            elif any(word in title.lower() for word in ["参考", "示例"]):
                self.stats["资源类型分布"]["ref"] += 1
            else:
                self.stats["资源类型分布"]["res"] += 1

    def print_report(self):
        """打印分析报告"""
        print("\n=== 书签分析报告 ===")
        print(f"\n总书签数：{self.stats['总书签数']}")

        print("\n资源类型分布：")
        for type_, count in self.stats["资源类型分布"].items():
            print(f"  {type_:6} : {count:4d} ({count/self.stats['总书签数']*100:5.1f}%)")

        print("\n领域分布：")
        for domain, count in self.stats["领域分布"].items():
            print(f"  {domain:8} : {count:4d}")

        print("\n内容形式：")
        for form, count in self.stats["内容形式"].items():
            print(f"  {form:8} : {count:4d}")

        print("\n用途分布：")
        for usage, count in self.stats["用途分布"].items():
            print(f"  {usage:8} : {count:4d}")

        print("\n语言分布：")
        for lang, count in self.stats["语言分布"].items():
            print(f"  {lang:6} : {count:4d}")

        print("\nTOP10 域名：")
        for domain, count in self.stats["域名TOP10"].items():
            print(f"  {domain:30} : {count:4d}")

    def save_report(self):
        """保存分析报告"""
        try:
            output_file = Path("data/analysis/bookmark_analysis.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            print(f"\n详细分析结果已保存到：{output_file}")
        except PermissionError:
            raise PermissionError(f"无法写入文件，请检查权限：{output_file}")
        except Exception as e:
            raise RuntimeError(f"保存报告时出错：{str(e)}") 