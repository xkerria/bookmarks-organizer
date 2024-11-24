from pathlib import Path
import random
from typing import List, Dict

class TestDataGenerator:
    @staticmethod
    def generate_test_bookmarks(count: int = 10) -> List[Dict]:
        """生成测试用的书签数据"""
        prefixes = ["doc", "pkg", "api", "ref", "tool", "res", "blog"]
        domains = [
            "github.com",
            "docs.python.org",
            "miyoushe.com",
            "zhihu.com",
            "bilibili.com"
        ]
        
        bookmarks = []
        for i in range(count):
            prefix = random.choice(prefixes)
            domain = random.choice(domains)
            path = f"/test/{random.randint(1000, 9999)}"
            
            bookmark = {
                "title": f"{prefix}: Test Bookmark {i+1}",
                "url": f"https://{domain}{path}",
                "add_date": str(random.randint(1600000000, 1700000000)),
                "last_modified": str(random.randint(1600000000, 1700000000))
            }
            bookmarks.append(bookmark)
        
        return bookmarks

    @staticmethod
    def generate_test_html(bookmarks: List[Dict], output_path: Path) -> None:
        """生成测试用的书签HTML文件"""
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
"""
        
        for bookmark in bookmarks:
            add_date = f' ADD_DATE="{bookmark["add_date"]}"' if bookmark.get("add_date") else ""
            last_modified = f' LAST_MODIFIED="{bookmark["last_modified"]}"' if bookmark.get("last_modified") else ""
            
            html += f'    <DT><A HREF="{bookmark["url"]}"{add_date}{last_modified}>{bookmark["title"]}</A>\n'
        
        html += "</DL><p>"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8') 