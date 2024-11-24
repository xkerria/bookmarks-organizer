from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup
from src.models.fasttext_model import FastTextModel
import logging
from src.config import config, INPUT_DIR, OUTPUT_DIR, LOGS_DIR

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建日志目录
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / "organize.log"

# 添加文件处理器
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class BookmarkOrganizer:
    def __init__(self):
        self.model = FastTextModel()
        self.model.load_model()
        
    def organize(self, input_file: Path = None, output_file: Path = None):
        """整理书签文件"""
        # 使用默认径
        if input_file is None:
            input_file = INPUT_DIR / "bookmarks.html"
        if output_file is None:
            output_file = OUTPUT_DIR / "organized_bookmarks.html"
            
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始整理书签文件：{input_file}")
        
        # 1. 加载书签
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                
            bookmarks = soup.find_all("a")
            logger.info(f"加载书签数量：{len(bookmarks)}")
                
        except FileNotFoundError:
            msg = f"书签文件不存在：{input_file}"
            logger.error(msg)
            raise FileNotFoundError(msg)
        except Exception as e:
            msg = f"加载书签文件失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
            
        # 2. 创建新的文档结构
        new_soup = BeautifulSoup(
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n'
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
            '<TITLE>Bookmarks</TITLE>\n'
            '<H1>Bookmarks</H1>\n',
            'html.parser'
        )
        
        root = new_soup.new_tag("DL")
        root.append(new_soup.new_tag("p"))
        
        folders = {
            "domain": {"name": "按领域", "dl": new_soup.new_tag("DL")},
            "type": {"name": "按类型", "dl": new_soup.new_tag("DL")},
            "content": {"name": "按内容", "dl": new_soup.new_tag("DL")}
        }
        
        # 为每个分类添加 <p> 标签
        for folder in folders.values():
            folder["dl"].append(new_soup.new_tag("p"))
            
        # 3. 处理每个书签
        processed = 0
        fallback = 0
        
        # 创建默认文件夹
        default_folders = {
            "domain": self._ensure_folder(folders["domain"]["dl"], "未分类", new_soup),
            "type": self._ensure_folder(folders["type"]["dl"], "未分类", new_soup),
            "content": self._ensure_folder(folders["content"]["dl"], "未分类", new_soup)
        }
        
        for bookmark in bookmarks:
            try:
                # 预测标签
                text = f"{bookmark.text} {bookmark['href']}"
                labels = self.model.predict(text)
                
                # 标记是否被处理
                bookmark_processed = False
                
                # 按标签类型分类
                for label in labels:
                    category, value = label.split("_", 1)
                    if category in folders:
                        # 确保子文件夹存在
                        folder = self._ensure_folder(folders[category]["dl"], value, new_soup)
                        # 复制书签并保留所有属性
                        new_bookmark = new_soup.new_tag("A")
                        for attr, val in bookmark.attrs.items():
                            new_bookmark[attr] = val
                        new_bookmark.string = bookmark.string
                        dt = new_soup.new_tag("DT")
                        dt.append(new_bookmark)
                        folder.append(dt)
                        bookmark_processed = True
                
                # 如果没有任何分类，放入默认文件夹
                if not bookmark_processed:
                    fallback += 1
                    logger.warning(f"使用默认分类的书签：{bookmark.get('href', '未知')}")
                    
                    # 复制到所有默认文件夹
                    for default_folder in default_folders.values():
                        new_bookmark = new_soup.new_tag("A")
                        for attr, val in bookmark.attrs.items():
                            new_bookmark[attr] = val
                        new_bookmark.string = bookmark.string
                        dt = new_soup.new_tag("DT")
                        dt.append(new_bookmark)
                        default_folder.append(dt)
                    
                    bookmark_processed = True
                
                if bookmark_processed:
                    processed += 1
                    
            except Exception as e:
                logger.error(f"处理书签失败：{bookmark.get('href', '未知')} - {str(e)}")
                # 即使出错也放入默认文件夹
                fallback += 1
                for default_folder in default_folders.values():
                    try:
                        new_bookmark = new_soup.new_tag("A")
                        for attr, val in bookmark.attrs.items():
                            new_bookmark[attr] = val
                        new_bookmark.string = bookmark.string
                        dt = new_soup.new_tag("DT")
                        dt.append(new_bookmark)
                        default_folder.append(dt)
                    except Exception as e2:
                        logger.error(f"添加到默认文件夹失败：{str(e2)}")
                        continue
        
        # 4. 构建最终结构
        for category, folder in folders.items():
            dt = new_soup.new_tag("DT")
            h3 = new_soup.new_tag("H3")
            h3.string = folder["name"]
            dt.append(h3)
            root.append(dt)
            root.append(folder["dl"])
            
        new_soup.append(root)
        
        # 5. 保存结果
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(str(new_soup))
            logger.info(f"书签整理完成！")
            logger.info(f"处理成功：{processed} 个")
            logger.info(f"使用默认分类：{fallback} 个")
            logger.info(f"输出文件：{output_file}")
        except Exception as e:
            msg = f"保存结果失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)

    def _ensure_folder(self, parent: BeautifulSoup, name: str, soup: BeautifulSoup) -> BeautifulSoup:
        """确保文件夹存在，不存在则创建"""
        # 查找现有文件夹
        for dt in parent.find_all("DT", recursive=False):
            h3 = dt.find("H3")
            if h3 and h3.string == name:
                return dt.find_next_sibling("DL")
        
        # 创建新文件夹
        dt = soup.new_tag("DT")
        h3 = soup.new_tag("H3")
        h3.string = name
        dt.append(h3)
        
        dl = soup.new_tag("DL")
        dl.append(soup.new_tag("p"))  # 必需的格式
        
        parent.append(dt)
        parent.append(dl)
        return dl
        
    def _get_category_name(self, category: str) -> str:
        """获取分类显示名称"""
        names = {
            "domain": "按领域",
            "type": "按类型",
            "content": "按内容"
        }
        return names.get(category, category) 