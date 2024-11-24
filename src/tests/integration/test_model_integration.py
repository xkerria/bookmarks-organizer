import unittest
from pathlib import Path
from src.models.fasttext_model import FastTextModel
from src.data.converter import BookmarkConverter
import tempfile

class TestModelIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.model = FastTextModel()
        self.converter = BookmarkConverter()
        
    def test_convert_and_train(self):
        """测试转换和训练流程"""
        # 准备测试数据
        test_html = """
        <dl>
            <dt><a href="https://github.com/test/repo">Test Repo</a></dt>
            <dt><a href="https://docs.python.org">Python Docs</a></dt>
        </dl>
        """
        
        input_file = self.test_dir / "test.html"
        with open(input_file, "w") as f:
            f.write(test_html)
            
        # 转换数据
        self.converter.convert_to_fasttext(input_file, self.test_dir)
        
        # 验证生成的文件
        self.assertTrue((self.test_dir / "train.txt").exists())
        self.assertTrue((self.test_dir / "test.txt").exists()) 