#!/usr/bin/env python3
"""调试健身房 Agent tool_use_id 问题"""
import os
import sys
import asyncio
from pathlib import Path
from loguru import logger

# 设置详细日志
logger.remove()
logger.add(sys.stdout, level="DEBUG", format="<level>{level: <8}</level> | <level>{message}</level>")

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from examples.gym_agent_manager import (
    init_database,
    record_service_income,
    open_membership_card
)


async def main():
    """主程序"""
    print("\n=== 初始化数据库 ===")
    init_database()
    
    # 创建 Agent
    api_key = os.getenv("MINIMAX_API_KEY")
    provider = create_provider("minimax", api_key=api_key, model="MiniMax-M2.5")
    
    registry = FunctionRegistry()
    registry.register("record_service_income", "记录服务收入", record_service_income)
    registry.register("open_membership_card", "开会员卡", open_membership_card)
    
    agent = Agent(
        provider,
        function_registry=registry,
        system_prompt="你是健身房管理助手。私教课提成40%。"
    )
    
    # 场景1
    print("\n=== 场景1: 记录私教课 ===")
    response1 = await agent.chat("今天张三上了李教练的私教课，收费300元", temperature=0.1)
    print(f"回复1: {response1['content'][:100]}")
    print(f"函数调用: {[fc['name'] for fc in response1['function_calls']]}")
    
    # 打印历史消息
    print(f"\n历史消息数量: {len(agent.conversation_history)}")
    for i, msg in enumerate(agent.conversation_history):
        print(f"  {i}: role={msg.role}, name={msg.name}, content_preview={str(msg.content)[:80]}")
    
    # 场景2
    print("\n=== 场景2: 开会员卡 ===")
    response2 = await agent.chat("李四开了一张年卡，充值3000元", temperature=0.1)
    print(f"回复2: {response2['content'][:100]}")
    print(f"函数调用: {[fc['name'] for fc in response2['function_calls']]}")


if __name__ == "__main__":
    asyncio.run(main())

