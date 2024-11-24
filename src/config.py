from pathlib import Path
import yaml

# 添加目录配置
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
ANALYSIS_DIR = DATA_DIR / "analysis"
TRAINING_DIR = DATA_DIR / "training"

class Config:
    def __init__(self):
        self.config_file = ROOT_DIR / "config.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_file.exists():
            return self._get_default_config()
            
        with open(self.config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "converter": {
                "domains": {
                    "技术": {
                        "keywords": [
                            "编程", "开发", "python", "java", "javascript",
                            "github", "代码", "框架", "数据库", "运维", "部署",
                        ],
                        "domains": [
                            "github.com", "stackoverflow.com", "leetcode.com",
                            "developer.", "docs.", ".dev",
                        ]
                    },
                    # ... 其他领域配置
                },
                "content_types": {
                    "官方文档": ["docs", "document", "文档", "手册", "指南", "reference"],
                    # ... 其他内容类型配置
                },
                "feature_extraction": {
                    "max_path_keywords": 5,
                    "min_keyword_length": 2,
                    "stop_words": ["的", "了", "和", "与", "或", "及", "等", "the", "a", "an", "and", "or"],
                },
                "output_format": {
                    "label_prefix": "__label__",
                    "feature_separator": " ",
                }
            }
        }

config = Config()