#!/bin/bash
# 运行各个模块测试的脚本

export PATH="$HOME/miniconda3/bin:$PATH"
eval "$(conda shell.bash hook)"
conda activate wechat-business-manager

cd "$(dirname "$0")/.."

MODULE=$1

if [ -z "$MODULE" ]; then
    echo "=========================================="
    echo "各模块测试脚本"
    echo "=========================================="
    echo ""
    echo "用法: $0 <模块名>"
    echo ""
    echo "可用模块:"
    echo "  preprocessor  - 消息预处理器 (4 tests)"
    echo "  llm_parser    - LLM 解析器 (6 tests)"
    echo "  pipeline      - 消息处理流水线 (8 tests)"
    echo "  repository    - 数据库访问层 (10 tests)"
    echo "  command       - 命令处理器 (10 tests)"
    echo "  summary       - 汇总服务 (6 tests)"
    echo "  all           - 运行所有测试 (44 tests)"
    echo "  coverage      - 生成覆盖率报告"
    echo ""
    exit 1
fi

case $MODULE in
    preprocessor)
        echo "=========================================="
        echo "测试: 消息预处理器"
        echo "=========================================="
        pytest tests/test_preprocessor.py -v --tb=short
        ;;
    llm_parser)
        echo "=========================================="
        echo "测试: LLM 解析器"
        echo "=========================================="
        pytest tests/test_llm_parser.py -v --tb=short
        ;;
    pipeline)
        echo "=========================================="
        echo "测试: 消息处理流水线"
        echo "=========================================="
        pytest tests/test_pipeline.py -v --tb=short
        ;;
    repository)
        echo "=========================================="
        echo "测试: 数据库访问层"
        echo "=========================================="
        pytest tests/test_repository.py -v --tb=short
        ;;
    command)
        echo "=========================================="
        echo "测试: 命令处理器"
        echo "=========================================="
        pytest tests/test_command_handler.py -v --tb=short
        ;;
    summary)
        echo "=========================================="
        echo "测试: 汇总服务"
        echo "=========================================="
        pytest tests/test_summary_svc.py -v --tb=short
        ;;
    all)
        echo "=========================================="
        echo "运行所有测试"
        echo "=========================================="
        pytest tests/ -v --tb=short
        ;;
    coverage)
        echo "=========================================="
        echo "生成测试覆盖率报告"
        echo "=========================================="
        pytest tests/ --cov=parsing --cov=db --cov=services --cov=core \
            --cov-report=term-missing --cov-report=html -v
        echo ""
        echo "✅ 覆盖率报告已生成: htmlcov/index.html"
        ;;
    *)
        echo "❌ 未知模块: $MODULE"
        echo "运行 '$0' 查看可用模块"
        exit 1
        ;;
esac

