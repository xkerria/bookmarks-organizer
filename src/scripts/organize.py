from pathlib import Path
import argparse
from src.bookmarks.organizer import BookmarkOrganizer
from src.config import INPUT_DIR, OUTPUT_DIR
import logging

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="自动整理书签")
    parser.add_argument("--input", "-i", type=str,
                      default=str(INPUT_DIR / "bookmarks.html"),
                      help="输入书签文件路径")
    parser.add_argument("--output", "-o", type=str,
                      default=str(OUTPUT_DIR / "organized_bookmarks.html"),
                      help="输出书签文件路径")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="显示详细日志")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger('src').setLevel(logging.DEBUG)
    
    try:
        logger.info("开始整理书签...")
        organizer = BookmarkOrganizer()
        organizer.organize(
            input_file=Path(args.input),
            output_file=Path(args.output)
        )
        
    except Exception as e:
        logger.error(f"整理失败：{str(e)}")
        raise

if __name__ == "__main__":
    main() 