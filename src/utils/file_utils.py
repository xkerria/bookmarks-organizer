from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict
import json

def create_test_bookmarks(input_file: Path, output_file: Path, num_bookmarks: int = 20):
    """从原始书签文件中提取指定数量的书签创建测试文件"""
    with open(input_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    # 获取前 num_bookmarks 个书签
    links = soup.find_all('a')[:num_bookmarks]
    
    # 创建新的书签文件
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file for testing.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
"""
    
    # 添加书签
    for link in links:
        html += str(link.parent) + "\n"
    
    html += "</DL><p>"
    
    # 保存测试文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html)
    
    print(f"已创建测试文件：{output_file}，包含 {len(links)} 个书签")

def save_json_response(data: dict, file_path: Path):
    """保存API响应的JSON数据"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2) 