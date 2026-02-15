"""运行所有测试的脚本"""
import sys
import subprocess
import os


def run_tests():
    """运行所有测试"""
    # 获取测试目录
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(test_dir)
    
    # 添加项目根目录到路径
    sys.path.insert(0, project_root)
    
    # 运行 pytest
    result = subprocess.run(
        ["pytest", test_dir, "-v", "--tb=short"],
        cwd=project_root
    )
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

