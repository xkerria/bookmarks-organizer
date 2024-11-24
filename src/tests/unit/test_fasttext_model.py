import unittest
from pathlib import Path
from src.models.fasttext_model import FastTextModel
import tempfile

class TestFastTextModel(unittest.TestCase):
    def setUp(self):
        self.model = FastTextModel()
        self.test_dir = Path(tempfile.mkdtemp())
        
    def test_dimension_filtering(self):
        """测试维度数据过滤"""
        test_data = [
            "__label__type_doc __label__domain_技术 test text",
            "__label__content_other some text",
            "__label__type_pkg __label__domain_other code"
        ]
        
        type_data = self.model._filter_dimension_data(test_data, "type_")
        self.assertEqual(len(type_data), 2)
        
        domain_data = self.model._filter_dimension_data(test_data, "domain_")
        self.assertEqual(len(domain_data), 2)
        
        content_data = self.model._filter_dimension_data(test_data, "content_")
        self.assertEqual(len(content_data), 1)