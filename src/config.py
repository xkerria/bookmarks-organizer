from pathlib import Path
from typing import Dict
import yaml

# 基础路径
BASE_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = DATA_DIR / "logs"

# 默认文件
DEFAULT_INPUT_FILE = INPUT_DIR / "bookmarks.html"
DEFAULT_OUTPUT_FILE = OUTPUT_DIR / "organized_bookmarks.html"

# 确保所有目录存在
for dir_path in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

class Config:
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """从yaml文件加载配置"""
        try:
            with open('config.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 如果找不到主配置文件，尝试加载测试配置
            test_config = Path('tests/test_config.yaml')
            if test_config.exists():
                with open(test_config, 'r') as f:
                    return yaml.safe_load(f)
            return {}
    
    @property
    def api_settings(self) -> Dict:
        return self.config.get('api', {})
    
    @property
    def testing(self) -> Dict:
        return self.config.get('testing', {})
    
    @property
    def monitoring(self) -> Dict:
        return self.config.get('monitoring', {})