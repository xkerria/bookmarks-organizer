from pathlib import Path
from src.data.analyzer import BookmarkAnalyzer
import sys

def main():
    try:
        input_file = Path("data/input/bookmarks.html")
        print(f"开始分析书签文件：{input_file}")

        analyzer = BookmarkAnalyzer(input_file)
        analyzer.analyze()
        
        # 打印分析报告
        analyzer.print_report()
        analyzer.save_report()
        
    except FileNotFoundError as e:
        print(f"错误：{str(e)}")
        sys.exit(1)
    except ValueError as e:
        print(f"错误：{str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"发生未预期的错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 