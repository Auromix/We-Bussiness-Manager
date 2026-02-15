#!/bin/bash
# Agent 模块测试运行脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Agent 模块测试 ===${NC}\n"

# 检查是否使用真实 API
if [ "$AGENT_TEST_USE_REAL_API" = "true" ]; then
    echo -e "${YELLOW}警告: 将使用真实 API 进行测试，可能产生费用${NC}"
    echo "Provider: ${AGENT_TEST_PROVIDER_TYPE:-未设置}"
    echo "Model: ${AGENT_TEST_MODEL:-未设置}"
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
fi

# 运行测试
echo -e "${GREEN}运行测试...${NC}\n"

# 如果提供了测试文件或测试类，只运行指定的测试
if [ $# -gt 0 ]; then
    pytest tests/agent/"$@" -v
else
    # 运行所有测试
    pytest tests/agent/ -v
fi

echo -e "\n${GREEN}测试完成!${NC}"

