from pathlib import Path
from collections import Counter
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


def analyze_bookmarks(file_path: Path):
    """分析书签数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    all_bookmarks = soup.find_all("a")
    total_count = len(all_bookmarks)

    stats = {
        "总书签数": total_count,
        "资源类型分布": Counter(),
        "文件夹分布": Counter(),
        "语言分布": Counter(),
        "域名TOP10": Counter(),
        "技术领域分布": Counter(),
        "特征分布": {
            "文档类": 0,
            "工具类": 0,
            "API类": 0,
            "参考资料": 0,
            "媒体内容": 0,
            "学习资源": 0,
            "生活相关": 0,
        },
    }

    # 技术领域分类
    tech_domains = {
        "web": {
            "name": "Web开发",
            "keywords": [
                "html",
                "css",
                "javascript",
                "vue",
                "react",
                "web",
                "前端",
                "webpack",
                "node",
            ],
        },
        "server": {
            "name": "服务端",
            "keywords": [
                "python",
                "java",
                "php",
                "spring",
                "django",
                "后端",
                "服务器",
                "数据库",
            ],
        },
        "mobile": {
            "name": "移动开发",
            "keywords": ["android", "ios", "flutter", "移动", "app", "小程序"],
        },
        "devops": {
            "name": "运维&部署",
            "keywords": [
                "docker",
                "kubernetes",
                "运维",
                "部署",
                "jenkins",
                "git",
                "linux",
            ],
        },
        "data": {
            "name": "数据技术",
            "keywords": ["数据库", "mysql", "redis", "mongodb", "数据分析", "大数据"],
        },
        "ai": {
            "name": "人工智能",
            "keywords": [
                "机器学习",
                "深度学习",
                "人工智能",
                "tensorflow",
                "pytorch",
                "nlp",
            ],
        },
        "security": {
            "name": "安全技术",
            "keywords": ["安全", "加密", "认证", "渗透", "网络安全"],
        },
        "architecture": {
            "name": "架构设计",
            "keywords": ["架构", "设计模式", "微服务", "分布式", "高可用"],
        },
    }

    def process_folders(element, current_path=""):
        """递归处理文件夹结构"""
        folder = element.find_previous_sibling("h3")
        if folder:
            name = folder.text.strip()
            path = f"{current_path}/{name}" if current_path else name

            # 统计当前文件夹下的直接书签数量
            bookmarks = element.find_all("a", recursive=False)
            if bookmarks:
                stats["文件夹分布"][path] = len(bookmarks)

            # 为书签添加文件夹路径
            for bookmark in bookmarks:
                bookmark.folder_path = path

            # 递归处理子文件夹
            for dl in element.find_all("dl", recursive=False):
                process_folders(dl, path)

    # 处理文件夹结构
    root_dl = soup.find("dl")
    if root_dl:
        process_folders(root_dl)

    # 分析每个书签
    for bookmark in all_bookmarks:
        title = bookmark.text.strip()
        url = bookmark.get("href", "")
        folder_path = getattr(bookmark, "folder_path", "")

        # 1. 统计资源类型
        type_found = False
        for prefix in ["doc:", "pkg:", "api:", "ref:", "tool:", "res:", "blog:"]:
            if title.lower().startswith(prefix):
                stats["资源类型分布"][prefix[:-1]] += 1
                type_found = True
                break

        if not type_found:
            if "github.com" in url:
                stats["资源类型分布"]["pkg"] += 1
            elif "docs." in url or "/docs/" in url or "文档" in title:
                stats["资源类型分布"]["doc"] += 1
            elif "api." in url or "/api/" in url:
                stats["资源类型分布"]["api"] += 1
            elif any(word in title.lower() for word in ["blog", "博客"]):
                stats["资源类型分布"]["blog"] += 1
            elif any(word in title.lower() for word in ["tool", "工具"]):
                stats["资源类型分布"]["tool"] += 1
            elif any(word in title.lower() for word in ["参考", "示例"]):
                stats["资源类型分布"]["ref"] += 1
            else:
                stats["资源类型分布"]["res"] += 1

        # 2. 统计域名
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain:
            stats["域名TOP10"][domain] += 1

        # 3. 统计语言
        if re.search(r"[\u4e00-\u9fff]", title):
            stats["语言分布"]["zh"] += 1
        else:
            stats["语言分布"]["en"] += 1

        # 4. 统计技术领域
        text = f"{title} {url} {folder_path}".lower()
        for domain, info in tech_domains.items():
            if any(keyword in text for keyword in info["keywords"]):
                stats["技术领域分布"][info["name"]] += 1

        # 5. 统计特征
        if "docs." in url or "/docs/" in url or "文档" in title:
            stats["特征分布"]["文档类"] += 1
        if "github.com" in url or "工具" in title:
            stats["特征分布"]["工具类"] += 1
        if "api." in url or "/api/" in url:
            stats["特征分布"]["API类"] += 1
        if any(word in title.lower() for word in ["参考", "示例", "demo"]):
            stats["特征分布"]["参考资料"] += 1
        if any(domain in url for domain in ["youtube.com", "bilibili.com"]):
            stats["特征分布"]["媒体内容"] += 1
        if any(word in title.lower() for word in ["教程", "学习", "课程"]):
            stats["特征分布"]["学习资源"] += 1
        if any(word in title.lower() for word in ["生活", "购物", "游戏"]):
            stats["特征分布"]["生活相关"] += 1

    # 后处理
    stats["域名TOP10"] = Counter(dict(stats["域名TOP10"].most_common(10)))
    stats["文件夹分布"] = Counter(
        {
            k: v
            for k, v in sorted(
                stats["文件夹分布"].items(), key=lambda x: x[1], reverse=True
            )
        }
    )

    return stats


def format_folder_path(path: str) -> str:
    """格式化文件夹路径显示"""
    parts = path.split("/")
    if len(parts) > 2:
        return f"{parts[0]}/.../{parts[-1]}"
    return path


def main():
    input_file = Path("data/input/bookmarks_2024_11_24.html")
    print(f"开始分析书签文件：{input_file}")

    stats = analyze_bookmarks(input_file)

    # 打印分析报告
    print("\n=== 书签分析报告 ===")
    print(f"\n总书签数：{stats['总书签数']}")

    print("\n资源类型分布：")
    for type_, count in stats["资源类型分布"].items():
        print(f"  {type_:6} : {count:4d} ({count/stats['总书签数']*100:5.1f}%)")

    print("\nTOP10 文件夹：")
    for folder, count in list(stats["文件夹分布"].items())[:10]:
        print(f"  {format_folder_path(folder):30} : {count:4d}")

    print("\n语言分布：")
    for lang, count in stats["语言分布"].items():
        print(f"  {lang:6} : {count:4d}")

    print("\nTOP10 域名：")
    for domain, count in stats["域名TOP10"].items():
        print(f"  {domain:30} : {count:4d}")

    print("\n技术领域分布：")
    for tech, count in stats["技术领域分布"].items():
        print(f"  {tech:12} : {count:4d}")

    print("\n特征分布：")
    for feature, count in stats["特征分布"].items():
        print(f"  {feature:8} : {count:4d}")

    # 保存结果
    output_file = Path("data/analysis/bookmark_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n详细分析结果已保存到：{output_file}")


if __name__ == "__main__":
    main()
