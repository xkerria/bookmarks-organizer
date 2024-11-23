from src.bookmark_processor import BookmarkProcessor
from src.clients.ernie_client import ErnieClient
from src.clients.chatgpt_client import ChatGPTClient
from src.config import DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_FILE
import argparse

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='书签整理工具')
    parser.add_argument('--client', type=str, choices=['ernie', 'chatgpt'], 
                       default='ernie', help='选择使用的AI客户端')
    parser.add_argument('--input', type=str, default=str(DEFAULT_INPUT_FILE),
                       help='输入文件路径')
    parser.add_argument('--output', type=str, default=str(DEFAULT_OUTPUT_FILE),
                       help='输出文件路径')
    args = parser.parse_args()
    
    # 初始化处理器和客户端
    processor = BookmarkProcessor()
    client = ErnieClient() if args.client == 'ernie' else ChatGPTClient()
    
    try:
        print("开始加载书签文件...")
        processor.load_bookmarks(args.input)
        
        print("获取简化的书签数据...")
        bookmarks_data = processor.get_simplified_bookmarks()
        print(f"待处理书签数量：{len(bookmarks_data)}")
        
        print(f"\n正在使用 {args.client} 整理书签...")
        organized_bookmarks = client.categorize_bookmarks(bookmarks_data)
        
        if organized_bookmarks:
            print("\n处理完成！")
            if isinstance(organized_bookmarks[0], dict) and 'folders' in organized_bookmarks[0]:
                folders = organized_bookmarks[0]['folders']
                print(f"生成的分类数量：{len(folders)}")
                for folder in folders:
                    print(f"- {folder['name']}: {len(folder.get('bookmarks', []))} 个书签")
        
        print("\n更新书签数据...")
        processor.update_bookmarks_data(organized_bookmarks)
        
        print("保存整理后的书签...")
        processor.save_bookmarks(args.output)
        
        print(f"书签整理完成！输出文件：{args.output}")
        
    except Exception as e:
        print(f"处理过程中出现错误：{str(e)}")

if __name__ == "__main__":
    main() 