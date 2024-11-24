import pytest
from pathlib import Path
from src.data.converter import BookmarkConverter
import time

class TestConverterPerformance:
    @pytest.fixture
    def large_bookmarks_file(self, test_data_dir):
        """生成大量测试数据"""
        content = """
        <!DOCTYPE NETSCAPE-Bookmark-file-1>
        <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
        <TITLE>Bookmarks</TITLE>
        <H1>Bookmarks</H1>
        <DL><p>
        """
        
        # 生成1000个书签
        for i in range(1000):
            content += f"""
            <DT><A HREF="https://example.com/{i}">Bookmark {i}</A>
            """
            
        content += "</DL><p>"
        
        test_data_dir.mkdir(parents=True, exist_ok=True)
        bookmarks_file = test_data_dir / "large_bookmarks.html"
        bookmarks_file.write_text(content, encoding="utf-8")
        return bookmarks_file
        
    def test_conversion_performance(self, large_bookmarks_file, test_data_dir, benchmark):
        """测试转换性能"""
        output_dir = test_data_dir / "training"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        converter = BookmarkConverter()
        
        def run_conversion():
            converter.convert_to_fasttext(
                input_file=large_bookmarks_file,
                output_dir=output_dir,
                test_size=0.2
            )
            
        # 使用 pytest-benchmark 测试性能
        benchmark(run_conversion)