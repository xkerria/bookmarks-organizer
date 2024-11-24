from pathlib import Path
from src.data.converter import BookmarkConverter
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="转换书签为训练数据")
    parser.add_argument("--input", type=str, default="data/input/bookmarks.html",
                      help="输入书签文件路径")
    parser.add_argument("--output", type=str, default="data/training",
                      help="输出目录路径")
    return parser.parse_args()

def main():
    try:
        args = parse_args()
        input_file = Path(args.input)
        output_dir = Path(args.output)
        
        print(f"开始转换书签文件：{input_file}")
        
        # 创建转换器并执行转换
        converter = BookmarkConverter()
        converter.convert_to_fasttext(input_file, output_dir)
        
        print(f"转换完成！数据已保存到：{output_dir}")
        
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 