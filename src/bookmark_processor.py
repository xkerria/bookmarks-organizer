from bs4 import BeautifulSoup
from typing import Dict, List
import json

class BookmarkProcessor:
    def __init__(self):
        self.bookmarks_data = []
        self.soup = None

    def load_bookmarks(self, file_path: str):
        """加载书签文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.soup = BeautifulSoup(file, 'html.parser')
                self.bookmarks_data = self._extract_bookmarks()
        except Exception as e:
            raise Exception(f"加载书签文件失败: {str(e)}")

    def _extract_bookmarks(self) -> List[Dict]:
        """从HTML中提取书签数据"""
        bookmarks = []
        links = self.soup.find_all('a')
        for link in links:
            bookmark = {
                'title': link.get_text().strip(),
                'url': link.get('href', ''),
                'add_date': link.get('add_date', ''),
                'last_modified': link.get('last_modified', '')
            }
            bookmarks.append(bookmark)
        return bookmarks

    def save_bookmarks(self, output_path: str):
        """保存书签到HTML文件"""
        try:
            html = self._generate_bookmarks_html()
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(html)
        except Exception as e:
            raise Exception(f"保存书签文件失败: {str(e)}")

    def _generate_bookmarks_html(self) -> str:
        """生成书签HTML"""
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
"""
        
        # 处理文件夹结构
        for item in self.bookmarks_data:
            if isinstance(item, dict) and 'folders' in item:
                for folder in item['folders']:
                    html += self._generate_folder_html(folder)
            elif isinstance(item, dict) and 'title' in item and 'url' in item:
                html += self._generate_bookmark_html(item)

        html += "</DL><p>"
        return html

    def _generate_folder_html(self, folder: Dict, indent: int = 1) -> str:
        """生成文件夹HTML"""
        html = "    " * indent
        html += f'<DT><H3>{folder["name"]}</H3>\n'
        html += "    " * indent + "<DL><p>\n"
        
        # 处理文件夹中的书签
        for bookmark in folder.get('bookmarks', []):
            html += "    " * (indent + 1)
            html += self._generate_bookmark_html(bookmark)
        
        # 处理子文件夹
        for subfolder in folder.get('subfolders', []):
            html += self._generate_folder_html(subfolder, indent + 1)
        
        html += "    " * indent + "</DL><p>\n"
        return html

    def _generate_bookmark_html(self, bookmark: Dict) -> str:
        """生成单个书签HTML"""
        add_date = bookmark.get('add_date', '')
        last_modified = bookmark.get('last_modified', '')
        
        attributes = []
        if add_date:
            attributes.append(f'ADD_DATE="{add_date}"')
        if last_modified:
            attributes.append(f'LAST_MODIFIED="{last_modified}"')
        
        attrs = ' '.join(attributes)
        return f'<DT><A HREF="{bookmark["url"]}" {attrs}>{bookmark["title"]}</A>\n'

    def get_bookmarks_data(self) -> List[Dict]:
        """获取书签数据"""
        return self.bookmarks_data

    def update_bookmarks_data(self, new_data: List[Dict]):
        """更新书签数据"""
        self.bookmarks_data = new_data

    def get_simplified_bookmarks(self) -> List[Dict]:
        """获取简化的书签数据（只包含标题和URL）"""
        simplified = []
        for bookmark in self.bookmarks_data:
            if isinstance(bookmark, dict):
                if 'title' in bookmark and 'url' in bookmark:
                    simplified.append({
                        'title': bookmark['title'],
                        'url': bookmark['url']
                    })
                elif 'folders' in bookmark:
                    # 处理文件夹结构
                    simplified.extend(self._extract_bookmarks_from_folder(bookmark))
        return simplified

    def _extract_bookmarks_from_folder(self, folder: Dict) -> List[Dict]:
        """从文件夹结构中提取书签"""
        bookmarks = []
        
        # 处理当前文件夹中的书签
        for bookmark in folder.get('bookmarks', []):
            if 'title' in bookmark and 'url' in bookmark:
                bookmarks.append({
                    'title': bookmark['title'],
                    'url': bookmark['url']
                })
        
        # 递归处理子文件夹
        for subfolder in folder.get('subfolders', []):
            bookmarks.extend(self._extract_bookmarks_from_folder(subfolder))
        
        return bookmarks
    