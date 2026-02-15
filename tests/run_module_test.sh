#!/bin/bash
# 运行单个模块测试的脚本

MODULE=$1

if [ -z "$MODULE" ]; then
    echo "用法: $0 <模块名>"
    echo "可用模块:"
    echo "  preprocessor  - 消息预处理器"
    echo "  llm_parser    - LLM 解析器"
    echo "  pipeline      - 消息处理流水线"
    echo "  repository    - 数据库访问层"
    echo "  command       - 命令处理器"
    echo "  summary       - 汇总服务"
    echo "  all           - 运行所有测试"
    exit 1
fi

case $MODULE in
    preprocessor)
        pytest tests/test_preprocessor.py -v
        ;;
    llm_parser)
        pytest tests/test_llm_parser.py -v -s
        ;;
    pipeline)
        pytest tests/test_pipeline.py -v -s
        ;;
    repository)
        pytest tests/test_repository.py -v
        ;;
    command)
        pytest tests/test_command_handler.py -v
        ;;
    summary)
        pytest tests/test_summary_svc.py -v
        ;;
    all)
        pytest tests/ -v
        ;;
    *)
        echo "未知模块: $MODULE"
        exit 1
        ;;
esac

