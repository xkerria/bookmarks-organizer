import pytest
from pathlib import Path
from src.models.fasttext_model import FastTextModel
from src.tests.utils.test_data_generator import TestDataGenerator

class TestModelPerformance:
    @pytest.fixture
    def large_dataset(self, test_data_dir):
        """生成大量训练数据"""
        train_file = test_data_dir / "large_train.txt"
        test_file = test_data_dir / "large_test.txt"
        
        # 生成1000条训练数据
        train_data = []
        for i in range(1000):
            train_data.append(f"__label__type_doc __label__domain_技术 sample text {i}")
        train_file.write_text("\n".join(train_data))
        
        # 生成200条测试数据
        test_data = []
        for i in range(200):
            test_data.append(f"__label__type_doc __label__domain_技术 test text {i}")
        test_file.write_text("\n".join(test_data))
        
        return train_file, test_file
        
    def test_training_performance(self, large_dataset, benchmark):
        """测试训练性能"""
        train_file, test_file = large_dataset
        model = FastTextModel()
        
        def run_training():
            model.train(train_file, test_file)
            
        # 使用 pytest-benchmark 测试性能
        benchmark(run_training)
        
    def test_prediction_performance(self, large_dataset, benchmark):
        """测试预测性能"""
        train_file, _ = large_dataset
        model = FastTextModel()
        model.train(train_file)
        
        def run_prediction():
            for i in range(100):
                model.predict(f"test prediction text {i}")
                
        benchmark(run_prediction) 