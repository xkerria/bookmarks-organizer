import pytest
from pathlib import Path
from src.data.converter import BookmarkConverter

class TestConverterIntegration:
    @pytest.fixture
    def test_data_dir(self, tmp_path):
        return tmp_path / "data"
        
    @pytest.fixture
    def sample_bookmarks_file(self, test_data_dir):
        content = """
        <!DOCTYPE NETSCAPE-Bookmark-file-1>
        <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
        <TITLE>Bookmarks</TITLE>
        <H1>Bookmarks</H1>
        <DL><p>
            <DT><A HREF="https://docs.python.org/3/">doc: Python Documentation</A>
            <DT><A HREF="https://github.com/facebookresearch/fastText">pkg: FastText</A>
            <DT><A HREF="https://www.runoob.com/python/">Python 教程</A>
        </DL><p>
        """
        
        test_data_dir.mkdir(parents=True, exist_ok=True)
        bookmarks_file = test_data_dir / "bookmarks.html"
        bookmarks_file.write_text(content, encoding="utf-8")
        return bookmarks_file
        
    def test_full_conversion_process(self, test_data_dir, sample_bookmarks_file):
        """测试完整的转换流程"""
        output_dir = test_data_dir / "training"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行转换
        converter = BookmarkConverter()
        converter.convert_to_fasttext(
            input_file=sample_bookmarks_file,
            output_dir=output_dir
        )
        
        # 验证输出文件
        train_file = output_dir / "train.txt"
        test_file = output_dir / "test.txt"
        
        assert train_file.exists()
        assert test_file.exists()
        
        # 验证文件内容
        train_data = train_file.read_text(encoding="utf-8").splitlines()
        test_data = test_file.read_text(encoding="utf-8").splitlines()
        
        # 验证格式
        for line in train_data + test_data:
            assert line.startswith("__label__")
            assert " domain_" in line 