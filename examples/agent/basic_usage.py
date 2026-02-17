"""基础使用示例 - Agent 模块入门

本示例展示 Agent 的基本使用方法：
1. 创建不同的 LLM Provider
2. 创建 Agent 实例
3. 进行单轮和多轮对话
4. 管理对话历史

运行方式：
    python examples/agent/basic_usage.py
"""
import sys
import os
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent, create_provider
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


async def example_create_provider():
    """示例：创建不同的 Provider"""
    logger.info("=" * 60)
    logger.info("步骤 1: 创建 LLM Provider")
    logger.info("=" * 60)

    # 1.1 创建 OpenAI Provider
    logger.info("\n1️⃣ 创建 OpenAI Provider")
    logger.info("-" * 60)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            provider = create_provider(
                "openai",
                api_key=api_key,
                model="gpt-4o-mini"  # 使用较便宜的模型
            )
            logger.info(f"✅ OpenAI Provider 已创建")
            logger.info(f"   模型: {provider.model_name}")
            logger.info(f"   支持函数调用: {provider.supports_function_calling()}")
        except Exception as e:
            logger.warning(f"创建 OpenAI Provider 失败: {e}")
    else:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过 OpenAI 示例")

    # 1.2 创建 Claude Provider
    logger.info("\n2️⃣ 创建 Claude Provider")
    logger.info("-" * 60)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            provider = create_provider("claude", api_key=api_key)
            logger.info(f"✅ Claude Provider 已创建")
            logger.info(f"   模型: {provider.model_name}")
            logger.info(f"   支持函数调用: {provider.supports_function_calling()}")
        except Exception as e:
            logger.warning(f"创建 Claude Provider 失败: {e}")
    else:
        logger.warning("未设置 ANTHROPIC_API_KEY 环境变量，跳过 Claude 示例")

    # 1.3 创建 MiniMax Provider
    logger.info("\n3️⃣ 创建 MiniMax Provider")
    logger.info("-" * 60)
    api_key = os.getenv("MINIMAX_API_KEY")
    if api_key:
        try:
            provider = create_provider(
                "minimax",
                api_key=api_key,
                model="MiniMax-M2.5"
            )
            logger.info(f"✅ MiniMax Provider 已创建")
            logger.info(f"   模型: {provider.model_name}")
            logger.info(f"   支持函数调用: {provider.supports_function_calling()}")
        except Exception as e:
            logger.warning(f"创建 MiniMax Provider 失败: {e}")
    else:
        logger.warning("未设置 MINIMAX_API_KEY 环境变量，跳过 MiniMax 示例")

    logger.info("")


async def example_create_agent():
    """示例：创建 Agent 实例"""
    logger.info("=" * 60)
    logger.info("步骤 2: 创建 Agent 实例")
    logger.info("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    # 2.1 创建不带系统提示词的 Agent
    logger.info("\n1️⃣ 创建不带系统提示词的 Agent")
    logger.info("-" * 60)
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent1 = Agent(provider)
    logger.info(f"✅ Agent 已创建")
    logger.info(f"   对话历史长度: {len(agent1.conversation_history)}")
    logger.info(f"   系统提示词: {agent1.system_prompt}")

    # 2.2 创建带系统提示词的 Agent
    logger.info("\n2️⃣ 创建带系统提示词的 Agent")
    logger.info("-" * 60)
    agent2 = Agent(
        provider,
        system_prompt="你是一个友好的助手，擅长用简洁明了的方式回答问题。"
    )
    logger.info(f"✅ Agent 已创建")
    logger.info(f"   对话历史长度: {len(agent2.conversation_history)}")
    logger.info(f"   系统提示词: {agent2.system_prompt}")
    logger.info(f"   第一条消息角色: {agent2.conversation_history[0].role}")

    logger.info("")


async def example_single_turn_chat():
    """示例：单轮对话"""
    logger.info("=" * 60)
    logger.info("步骤 3: 单轮对话")
    logger.info("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(
        provider,
        system_prompt="你是一个友好的助手。"
    )

    # 3.1 简单对话
    logger.info("\n1️⃣ 简单对话")
    logger.info("-" * 60)
    logger.info("用户: 什么是 Python？")
    response = await agent.chat("什么是 Python？")
    logger.info(f"助手: {response['content'][:200]}...")  # 只显示前200个字符
    logger.info(f"迭代次数: {response['iterations']}")
    logger.info(f"函数调用次数: {len(response['function_calls'])}")

    # 3.2 查看对话历史
    logger.info("\n2️⃣ 查看对话历史")
    logger.info("-" * 60)
    logger.info(f"对话历史包含 {len(agent.conversation_history)} 条消息:")
    for i, msg in enumerate(agent.conversation_history, 1):
        role = msg.role
        content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        logger.info(f"  {i}. [{role}]: {content}")

    logger.info("")


async def example_multi_turn_chat():
    """示例：多轮对话"""
    logger.info("=" * 60)
    logger.info("步骤 4: 多轮对话（利用上下文）")
    logger.info("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(provider, system_prompt="你是一个数学助手。")

    # 第一轮对话
    logger.info("\n第一轮对话:")
    logger.info("用户: 2 + 2 等于多少？")
    response = await agent.chat("2 + 2 等于多少？")
    logger.info(f"助手: {response['content']}")

    # 第二轮对话（利用上下文）
    logger.info("\n第二轮对话:")
    logger.info("用户: 那 3 + 3 呢？")
    response = await agent.chat("那 3 + 3 呢？")
    logger.info(f"助手: {response['content']}")

    # 第三轮对话（继续利用上下文）
    logger.info("\n第三轮对话（利用上下文）:")
    logger.info("用户: 把这两个结果加起来")
    response = await agent.chat("把这两个结果加起来")
    logger.info(f"助手: {response['content']}")

    # 查看完整对话历史
    logger.info(f"\n当前对话历史包含 {len(agent.conversation_history)} 条消息:")
    for i, msg in enumerate(agent.conversation_history, 1):
        role = msg.role
        content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        logger.info(f"  {i}. [{role}]: {content}")

    logger.info("")


async def example_manage_history():
    """示例：管理对话历史"""
    logger.info("=" * 60)
    logger.info("步骤 5: 管理对话历史")
    logger.info("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(provider, system_prompt="你是一个助手。")

    # 进行几轮对话
    logger.info("\n进行几轮对话...")
    await agent.chat("你好")
    await agent.chat("我的名字是张三")
    await agent.chat("记住我的名字")
    logger.info(f"对话历史长度: {len(agent.conversation_history)}")

    # 清空对话历史
    logger.info("\n清空对话历史...")
    agent.clear_history()
    logger.info(f"清空后对话历史长度: {len(agent.conversation_history)}")
    logger.info(f"系统提示词是否保留: {agent.system_prompt is not None}")

    # 重新开始对话
    logger.info("\n重新开始对话:")
    response = await agent.chat("1 + 1 等于多少？")
    logger.info(f"助手: {response['content']}")
    logger.info(f"对话历史长度: {len(agent.conversation_history)}")

    logger.info("")


async def example_custom_parameters():
    """示例：传递自定义参数"""
    logger.info("=" * 60)
    logger.info("步骤 6: 传递自定义参数给 Provider")
    logger.info("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(provider, system_prompt="你是一个助手。")

    # 传递 temperature 参数
    logger.info("\n使用自定义 temperature 参数:")
    response = await agent.chat(
        "用一句话介绍 Python",
        temperature=0.9  # 更高的温度，回复更随机
    )
    logger.info(f"助手: {response['content']}")

    logger.info("")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Agent 模块 - 基础使用示例")
    logger.info("=" * 60)
    logger.info("")
    logger.info("提示: 请确保设置了相应的 API Key 环境变量")
    logger.info("  - OPENAI_API_KEY: OpenAI API Key")
    logger.info("  - ANTHROPIC_API_KEY: Anthropic API Key")
    logger.info("  - MINIMAX_API_KEY: MiniMax API Key")
    logger.info("")

    try:
        # 运行各个示例
        await example_create_provider()
        await example_create_agent()
        await example_single_turn_chat()
        await example_multi_turn_chat()
        await example_manage_history()
        await example_custom_parameters()

        logger.info("=" * 60)
        logger.info("✅ 基础使用示例完成！")
        logger.info("=" * 60)
        logger.info("")
        logger.info("💡 下一步:")
        logger.info("   - 运行 provider_example.py 了解不同 Provider 的使用")
        logger.info("   - 运行 function_calling_example.py 学习函数调用")
        logger.info("   - 阅读 design/agent.md 了解架构设计")

    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

