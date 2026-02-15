#!/bin/bash
# 快速激活 conda 环境的脚本

export PATH="$HOME/miniconda3/bin:$PATH"
eval "$(conda shell.bash hook)"
conda activate wechat-business-manager

echo "✅ Conda 环境已激活: wechat-business-manager"
echo "Python 版本: $(python --version)"
echo ""
echo "运行测试:"
echo "  pytest tests/ -v"
echo "  或"
echo "  python tests/run_all_tests.py"
echo ""

