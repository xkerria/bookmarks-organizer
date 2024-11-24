from pathlib import Path
import argparse
import re
from src.models.fasttext_model import FastTextModel
from bs4 import BeautifulSoup
import logging
from src.config import config

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="组织书签")
    parser.add_argument("--input", type=str, default="data/input/bookmarks.html",
                      help="输入书签文件路径")
    parser.add_argument("--output", type=str, default="data/output/organized_bookmarks.html",
                      help="输出书签文件路径")
    parser.add_argument("--models", type=str, default="data/training",
                      help="模型目录路径")
    parser.add_argument("--verbose", action="store_true",
                      help="显示详细日志")
    return parser.parse_args()

def organize_bookmarks(input_file: Path, output_file: Path, model_dir: Path):
    """组织书签文件"""
    try:
        # 加载模型
        logger.info("正在加载模型...")
        model = FastTextModel()
        model.load_model(model_dir)
        logger.info("模型加载完成")
        
        # 读取书签文件
        logger.info(f"正在读取书签文件: {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
        # 统计书签数量
        bookmarks = soup.find_all("a")
        total = len(bookmarks)
        logger.info(f"找到 {total} 个书签")
            
        # 处理每个书签
        processed = 0
        skipped = 0
        
        logger.info("开始组织书签...")
        for link in bookmarks:
            try:
                title = link.text.strip()
                url = link.get("href", "")
                
                # 获取预测结果
                text = f"{title} {url}"
                predictions = {
                    "type": model.predict_dimension(text, "type"),
                    "domain": model.predict_dimension(text, "domain"),
                    "content": model.predict_dimension(text, "content")
                }
                
                # 生成新标题
                new_title = format_title(title, predictions)
                link.string = new_title
                
                # 移动到对应文件夹
                move_to_folder(link, predictions, soup)
                processed += 1
                
                # 定期显示进度
                if processed % 100 == 0:
                    logger.info(f"已组织: {processed}/{total} ({processed/total:.1%})")
                
            except Exception as e:
                logger.warning(f"组织书签失败：{title} - {str(e)}")
                skipped += 1
                continue
            
        # 保存组织后的书签
        logger.info("正在保存组织后的书签...")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(soup))
            
        logger.info(f"书签组织完成，已保存到：{output_file}")
        logger.info("组织统计:")
        logger.info(f"- 总计书签: {total} 个")
        logger.info(f"- 成功组织: {processed} 个 ({processed/total:.1%})")
        logger.info(f"- 组织失败: {skipped} 个 ({skipped/total:.1%})")
        
    except Exception as e:
        logger.error(f"书签组织失败：{str(e)}")
        raise

def format_title(title: str, predictions: dict) -> str:
    """格式化书签标题"""
    # 移除已有的前缀
    clean_title = re.sub(r'^((?:(?:doc|tip|res|entry|pkg|api|ref|tool|blog):)+)', '', title).strip()
    
    # 添加新的前缀
    prefixes = []
    
    # 添加类型标签
    if predictions["type"]:
        prefixes.append(f"{predictions['type'][0]}:")
        
    # 添加内容标签（可选）
    if config.config.get("organize", {}).get("add_content_prefix", False):
        if predictions["content"] and predictions["content"][0] != "content_other":
            prefixes.append(f"{predictions['content'][0].replace('content_', '')}:")
    
    return f"{' '.join(prefixes)}{clean_title}"

def move_to_folder(link, predictions: dict, soup) -> None:
    """移动书签到对应文件夹"""
    try:
        # 创建或获取目标文件夹
        folder_name = get_folder_name(predictions)
        folder = ensure_folder_exists(folder_name, soup)
        
        # 移动书签
        old_parent = link.parent
        new_dt = soup.new_tag("dt")
        new_dt.append(link)
        folder.dl.append(new_dt)
        
        # 如果原父节点为空，则删除
        if old_parent and not old_parent.find_all(["a", "h3"]):
            old_parent.decompose()
            
    except Exception as e:
        logger.warning(f"移动书签失败：{str(e)}")
        raise

def get_folder_name(predictions: dict) -> str:
    """根据预测结果生成文件夹名"""
    if predictions["domain"]:
        domain = predictions["domain"][0].replace("domain_", "")
        if domain != "other":
            return domain
            
    # 如果没有明确的领域或是其他类，尝试使用内容类型
    if predictions["content"]:
        content = predictions["content"][0].replace("content_", "")
        if content != "other":
            return f"其他_{content}"
    
    return "未分类"

def ensure_folder_exists(name: str, soup) -> BeautifulSoup:
    """确保文件夹存在"""
    # 查找现有文件夹
    for h3 in soup.find_all("h3"):
        if h3.text.strip() == name:
            return h3.find_parent("dt")
            
    # 创建新文件夹
    root_dl = soup.find("dl")
    if not root_dl:
        root_dl = soup.new_tag("dl")
        soup.append(root_dl)
        
    folder_dt = soup.new_tag("dt")
    folder_h3 = soup.new_tag("h3")
    folder_h3.string = name
    folder_dl = soup.new_tag("dl")
    
    folder_dt.append(folder_h3)
    folder_dt.append(folder_dl)
    root_dl.append(folder_dt)
    
    return folder_dt

def main():
    args = parse_args()
    organize_bookmarks(
        Path(args.input),
        Path(args.output),
        Path(args.models)
    )

if __name__ == "__main__":
    main() 