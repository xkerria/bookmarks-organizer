from pathlib import Path
import fasttext
import json
from typing import Dict, List, Tuple
import logging
from src.config import config, TRAINING_DIR, LOGS_DIR
import re
import random

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建日志目录
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / "training.log"

# 添加文件处理器
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class FastTextModel:
    def __init__(self):
        self.model = None
        self.config = config.config["model"]["fasttext"]
        self.model_path = TRAINING_DIR / "model.bin"
        self.metrics_path = TRAINING_DIR / "metrics.json"
        
    def train(self, train_file: Path, valid_file: Path = None) -> Dict:
        """训练模型"""
        if not train_file.exists():
            msg = f"训练文件不存在：{train_file}"
            logger.error(msg)
            raise FileNotFoundError(msg)
            
        try:
            # 读取训练数据
            with open(train_file, "r", encoding="utf-8") as f:
                training_data = f.read().splitlines()
                
            # 数据增强
            enhanced_data = []
            for sample in training_data:
                parts = sample.split(" ", 1)
                if len(parts) == 2:
                    labels, text = parts
                    enhanced_text = self._enhance_features(text)
                    enhanced_data.append(f"{labels} {enhanced_text}")
                    
            # 数据平衡
            balanced_data = self._balance_dataset(enhanced_data)
            
            # 保存处理后的数据
            processed_file = train_file.parent / "processed_train.txt"
            with open(processed_file, "w", encoding="utf-8") as f:
                f.write("\n".join(balanced_data))
                
            # 训练参数
            params = {
                'lr': float(self.config['learning_rate']),
                'epoch': int(self.config['epochs']),
                'wordNgrams': int(self.config['word_ngrams']),
                'dim': int(self.config['embedding_dim']),
                'minCount': int(self.config['min_count']),
                'loss': str(self.config['loss_func']),
                'verbose': 2,
            }
            
            logger.info("开始训练模型")
            logger.info(f"训练参数：{params}")
            logger.info(f"训练文件：{processed_file}")
            if valid_file:
                logger.info(f"验证文件：{valid_file}")
            
            # 训练模型
            self.model = fasttext.train_supervised(
                input=str(processed_file),
                **params
            )
            
            # 评估模型
            metrics = self.evaluate(valid_file) if valid_file else {}
            
            # 保存模型和指标
            self.save_model()
            self.save_metrics(metrics)
            
            logger.info("模型训练完成")
            logger.info(f"评估指标：{metrics}")
            
            return metrics
            
        except Exception as e:
            msg = f"模型训练失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
            
    def evaluate(self, test_file: Path) -> Dict:
        """评估模型性能"""
        if not self.model:
            msg = "模型未训练"
            logger.error(msg)
            raise ValueError(msg)
            
        if not test_file.exists():
            msg = f"测试文件不存在：{test_file}"
            logger.error(msg)
            raise FileNotFoundError(msg)
            
        try:
            logger.info("开始评估模型")
            
            # 读取测试数据
            y_true = []
            y_pred = []
            skipped = 0
            
            # 记录每个标签的统计
            label_stats = {}
            
            with open(test_file, "r", encoding="utf-8") as f:
                for line in f:
                    # 分割标签和文本
                    parts = line.strip().split(" ", 1)
                    if len(parts) != 2:
                        continue
                        
                    # 获取真实标签
                    true_labels = set(l.replace("__label__", "") 
                                    for l in parts[0].split() 
                                    if l.startswith("__label__"))
                    text = parts[1]
                    
                    try:
                        # 预测标签
                        pred_labels = set(self.predict(text))
                        
                        # 更新每个标签的统计
                        for label in true_labels | pred_labels:
                            if label not in label_stats:
                                label_stats[label] = {
                                    "true_positives": 0,
                                    "false_positives": 0,
                                    "false_negatives": 0
                                }
                            
                            if label in true_labels and label in pred_labels:
                                label_stats[label]["true_positives"] += 1
                            elif label in pred_labels:
                                label_stats[label]["false_positives"] += 1
                            elif label in true_labels:
                                label_stats[label]["false_negatives"] += 1
                        
                        y_true.append(true_labels)
                        y_pred.append(pred_labels)
                    except Exception as e:
                        skipped += 1
                        logger.warning(f"预测失败，跳过样本：{text[:50]}... - {str(e)}")
                        continue
            
            # 计算整体指标
            metrics = self._calculate_metrics(y_true, y_pred)
            metrics["skipped_samples"] = skipped
            
            # 计算每个标签的指标
            per_label_metrics = {}
            for label, stats in label_stats.items():
                tp = stats["true_positives"]
                fp = stats["false_positives"]
                fn = stats["false_negatives"]
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                per_label_metrics[label] = {
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "support": tp + fn
                }
                
            metrics["per_label_metrics"] = per_label_metrics
            
            logger.info(f"评估完成：{metrics}")
            return metrics
            
        except Exception as e:
            msg = f"模型评估失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
            
    def predict(self, text: str, k: int = 3) -> List[str]:
        """预测标签"""
        if not self.model:
            raise ValueError("模型未训练")
        
        try:
            # 获取预测结果
            raw_prediction = self.model.predict(text, k=k)
            
            # FastText 返回格式: (labels, probs)
            # labels 和 probs 都是一维数组
            labels = raw_prediction[0]  # 标签数组
            probs = raw_prediction[1]   # 概率数组
            
            threshold = self.config["prediction_threshold"]
            results = []
            
            # 直接遍历原始返回值
            for label, prob in zip(labels, probs):
                if float(prob) > threshold:
                    # 确保标签是字符串
                    clean_label = str(label).replace("__label__", "")
                    results.append(clean_label)
                    
            return results
            
        except Exception as e:
            error_msg = (f"测失败：{str(e)}\n"
                        f"输入文本：{text}\n"
                        f"原始预测结果：{raw_prediction}")
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
    def save_model(self):
        """保存模型"""
        if not self.model:
            msg = "没有可保存的模型"
            logger.error(msg)
            raise ValueError(msg)
            
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            self.model.save_model(str(self.model_path))
            logger.info(f"模型已保存：{self.model_path}")
        except Exception as e:
            msg = f"模型保存失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
            
    def load_model(self):
        """加载模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型文件不存在：{self.model_path}")
            
        try:
            self.model = fasttext.load_model(str(self.model_path))
        except Exception as e:
            raise RuntimeError(f"模型加载失败：{str(e)}")
            
    def save_metrics(self, metrics: Dict):
        """保存评估指标"""
        try:
            self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            logger.info(f"评估指标已保存：{self.metrics_path}")
        except Exception as e:
            msg = f"指标保存失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
            
    def _calculate_metrics(self, y_true: List[set], y_pred: List[set]) -> Dict:
        """计算评估指标"""
        if not y_true or not y_pred:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "samples": 0
            }
        
        # 使用列表推导式计算，避免 NumPy
        precisions = []
        recalls = []
        
        for true_labels, pred_labels in zip(y_true, y_pred):
            if pred_labels:  # 避免除零错误
                precision = len(true_labels & pred_labels) / len(pred_labels)
                precisions.append(precision)
            
            if true_labels:  # 避免除零错误
                recall = len(true_labels & pred_labels) / len(true_labels)
                recalls.append(recall)
        
        # 计算平均值
        avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
        avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
        
        # 计算 F1
        f1 = 2 * avg_precision * avg_recall / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0.0
        
        return {
            "precision": float(avg_precision),
            "recall": float(avg_recall),
            "f1": float(f1),
            "samples": len(y_true)
        } 

    def print_metrics(self, metrics: Dict):
        """打印评估指标"""
        print("\n整体评估指标：")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall: {metrics['recall']:.4f}")
        print(f"F1 Score: {metrics['f1']:.4f}")
        print(f"样本数: {metrics['samples']}")
        
        if 'per_label_metrics' in metrics:
            print("\n各标签评估指标：")
            for label, label_metrics in metrics['per_label_metrics'].items():
                if label_metrics['support'] > 0:  # 只显示有样本的标签
                    print(f"\n{label}:")
                    print(f"  Precision: {label_metrics['precision']:.4f}")
                    print(f"  Recall: {label_metrics['recall']:.4f}")
                    print(f"  F1 Score: {label_metrics['f1']:.4f}")
                    print(f"  Support: {label_metrics['support']}") 

    def _enhance_features(self, text: str) -> str:
        """增强特征工程"""
        features = []
        
        # 1. 原始文本特征
        features.append(text)
        
        # 2. 分词并清理
        words = text.split()
        clean_words = []
        for word in words:
            # 移除特殊字符
            word = re.sub(r'[^\w\u4e00-\u9fff]', '', word)
            if word and len(word) > 1:  # 忽略空字符和单字符
                clean_words.append(word.lower())
        
        # 3. n-gram 特征
        for i in range(len(clean_words)-1):
            # 2-gram
            features.append(f"bigram_{clean_words[i]}_{clean_words[i+1]}")
            
            # 3-gram
            if i < len(clean_words)-2:
                features.append(f"trigram_{clean_words[i]}_{clean_words[i+1]}_{clean_words[i+2]}")
        
        # 4. 字符级特征
        for word in clean_words:
            if len(word) > 2:
                # 前缀和后缀
                features.append(f"prefix_{word[:3]}")
                features.append(f"suffix_{word[-3:]}")
                
                # 字符 bigram
                for i in range(len(word)-1):
                    features.append(f"char_bigram_{word[i:i+2]}")
        
        # 5. 领域特征
        for domain, info in self.config.get("domains", {}).items():
            keywords = info.get("keywords", [])
            if any(kw in text.lower() for kw in keywords):
                features.append(f"domain_{domain}")
        
        # 6. 内容类型特征
        for ctype, keywords in self.config.get("content_types", {}).items():
            if any(kw in text.lower() for kw in keywords):
                features.append(f"content_{ctype}")
            
        return " ".join(features)

    def _balance_dataset(self, samples: List[str], min_samples: int = 10) -> List[str]:
        """平衡数据集"""
        from collections import defaultdict
        import random
        
        # 按标签分组
        label_samples = defaultdict(list)
        for sample in samples:
            labels = [l for l in sample.split() if l.startswith("__label__")]
            for label in labels:
                label_samples[label].append(sample)
        
        # 统计标签分布
        label_counts = {label: len(samples) for label, samples in label_samples.items()}
        avg_count = sum(label_counts.values()) / len(label_counts)
        
        # 平衡数据集
        balanced_samples = []
        for label, samples in label_samples.items():
            count = len(samples)
            
            if count < min_samples:
                # 过采样
                multiplier = min_samples // count + 1
                augmented = samples * multiplier
                # 添加随机噪声
                augmented.extend([self._add_noise(s) for s in samples[:min_samples-len(augmented)]])
                balanced_samples.extend(augmented[:min_samples])
            elif count > avg_count * 2:
                # 欠采样
                target_count = int(avg_count * 1.5)
                balanced_samples.extend(random.sample(samples, target_count))
            else:
                balanced_samples.extend(samples)
        
        return balanced_samples

    def _add_noise(self, sample: str) -> str:
        """添加随机噪声进行数据增强"""
        # 分离标签和特征
        parts = sample.split(" ", 1)
        if len(parts) != 2:
            return sample
        
        labels, text = parts
        words = text.split()
        
        # 随机操作
        if random.random() < 0.3:  # 30% 概率删除词
            if len(words) > 3:
                del_idx = random.randint(0, len(words)-1)
                words.pop(del_idx)
                
        if random.random() < 0.3:  # 30% 概率重复词
            if words:
                dup_idx = random.randint(0, len(words)-1)
                words.insert(dup_idx, words[dup_idx])
                
        if random.random() < 0.3:  # 30% 概率打乱词序
            if len(words) > 2:
                start = random.randint(0, len(words)-2)
                words[start], words[start+1] = words[start+1], words[start]
        
        return f"{labels} {' '.join(words)}" 