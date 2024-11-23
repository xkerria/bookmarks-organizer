from pathlib import Path
import random
from typing import List, Dict

class TestDataGenerator:
    @staticmethod
    def generate_test_bookmarks(count: int = 10) -> List[Dict]:
        """生成测试用的书签数据"""
        categories = [
            ("doc", "文档"),
            ("pkg", "工具"),
            ("tip", "教程"),
            ("res", "资源")
        ]
        
        domains = [
            "github.com",
            "docs.python.org",
            "stackoverflow.com",
            "medium.com"
        ]
        
        bookmarks = []
        for _ in range(count):
            prefix, category = random.choice(categories)
            domain = random.choice(domains)
            path = f"/test/{random.randint(1000, 9999)}"
            
            bookmark = {
                "title": f"{prefix}: Test {category} {random.randint(1, 100)}",
                "url": f"https://{domain}{path}"
            }
            bookmarks.append(bookmark)
        
        return bookmarks
    
    @staticmethod
    def generate_test_html(bookmarks: List[Dict], output_path: Path):
        """生成测试用的书签HTML文件"""
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
"""
        
        for bookmark in bookmarks:
            html += f'    <DT><A HREF="{bookmark["url"]}">{bookmark["title"]}</A>\n'
        
        html += "</DL><p>"
        
        output_path.write_text(html, encoding='utf-8')
        return output_path 