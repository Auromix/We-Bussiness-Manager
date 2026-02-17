"""Provider 使用示例 - 不同 LLM 提供商

本示例展示如何使用不同的 LLM Provider：
1. OpenAI Provider（GPT 系列）
2. Claude Provider（Anthropic 系列）
3. MiniMax Provider（国内可用）
4. OpenSource Provider（兼容 OpenAI API 的开源模型）

运行方式：
    python examples/agent/provider_example.py
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


async def example_openai_provider():
    """示例：使用 OpenAI Provider"""
    logger.info("=" * 60)
    logger.info("示例 1: OpenAI Provider（GPT 系列）")
    logger.info("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    # 创建 OpenAI Provider
    logger.info("\n1️⃣ 创建 OpenAI Provider")
    logger.info("-" * 60)
    provider = create_provider(
        "openai",
        api_key=api_key,
        model="gpt-4o-mini"  # 使用较便宜的模型
    )
    logger.info(f"✅ Provider 已创建")
    logger.info(f"   模型: {provider.model_name}")
    logger.info(f"   支持函数调用: {provider.supports_function_calling()}")

    # 创建 Agent 并对话
    logger.info("\n2️⃣ 使用 OpenAI Provider 进行对话")
    logger.info("-" * 60)
    agent = Agent(
        provider,
        system_prompt="你是一个友好的助手，擅长用简洁明了的方式回答问题。"
    )

    logger.info("用户: 用一句话介绍 Python")
    response = await agent.chat("用一句话介绍 Python")
    logger.info(f"助手: {response['content']}")
    logger.info(f"迭代次数: {response['iterations']}")

    logger.info("")


async def example_claude_provider():
    """示例：使用 Claude Provider"""
    logger.info("=" * 60)
    logger.info("示例 2: Claude Provider（Anthropic 系列）")
    logger.info("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("未设置 ANTHROPIC_API_KEY 环境变量，跳过此示例")
        return

    # 创建 Claude Provider
    logger.info("\n1️⃣ 创建 Claude Provider")
    logger.info("-" * 60)
    provider = create_provider("claude", api_key=api_key)
    logger.info(f"✅ Provider 已创建")
    logger.info(f"   模型: {provider.model_name}")
    logger.info(f"   支持函数调用: {provider.supports_function_calling()}")

    # 创建 Agent 并对话
    logger.info("\n2️⃣ 使用 Claude Provider 进行对话")
    logger.info("-" * 60)
    agent = Agent(
        provider,
        system_prompt="你是一个专业的编程助手，擅长解释技术概念。"
    )

    logger.info("用户: 解释一下异步编程的概念")
    response = await agent.chat("解释一下异步编程的概念")
    logger.info(f"助手: {response['content'][:300]}...")  # 只显示前300个字符
    logger.info(f"迭代次数: {response['iterations']}")

    logger.info("")


async def example_minimax_provider():
    """示例：使用 MiniMax Provider"""
    logger.info("=" * 60)
    logger.info("示例 3: MiniMax Provider（国内可用）")
    logger.info("=" * 60)

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        logger.warning("未设置 MINIMAX_API_KEY 环境变量，跳过此示例")
        return

    # 创建 MiniMax Provider
    logger.info("\n1️⃣ 创建 MiniMax Provider")
    logger.info("-" * 60)
    provider = create_provider(
        "minimax",
        api_key=api_key,
        model="MiniMax-M2.5"  # 或 MiniMax-M2.5-highspeed
    )
    logger.info(f"✅ Provider 已创建")
    logger.info(f"   模型: {provider.model_name}")
    logger.info(f"   支持函数调用: {provider.supports_function_calling()}")

    # 创建 Agent 并对话
    logger.info("\n2️⃣ 使用 MiniMax Provider 进行对话")
    logger.info("-" * 60)
    agent = Agent(
        provider,
        system_prompt="你是一个友好的助手。"
    )

    logger.info("用户: 你好")
    response = await agent.chat("你好")
    logger.info(f"助手: {response['content']}")
    logger.info(f"迭代次数: {response['iterations']}")

    logger.info("")


async def example_open_source_provider():
    """示例：使用 OpenSource Provider"""
    logger.info("=" * 60)
    logger.info("示例 4: OpenSource Provider（兼容 OpenAI API）")
    logger.info("=" * 60)

    # 从环境变量获取配置
    base_url = os.getenv("OPEN_SOURCE_BASE_URL", "http://localhost:8000/v1")
    model = os.getenv("OPEN_SOURCE_MODEL", "qwen")
    api_key = os.getenv("OPEN_SOURCE_API_KEY")

    logger.info(f"\n1️⃣ 创建 OpenSource Provider")
    logger.info("-" * 60)
    logger.info(f"   API 地址: {base_url}")
    logger.info(f"   模型: {model}")
    logger.info(f"   API Key: {'已设置' if api_key else '未设置'}")

    try:
        provider = create_provider(
            "open_source",
            base_url=base_url,
            model=model,
            api_key=api_key
        )
        logger.info(f"✅ Provider 已创建")
        logger.info(f"   模型: {provider.model_name}")
        logger.info(f"   支持函数调用: {provider.supports_function_calling()}")

        # 创建 Agent 并对话
        logger.info("\n2️⃣ 使用 OpenSource Provider 进行对话")
        logger.info("-" * 60)
        agent = Agent(
            provider,
            system_prompt="你是一个有用的助手。"
        )

        logger.info("用户: 你好")
        response = await agent.chat("你好")
        logger.info(f"助手: {response['content']}")
        logger.info(f"迭代次数: {response['iterations']}")

    except Exception as e:
        logger.error(f"调用开源模型失败: {e}")
        logger.info("提示: 请确保本地模型服务正在运行")
        logger.info("   - vLLM: 启动 vLLM 服务")
        logger.info("   - Ollama: 启动 Ollama 服务")
        logger.info("   - LocalAI: 启动 LocalAI 服务")

    logger.info("")


async def example_switch_provider():
    """示例：切换不同的 Provider"""
    logger.info("=" * 60)
    logger.info("示例 5: 切换不同的 Provider（代码无需修改）")
    logger.info("=" * 60)

    # 尝试使用不同的 Provider
    providers_to_try = []

    # 尝试 OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
            providers_to_try.append(("OpenAI", provider))
        except Exception as e:
            logger.warning(f"创建 OpenAI Provider 失败: {e}")

    # 尝试 Claude
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            provider = create_provider("claude", api_key=api_key)
            providers_to_try.append(("Claude", provider))
        except Exception as e:
            logger.warning(f"创建 Claude Provider 失败: {e}")

    # 尝试 MiniMax
    api_key = os.getenv("MINIMAX_API_KEY")
    if api_key:
        try:
            provider = create_provider("minimax", api_key=api_key, model="MiniMax-M2.5")
            providers_to_try.append(("MiniMax", provider))
        except Exception as e:
            logger.warning(f"创建 MiniMax Provider 失败: {e}")

    if not providers_to_try:
        logger.warning("没有可用的 Provider，请设置相应的 API Key")
        return

    # 使用不同的 Provider 进行相同的对话
    logger.info("\n使用不同的 Provider 进行相同的对话:")
    logger.info("-" * 60)

    for provider_name, provider in providers_to_try:
        logger.info(f"\n使用 {provider_name} Provider:")
        agent = Agent(provider, system_prompt="你是一个助手。")
        response = await agent.chat("用一句话介绍 Python")
        logger.info(f"  回复: {response['content'][:100]}...")
        logger.info(f"  模型: {provider.model_name}")

    logger.info("\n💡 关键点: Agent 代码完全相同，只需更换 Provider！")

    logger.info("")


async def example_provider_features():
    """示例：不同 Provider 的特性"""
    logger.info("=" * 60)
    logger.info("示例 6: 不同 Provider 的特性对比")
    logger.info("=" * 60)

    logger.info("\nProvider 特性对比:")
    logger.info("-" * 60)
    logger.info("""
    | Provider   | 模型示例                    | 函数调用 | 国内可用 | 特点                    |
    |------------|----------------------------|---------|---------|------------------------|
    | OpenAI     | gpt-4o-mini, gpt-4o        | ✅      | ❌      | 稳定、功能完整          |
    | Claude     | claude-sonnet-4            | ✅      | ❌      | 高质量回复、长上下文    |
    | MiniMax    | MiniMax-M2.5               | ✅      | ✅      | 国内可用、支持思考链    |
    | OpenSource | qwen, llama, mistral       | ✅      | ✅      | 本地部署、成本低        |
    """)

    logger.info("")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Agent 模块 - Provider 使用示例")
    logger.info("=" * 60)
    logger.info("")
    logger.info("提示: 请确保设置了相应的 API Key 环境变量")
    logger.info("  - OPENAI_API_KEY: OpenAI API Key")
    logger.info("  - ANTHROPIC_API_KEY: Anthropic API Key")
    logger.info("  - MINIMAX_API_KEY: MiniMax API Key")
    logger.info("  - OPEN_SOURCE_BASE_URL: 开源模型 API 地址（可选）")
    logger.info("  - OPEN_SOURCE_MODEL: 开源模型名称（可选）")
    logger.info("")

    try:
        # 运行各个示例
        await example_openai_provider()
        await example_claude_provider()
        await example_minimax_provider()
        await example_open_source_provider()
        await example_switch_provider()
        await example_provider_features()

        logger.info("=" * 60)
        logger.info("✅ Provider 使用示例完成！")
        logger.info("=" * 60)
        logger.info("")
        logger.info("💡 关键要点:")
        logger.info("   1. 所有 Provider 都实现 LLMProvider 接口，使用方式统一")
        logger.info("   2. 切换 Provider 只需更换 create_provider() 的参数")
        logger.info("   3. Agent 代码无需修改，完全透明")
        logger.info("   4. 根据需求选择合适的 Provider（成本、性能、可用性）")

    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

