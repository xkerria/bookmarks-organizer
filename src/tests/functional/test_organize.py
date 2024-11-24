import unittest
from pathlib import Path
from src.scripts.organize import organize_bookmarks
import tempfile

class TestOrganize(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
    def test_organize_bookmarks(self):
        """测试书签组织功能"""
        # 准备测试数据
        test_html = """
        <dl>
            <dt><a href="https://github.com/test">pkg:Test Repo</a></dt>
            <dt><a href="https://docs.test.com">doc:Test Docs</a></dt>
        </dl>
        """
        
        input_file = self.test_dir / "input.html"
        output_file = self.test_dir / "output.html"
        model_dir = self.test_dir / "models"
        
        with open(input_file, "w") as f:
            f.write(test_html)
            
        # 执行组织
        organize_bookmarks(input_file, output_file, model_dir)
        
        # 验证输出
        self.assertTrue(output_file.exists()) 