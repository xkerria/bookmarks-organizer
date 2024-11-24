import pytest
from pathlib import Path
import os
from dotenv import load_dotenv

@pytest.fixture(scope="session")
def load_env():
    """加载环境变量"""
    load_dotenv()
    assert os.getenv("OPENAI_API_KEY"), "未设置 OPENAI_API_KEY"
    assert os.getenv("QIANFAN_AK"), "未设置 QIANFAN_AK"
    assert os.getenv("QIANFAN_SK"), "未设置 QIANFAN_SK"

@pytest.fixture
def mock_api_response():
    """模拟 API 响应的通用 fixture"""
    return {
        "技术/文档": [
            {"title": "Test Doc", "url": "http://test.com/doc"}
        ],
        "技术/工具": [
            {"title": "Test Tool", "url": "http://test.com/tool"}
        ]
    }

@pytest.fixture
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