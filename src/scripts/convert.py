from pathlib import Path
from src.data.converter import BookmarkConverter
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="将书签转换为 FastText 训练格式")
    parser.add_argument("--input", "-i", type=str, default="data/input/bookmarks.html",
                      help="输入的书签文件路径")
    parser.add_argument("--output", "-o", type=str, default="data/training",
                      help="输出目录路径")
    parser.add_argument("--test-size", "-t", type=float, default=0.2,
                      help="测试集比例 (0-1)")
    parser.add_argument("--random-seed", "-s", type=int, default=42,
                      help="随机数种子")
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        input_file = Path(args.input)
        output_dir = Path(args.output)
        
        print(f"开始转换书签文件：{input_file}")
        
        converter = BookmarkConverter()
        converter.convert_to_fasttext(
            input_file=input_file,
            output_dir=output_dir,
            test_size=args.test_size
        )
        
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 