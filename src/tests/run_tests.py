import unittest
import sys
import os

def run_tests():
    """运行所有测试用例"""
    # 添加源代码目录到 Python 路径
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 