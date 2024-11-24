import pytest
from pathlib import Path
import os
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """设置测试环境"""
    # 创建测试所需目录
    test_dirs = [
        "data/input",
        "data/output",
        "data/analysis",
        "data/training",
        "data/logs",
        "tests/data"
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # 加载环境变量
    load_dotenv()

@pytest.fixture(scope="session")
def test_data_dir():
    """提供测试数据目录"""
    data_dir = Path("tests/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def cleanup_test_files():
    """清理测试文件的 fixture"""
    yield
    test_data_dir = Path("tests/data")
    if test_data_dir.exists():
        for file in test_data_dir.glob("*"):
            if file.is_file():
                file.unlink() 