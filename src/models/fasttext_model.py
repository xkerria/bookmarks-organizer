from pathlib import Path
import fasttext
import json
from typing import Dict, List, Tuple, Any
import logging
from src.config import config, TRAINING_DIR, LOGS_DIR
import re
import random
from collections import defaultdict
from gensim.models import KeyedVectors
import jieba
import numpy as np
from urllib.parse import urlparse

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
        self.config = config.config["model"]["fasttext"]
        # 分层模型
        self.type_model = None      # 类型分类
        self.domain_model = None    # 领域分类器
        self.content_model = None   # 内容分类器
        
        # 加载预训练词向量
        self.word_vectors = None
        if self.config.get("word_vectors", {}).get("enabled", False):
            self._load_word_vectors()
    
    def _load_word_vectors(self):
        """加载预训练词向量（带缓存）"""
        try:
            vector_path = Path(self.config["word_vectors"]["path"])
            cache_path = vector_path.parent / f"{vector_path.stem}.cache.pkl"
            
            logger.info(f"加载原始词向量: {vector_path}")
            
            # 尝试从缓存加载
            if cache_path.exists() and cache_path.stat().st_mtime > vector_path.stat().st_mtime:
                logger.info("从缓存加载词向量...")
                import pickle
                with open(cache_path, "rb") as f:
                    self.word_vectors = pickle.load(f)
                logger.info("缓存加载完成")
                return
            
            # 加载原始词向量
            self.word_vectors = KeyedVectors.load_word2vec_format(
                str(vector_path),
                binary=False
            )
            
            # 预计算相似度矩阵
            logger.info("预计算词向量相似度...")
            self.word_vectors.init_sims(replace=True)
            
            # 预热常用词
            logger.info("预热常用词...")
            common_words = ["python", "编程", "文档", "教程", "开发", "手册", "指南"]
            for word in common_words:
                if word in self.word_vectors:
                    _ = self.word_vectors[word]
            
            # 保存缓存
            logger.info("保存词向量缓存...")
            import pickle
            with open(cache_path, "wb") as f:
                pickle.dump(self.word_vectors, f)
            
            logger.info("词向量加载完成")
            
        except Exception as e:
            logger.warning(f"加载词向量失败: {str(e)}")
            self.word_vectors = None
    
    def train(self, train_file: Path, valid_file: Path = None) -> Dict:
        """训练分层模型"""
        try:
            # 读取数据
            with open(train_file, "r", encoding="utf-8") as f:
                data = f.read().splitlines()
            
            # 按维度分离数据
            type_data = self._filter_dimension_data(data, "type_")
            domain_data = self._filter_dimension_data(data, "domain_")
            content_data = self._filter_dimension_data(data, "content_")
            
            # 训练参数
            params = {
                'lr': self.config["learning_rate"],
                'epoch': self.config["epochs"],
                'wordNgrams': self.config["word_ngrams"],
                'dim': self.config["embedding_dim"],
                'minCount': self.config["min_count"],
                'loss': self.config["loss_func"],
                'verbose': 2,
            }
            
            logger.info("开始训练分层模型")
            logger.info(f"训练参数：{params}")
            
            # 训练各维度模型
            metrics = {}
            
            # 1. 类型分类器
            logger.info("训练类型分类器...")
            self.type_model = self._train_dimension_model(
                "type", type_data, valid_file, params)
            metrics["type"] = self._evaluate_dimension(
                "type", self.type_model, valid_file)
            
            # 2. 领域分类器
            logger.info("训练领域分类器...")
            self.domain_model = self._train_dimension_model(
                "domain", domain_data, valid_file, params)
            metrics["domain"] = self._evaluate_dimension(
                "domain", self.domain_model, valid_file)
            
            # 3. 内容分类器
            logger.info("训练内容分类器...")
            self.content_model = self._train_dimension_model(
                "content", content_data, valid_file, params)
            metrics["content"] = self._evaluate_dimension(
                "content", self.content_model, valid_file)
            
            # 保存模型和指标
            self._save_models()
            self.save_metrics(metrics)
            
            logger.info("分层模型训练完成")
            return metrics
            
        except Exception as e:
            msg = f"模型训练失败：{str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
    
    def _filter_dimension_data(self, data: List[str], prefix: str) -> List[str]:
        """过滤特定维度的数据"""
        filtered_data = []
        for line in data:
            labels = [l for l in line.split() if l.startswith(f"__label__{prefix}")]
            if labels:
                text = " ".join(line.split()[len(labels):])
                filtered_data.append(f"{' '.join(labels)} {text}")
        return filtered_data
    
    def _train_dimension_model(self, dimension: str, data: List[str], 
                             valid_file: Path, params: Dict) -> Any:
        """训练单个维度的模型"""
        try:
            # 保存维度数据
            temp_file = TRAINING_DIR / f"{dimension}_train.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("\n".join(data))
            
            # 调整参数
            local_params = params.copy()
            
            # 对于小数据集调整参数
            if len(data) < 100:
                local_params['minCount'] = 0
                local_params['epoch'] = min(200, local_params['epoch'])
                local_params['wordNgrams'] = min(2, local_params['wordNgrams'])
            
            # 训练模型
            model = fasttext.train_supervised(
                input=str(temp_file),
                **local_params
            )
            
            return model
            
        except Exception as e:
            logger.error(f"训练 {dimension} 维度失败: {str(e)}")
            raise
    
    def _save_models(self):
        """保存所有维度的模型"""
        if self.type_model:
            self.type_model.save_model(str(TRAINING_DIR / "type_model.bin"))
        if self.domain_model:
            self.domain_model.save_model(str(TRAINING_DIR / "domain_model.bin"))
        if self.content_model:
            self.content_model.save_model(str(TRAINING_DIR / "content_model.bin"))
    
    def load_model(self, model_path: Path, dimension: str = None):
        """加载指定维度的模型"""
        try:
            if dimension:
                # 加载指定维度的模型
                model_file = model_path / f"{dimension}_model.bin"
                if model_file.exists():
                    if dimension == "type":
                        self.type_model = fasttext.load_model(str(model_file))
                    elif dimension == "domain":
                        self.domain_model = fasttext.load_model(str(model_file))
                    elif dimension == "content":
                        self.content_model = fasttext.load_model(str(model_file))
                    logger.info(f"加载 {dimension} 维度模型成功")
                else:
                    logger.warning(f"{dimension} 维度模型文件不存在: {model_file}")
            else:
                # 尝试加载所有维度的模型
                for dim in ["type", "domain", "content"]:
                    model_file = model_path / f"{dim}_model.bin"
                    if model_file.exists():
                        if dim == "type":
                            self.type_model = fasttext.load_model(str(model_file))
                        elif dim == "domain":
                            self.domain_model = fasttext.load_model(str(model_file))
                        elif dim == "content":
                            self.content_model = fasttext.load_model(str(model_file))
                        logger.info(f"加载 {dim} 维度模型成功")
                    else:
                        logger.warning(f"{dim} 维度模型文件不存在: {model_file}")
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            raise
    
    def predict_dimension(self, text: str, dimension: str) -> List[str]:
        """预测指定维度的标签"""
        model = None
        if dimension == "type":
            model = self.type_model
        elif dimension == "domain":
            model = self.domain_model
        elif dimension == "content":
            model = self.content_model
        
        if not model:
            raise ValueError(f"模型 {dimension} 未加载")
        
        # 预处理文本
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())
        
        # 预测
        return self._predict_dimension(model, text)
    
    def _predict_dimension(self, model: Any, text: str) -> List[str]:
        """预测单个维度的标签"""
        labels, probs = model.predict(text, k=self.config.get("top_k", 3))
        threshold = self.config.get("prediction_threshold", 0.3)
        
        results = []
        for label, prob in zip(labels, probs):
            if prob >= threshold:
                clean_label = str(label).replace("__label__", "")
                results.append(clean_label)
                
        return results
    
    def _enhance_features(self, text: str) -> str:
        """增强文本特征"""
        features = []
        
        # 1. 原始文本
        features.append(text)
        
        # 2. URL特征
        url_features = re.findall(r'domain_\S+', text)
        if url_features:
            features.extend(url_features)
            # 添加域名部分特征
            for feature in url_features:
                parts = feature.split('_')
                if len(parts) > 2:
                    features.append(f"site_{parts[-1]}")
                    # 添加子域名特征
                    if len(parts) > 3:
                        features.append(f"subdomain_{parts[-2]}")
        
        # 3. 路径特征
        path_features = re.findall(r'path_\S+', text)
        if path_features:
            features.extend(path_features)
            # 组合相邻路径
            for i in range(len(path_features)-1):
                features.append(f"{path_features[i]}_{path_features[i+1]}")
        
        # 4. 词组特征
        words = text.split()
        if len(words) >= 2:
            # 双词组合
            for i in range(len(words)-1):
                features.append(f"{words[i]}_{words[i+1]}")
            # 三词组合
            if len(words) >= 3:
                for i in range(len(words)-2):
                    features.append(f"{words[i]}_{words[i+1]}_{words[i+2]}")
        
        # 5. 统计特征
        if len(words) > 0:
            features.append(f"length_{len(words)}")
            # 词长度分布
            word_lengths = [len(w) for w in words]
            avg_len = sum(word_lengths) / len(word_lengths)
            features.append(f"avg_word_length_{int(avg_len)}")
        
        # 6. 词向量特征
        if self.word_vectors is not None:
            # 分词
            words = jieba.lcut(text)
            semantic_features = []
            
            for word in words:
                if word in self.word_vectors:
                    # 获取最相似的词作为特征
                    similar_words = self.word_vectors.most_similar(word, topn=3)
                    for sim_word, score in similar_words:
                        if score > 0.6:  # 只使用相似度高的词
                            semantic_features.append(f"sim_{sim_word}")
            
            features.extend(semantic_features)
        
        return " ".join(features)
    
    def _enhance_url_features(self, url: str) -> List[str]:
        """增强URL特征"""
        features = []
        parsed = urlparse(url)
        
        # 域名分层特征
        domain_parts = parsed.netloc.split('.')
        features.extend([f"domain_{i}_{part}" for i, part in enumerate(domain_parts)])
        
        # 路径语义特征
        path_parts = [p for p in parsed.path.split('/') if p]
        if path_parts:
            # 路径深度特征
            features.append(f"path_depth_{len(path_parts)}")
            # 路径组合特征
            for i in range(len(path_parts)-1):
                features.append(f"path_seq_{path_parts[i]}_{path_parts[i+1]}")
        
        return features
    
    def _enhance_semantic_features(self, text: str) -> List[str]:
        """增强语义特征"""
        features = []
        
        # 分词
        words = jieba.lcut(text)
        word_vectors = []
        
        # 收集词向量
        for word in words:
            if word in self.word_vectors:
                word_vectors.append(self.word_vectors[word])
                # 获取相似词
                similar_words = self.word_vectors.most_similar(
                    word, 
                    topn=self.config["word_vectors"].get("max_similar_words", 3)
                )
                for sim_word, score in similar_words:
                    if score >= self.config["word_vectors"].get("min_similarity", 0.6):
                        features.append(f"sim_{sim_word}")
        
        # 如果有足够的词向量，计算主题特征
        if len(word_vectors) >= 2:
            avg_vector = np.mean(word_vectors, axis=0)
            topic_words = self.word_vectors.similar_by_vector(
                avg_vector,
                topn=3
            )
            for topic_word, score in topic_words:
                features.append(f"topic_{topic_word}")
        
        return features
    
    def _evaluate_dimension(self, dimension: str, model: Any, valid_file: Path) -> Dict:
        """评估单个维度的模型性能"""
        try:
            metrics = {
                "confusion_matrix": defaultdict(lambda: defaultdict(int)),
                "error_cases": [],
                "label_correlation": defaultdict(lambda: defaultdict(int)),
                "per_label_metrics": {}
            }
            
            # 如果没有验证文件，返回空指标
            if not valid_file or not valid_file.exists():
                logger.warning(f"{dimension} 维度没有验证数据")
                return metrics
            
            # 读取验证数据
            with open(valid_file, "r", encoding="utf-8") as f:
                valid_data = f.read().splitlines()
            
            # 过滤当前维度的数据
            dimension_data = self._filter_dimension_data(valid_data, f"{dimension}_")
            
            # 评估每个样本
            for line in dimension_data:
                # 分离标签和文本
                parts = line.split(" ", 1)
                if len(parts) != 2:
                    continue
                    
                labels_part, text = parts
                true_labels = set(l.replace("__label__", "") 
                                for l in labels_part.split() if l.startswith("__label__"))
                
                # 预处理文本
                text = text.replace('\n', ' ').replace('\r', ' ')
                text = ' '.join(text.split())
                
                # 预测标签
                pred_labels = set(self._predict_dimension(model, text))
                
                # 更新混淆矩阵
                for true_label in true_labels:
                    for pred_label in pred_labels:
                        if true_label == pred_label:
                            metrics["confusion_matrix"][true_label]["tp"] += 1
                        else:
                            metrics["confusion_matrix"][true_label]["fn"] += 1
                            metrics["confusion_matrix"][pred_label]["fp"] += 1
                
                # 收集错误案例
                if true_labels != pred_labels:
                    metrics["error_cases"].append({
                        "text": text,
                        "true": list(true_labels),
                        "pred": list(pred_labels)
                    })
                
                # 标签共现分析
                label_list = list(true_labels)
                for i in range(len(label_list)):
                    for j in range(i+1, len(label_list)):
                        metrics["label_correlation"][label_list[i]][label_list[j]] += 1
                        metrics["label_correlation"][label_list[j]][label_list[i]] += 1
            
            # 计算每个标签的指标
            for label, counts in metrics["confusion_matrix"].items():
                tp = counts["tp"]
                fp = counts["fp"]
                fn = counts["fn"]
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                metrics["per_label_metrics"][label] = {
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "support": tp + fn
                }
            
            logger.info(f"{dimension} 维度评估完成")
            return metrics
            
        except Exception as e:
            logger.error(f"评估 {dimension} 维度失败: {str(e)}")
            return {
                "confusion_matrix": {},
                "error_cases": [],
                "label_correlation": {},
                "per_label_metrics": {}
            }
    
    def save_metrics(self, metrics: Dict):
        """保存评估指标"""
        try:
            metrics_file = TRAINING_DIR / "metrics.json"
            
            # 转换 defaultdict 为普通 dict
            def convert_defaultdict(d):
                if isinstance(d, defaultdict):
                    d = dict(d)
                for k, v in d.items():
                    if isinstance(v, defaultdict):
                        d[k] = dict(v)
                    elif isinstance(v, dict):
                        d[k] = convert_defaultdict(v)
                return d
            
            # 处理指标数据
            metrics_data = convert_defaultdict(metrics)
            
            # 保存到文件
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"评估指标已保存：{metrics_file}")
            
        except Exception as e:
            logger.error(f"保存评估指标失败：{str(e)}")
            raise