"""Agent 基础使用示例

本示例展示如何使用 Agent 进行基础的对话功能，包括：
1. 创建不同的 LLM 提供商（OpenAI、Claude、开源模型）
2. 创建 Agent 实例
3. 进行单轮和多轮对话
4. 管理对话历史

运行方式：
    python examples/agent/basic_example.py
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


async def example_openai():
    """示例：使用 OpenAI 提供商"""
    logger.info("=" * 60)
    logger.info("示例 1: 使用 OpenAI 提供商")
    logger.info("=" * 60)
    
    # 从环境变量获取 API Key（如果没有设置，会使用 None，实际使用时需要设置）
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    # 创建 OpenAI 提供商
    provider = create_provider(
        "openai",
        api_key=api_key,
        model="gpt-4o-mini"  # 使用较便宜的模型
    )
    
    # 创建 Agent
    agent = Agent(
        provider,
        system_prompt="你是一个友好的助手，擅长用简洁明了的方式回答问题。"
    )
    
    # 进行对话
    logger.info("\n用户: 什么是 Python？")
    response = await agent.chat("什么是 Python？")
    logger.info(f"助手: {response['content']}")
    
    # 继续对话（多轮对话）
    logger.info("\n用户: 它有什么特点？")
    response = await agent.chat("它有什么特点？")
    logger.info(f"助手: {response['content']}")
    
    # 查看对话历史
    logger.info(f"\n对话历史包含 {len(agent.conversation_history)} 条消息")
    
    # 清空对话历史
    agent.clear_history()
    logger.info("已清空对话历史")
    logger.info("")


async def example_claude():
    """示例：使用 Claude 提供商"""
    logger.info("=" * 60)
    logger.info("示例 2: 使用 Claude 提供商")
    logger.info("=" * 60)
    
    # 从环境变量获取 API Key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("未设置 ANTHROPIC_API_KEY 环境变量，跳过此示例")
        return
    
    # 创建 Claude 提供商
    provider = create_provider(
        "claude",
        api_key=api_key,
        model="claude-sonnet-4-20250514"
    )
    
    # 创建 Agent
    agent = Agent(
        provider,
        system_prompt="你是一个专业的编程助手，擅长解释技术概念。"
    )
    
    # 进行对话
    logger.info("\n用户: 解释一下异步编程的概念")
    response = await agent.chat("解释一下异步编程的概念")
    logger.info(f"助手: {response['content'][:200]}...")  # 只显示前200个字符
    
    logger.info("")


async def example_open_source():
    """示例：使用开源模型提供商"""
    logger.info("=" * 60)
    logger.info("示例 3: 使用开源模型提供商")
    logger.info("=" * 60)
    
    # 从环境变量获取配置
    base_url = os.getenv("OPEN_SOURCE_BASE_URL", "http://localhost:8000/v1")
    model = os.getenv("OPEN_SOURCE_MODEL", "qwen")
    api_key = os.getenv("OPEN_SOURCE_API_KEY")
    
    logger.info(f"使用开源模型: {model}")
    logger.info(f"API 地址: {base_url}")
    
    # 创建开源模型提供商
    provider = create_provider(
        "open_source",
        base_url=base_url,
        model=model,
        api_key=api_key
    )
    
    # 创建 Agent
    agent = Agent(
        provider,
        system_prompt="你是一个有用的助手。"
    )
    
    try:
        # 进行对话
        logger.info("\n用户: 你好")
        response = await agent.chat("你好")
        logger.info(f"助手: {response['content']}")
    except Exception as e:
        logger.error(f"调用开源模型失败: {e}")
        logger.info("提示: 请确保本地模型服务正在运行")
    
    logger.info("")


async def example_conversation_history():
    """示例：管理对话历史"""
    logger.info("=" * 60)
    logger.info("示例 4: 管理对话历史")
    logger.info("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(provider, system_prompt="你是一个数学助手。")
    
    # 进行多轮对话
    logger.info("\n第一轮对话:")
    response = await agent.chat("2 + 2 等于多少？")
    logger.info(f"助手: {response['content']}")
    
    logger.info("\n第二轮对话:")
    response = await agent.chat("那 3 + 3 呢？")
    logger.info(f"助手: {response['content']}")
    
    logger.info("\n第三轮对话（利用上下文）:")
    response = await agent.chat("把这两个结果加起来")
    logger.info(f"助手: {response['content']}")
    
    # 查看对话历史
    logger.info(f"\n当前对话历史包含 {len(agent.conversation_history)} 条消息:")
    for i, msg in enumerate(agent.conversation_history, 1):
        role = msg.role
        content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        logger.info(f"  {i}. [{role}]: {content}")
    
    # 清空历史
    agent.clear_history()
    logger.info("\n已清空对话历史，重新开始对话")
    
    response = await agent.chat("1 + 1 等于多少？")
    logger.info(f"助手: {response['content']}")
    
    logger.info("")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Agent 基础使用示例")
    logger.info("=" * 60)
    logger.info("")
    logger.info("提示: 请确保设置了相应的 API Key 环境变量")
    logger.info("  - OPENAI_API_KEY: OpenAI API Key")
    logger.info("  - ANTHROPIC_API_KEY: Anthropic API Key")
    logger.info("  - OPEN_SOURCE_BASE_URL: 开源模型 API 地址（可选）")
    logger.info("  - OPEN_SOURCE_MODEL: 开源模型名称（可选）")
    logger.info("")
    
    try:
        # 运行各个示例
        await example_openai()
        await example_claude()
        await example_open_source()
        await example_conversation_history()
        
        logger.info("=" * 60)
        logger.info("示例运行完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

