import pytest
from pathlib import Path
from src.models.fasttext_model import FastTextModel

class TestFastTextModel:
    @pytest.fixture
    def model(self):
        return FastTextModel()
        
    @pytest.fixture
    def sample_data(self, test_data_dir):
        train_file = test_data_dir / "train.txt"
        test_file = test_data_dir / "test.txt"
        
        # 创建示例训练数据
        train_data = [
            "__label__type_doc __label__domain_技术 python documentation",
            "__label__type_pkg __label__domain_技术 github repository",
        ]
        train_file.write_text("\n".join(train_data))
        
        # 创建示例测试数据
        test_data = [
            "__label__type_doc __label__domain_技术 java documentation",
        ]
        test_file.write_text("\n".join(test_data))
        
        return train_file, test_file
        
    def test_train(self, model, sample_data):
        """测试模型训练"""
        train_file, test_file = sample_data
        metrics = model.train(train_file, test_file)
        
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert metrics["samples"] > 0
        
    def test_predict(self, model, sample_data):
        """测试模型预测"""
        train_file, _ = sample_data
        model.train(train_file)
        
        text = "python github documentation"
        labels = model.predict(text)
        
        assert len(labels) > 0
        assert all(isinstance(label, str) for label in labels)
        
    def test_save_load(self, model, sample_data, test_data_dir):
        """测试模型保存和加载"""
        train_file, _ = sample_data
        model.train(train_file)
        
        # 保存模型
        model.save_model()
        assert model.model_path.exists()
        
        # 加载模型
        new_model = FastTextModel()
        new_model.load_model()
        
        # 验证预测结果一致
        text = "test prediction"
        original_pred = model.predict(text)
        loaded_pred = new_model.predict(text)
        assert original_pred == loaded_pred 