from pathlib import Path
from src.data.processor import BookmarkDataProcessor
import json

def main():
    # 初始化处理器
    processor = BookmarkDataProcessor()
    
    # 设置输入输出路径
    input_file = Path("data/input/bookmarks.html")
    output_dir = Path("data/training/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"开始处理书签文件: {input_file}")
    
    try:
        # 处理书签文件
        training_data = processor.process_bookmarks_file(input_file)
        
        # 保存处理结果
        output_file = output_dir / "training_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        # 生成统计信息
        folders = set(item['features']['folder'] for item in training_data)
        prefixes = set()
        for item in training_data:
            if item['features'].get('has_prefix'):
                prefixes.update(item['features'].get('prefixes', []))
        domains = set(item['features']['domain'] for item in training_data)
        
        print("\n处理完成！")
        print(f"总书签数: {len(training_data)}")
        print(f"文件夹数: {len(folders)}")
        print(f"前缀类型: {len(prefixes)}")
        print(f"域名数量: {len(domains)}")
        print(f"\n结果已保存到: {output_file}")
        
        # 显示一些示例
        print("\n数据示例:")
        for item in training_data[:3]:
            print(f"\n标签: {item['label']}")
            print(f"文本: {item['text']}")
            print(f"特征: {item['features']}")
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 