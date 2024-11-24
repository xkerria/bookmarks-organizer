from pathlib import Path
import argparse
from src.models.fasttext_model import FastTextModel
from typing import Dict

def parse_args():
    parser = argparse.ArgumentParser(description="训练 FastText 模型")
    
    # 数据相关参数
    parser.add_argument("--train", type=str, default="data/training/train.txt",
                      help="训练数据文件路径")
    parser.add_argument("--valid", type=str, default="data/training/test.txt",
                      help="验证数据文件路径")
    
    # 其他参数
    parser.add_argument("--seed", type=int, default=42,
                      help="随机数种子")
    parser.add_argument("--output", type=str, default="data/training",
                      help="模型输出目录")
    parser.add_argument("--verbose", action="store_true",
                      help="显示详细日志")
    return parser.parse_args()

def print_evaluation_results(metrics: Dict):
    """打印分层模型的评估结果"""
    
    for dimension in ["type", "domain", "content"]:
        print("\n" + "="*50)
        print(f"{dimension.upper()} 维度评估结果".center(46))
        print("="*50)
        
        dim_metrics = metrics[dimension]
        
        # 1. 打印维度整体性能
        overall_metrics = calculate_overall_metrics(dim_metrics["per_label_metrics"])
        print(f"Precision: {overall_metrics['precision']:.2%}")
        print(f"Recall:    {overall_metrics['recall']:.2%}")
        print(f"F1 Score:  {overall_metrics['f1']:.2%}")
        print(f"样本总数:   {overall_metrics['total_samples']}")
        
        # 2. 按性能分组展示标签
        print("\n标签性能分布:")
        print("-" * 50)
        
        performance_groups = {
            "优秀 (F1 > 0.5)": [],
            "良好 (0.3 < F1 ≤ 0.5)": [],
            "一般 (0.1 < F1 ≤ 0.3)": [],
            "差 (0 < F1 ≤ 0.1)": [],
            "无效 (F1 = 0)": []
        }
        
        for label, m in dim_metrics["per_label_metrics"].items():
            if m["support"] == 0:
                continue
                
            if m["f1"] > 0.5:
                performance_groups["优秀 (F1 > 0.5)"].append((label, m))
            elif m["f1"] > 0.3:
                performance_groups["良好 (0.3 < F1 ≤ 0.5)"].append((label, m))
            elif m["f1"] > 0.1:
                performance_groups["一般 (0.1 < F1 ≤ 0.3)"].append((label, m))
            elif m["f1"] > 0:
                performance_groups["差 (0 < F1 ≤ 0.1)"].append((label, m))
            else:
                performance_groups["无效 (F1 = 0)"].append((label, m))
        
        for group_name, labels in performance_groups.items():
            if labels:
                print(f"\n{group_name}:")
                for label, m in sorted(labels, key=lambda x: x[1]["f1"], reverse=True):
                    print(f"{label:25} F1: {m['f1']:.2%} (support: {m['support']:3})")
        
        # 3. 主要问题分析
        print("\n主要问题分析:")
        print("-" * 50)
        
        # 样本不足的标签
        small_classes = sorted(
            [(l, m) for l, m in dim_metrics["per_label_metrics"].items() 
             if m["support"] > 0],
            key=lambda x: x[1]["support"]
        )[:5]
        
        print("\n样本不足的标签:")
        for label, m in small_classes:
            print(f"{label:25} (samples: {m['support']:3})")
        
        # 性能不佳的标签
        poor_performance = sorted(
            [(l, m) for l, m in dim_metrics["per_label_metrics"].items() 
             if m["support"] > 10 and m["f1"] < 0.2],
            key=lambda x: x[1]["f1"]
        )[:5]
        
        if poor_performance:
            print("\n性能不佳的主要标签:")
            for label, m in poor_performance:
                print(f"{label:25} F1: {m['f1']:.2%} (support: {m['support']:3})")

def calculate_overall_metrics(per_label_metrics: Dict) -> Dict:
    """计算总体指标"""
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_samples = 0
    
    for metrics in per_label_metrics.values():
        if metrics["support"] > 0:
            tp = metrics["precision"] * metrics["recall"] * metrics["support"]
            fn = metrics["support"] - tp
            fp = tp / metrics["precision"] - tp if metrics["precision"] > 0 else 0
            
            total_tp += tp
            total_fp += fp
            total_fn += fn
            total_samples += metrics["support"]
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "total_samples": total_samples
    }

def main():
    args = parse_args()
    
    try:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 训练模型
        model = FastTextModel()
        metrics = model.train(
            train_file=Path(args.train),
            valid_file=Path(args.valid)
        )
        
        # 打印评估结果
        print_evaluation_results(metrics)
        
    except Exception as e:
        print(f"训练失败：{str(e)}")
        raise

if __name__ == "__main__":
    main() 