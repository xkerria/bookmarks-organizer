from pathlib import Path
from src.data.converter import BookmarkConverter
import sys

def main():
    try:
        input_file = Path("data/input/bookmarks.html")
        output_file = Path("data/training/bookmarks_fasttext.txt")
        
        print(f"开始转换书签文件：{input_file}")
        
        converter = BookmarkConverter()
        converter.convert_to_fasttext(input_file, output_file)
        
    except FileNotFoundError as e:
        print(f"错误：{str(e)}")
        sys.exit(1)
    except ValueError as e:
        print(f"错误：{str(e)}")
        sys.exit(1)
    except PermissionError as e:
        print(f"错误：{str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"发生未预期的错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 