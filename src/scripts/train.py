from pathlib import Path
import argparse
from src.models.fasttext_model import FastTextModel

def parse_args():
    parser = argparse.ArgumentParser(description="训练 FastText 模型")
    
    # 数据相关参数
    parser.add_argument("--train", type=str, default="data/training/train.txt",
                      help="训练数据文件路径")
    parser.add_argument("--valid", type=str, default="data/training/test.txt",
                      help="验证数据文件路径")
    
    # 模型参数
    parser.add_argument("--epochs", type=int,
                      help="训练轮数 (默认: 配置文件中的值)")
    parser.add_argument("--lr", type=float,
                      help="学习率 (默认: 配置文件中的值)")
    parser.add_argument("--dim", type=int,
                      help="词向量维度 (默认: 配置文件中的值)")
    parser.add_argument("--word-ngrams", type=int,
                      help="词组长度 (默认: 配置文件中的值)")
    parser.add_argument("--min-count", type=int,
                      help="最小词频 (默认: 配置文件中的值)")
    
    # 预测参数
    parser.add_argument("--threshold", type=float,
                      help="预测阈值 (默认: 配置文件中的值)")
    parser.add_argument("--top-k", type=int, default=3,
                      help="返回前 K 个预测结果")
    
    # 其他参数
    parser.add_argument("--seed", type=int, default=42,
                      help="随机数种子")
    parser.add_argument("--output", type=str, default="data/training",
                      help="模型输出目录")
    parser.add_argument("--verbose", action="store_true",
                      help="显示详细日志")
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        print("开始训练模型...")
        model = FastTextModel()
        
        # 使用命令行参数覆盖配置
        if args.epochs:
            model.config['epochs'] = args.epochs
        if args.lr:
            model.config['learning_rate'] = args.lr
        if args.dim:
            model.config['embedding_dim'] = args.dim
        if args.word_ngrams:
            model.config['word_ngrams'] = args.word_ngrams
        if args.min_count:
            model.config['min_count'] = args.min_count
        if args.threshold:
            model.config['prediction_threshold'] = args.threshold
            
        # 设置输出路径
        if args.output:
            model.model_path = Path(args.output) / "model.bin"
            model.metrics_path = Path(args.output) / "metrics.json"
            
        # 训练模型
        metrics = model.train(
            train_file=Path(args.train),
            valid_file=Path(args.valid)
        )
        
        # 打印评估结果
        print("\n训练完成！评估结果：")
        for metric in ['precision', 'recall', 'f1', 'samples', 'skipped_samples']:
            if metric in metrics:
                print(f"{metric}: {metrics[metric]:.4f}")
                
        if args.verbose:
            print("\n各标签评估指标：")
            if 'per_label_metrics' in metrics:
                for label, label_metrics in metrics['per_label_metrics'].items():
                    if label_metrics['support'] > 0:
                        print(f"\n{label}:")
                        print(f"  Precision: {label_metrics['precision']:.4f}")
                        print(f"  Recall: {label_metrics['recall']:.4f}")
                        print(f"  F1: {label_metrics['f1']:.4f}")
                        print(f"  Support: {label_metrics['support']}")
            
    except Exception as e:
        print(f"训练失败：{str(e)}")
        
if __name__ == "__main__":
    main() 