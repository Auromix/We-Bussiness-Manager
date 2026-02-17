#!/usr/bin/env python3
"""MiniMax Provider 使用示例

本示例展示如何使用 MiniMax Provider 进行：
1. 基础对话
2. 函数调用（Tool Use）
3. Interleaved Thinking
4. 多轮对话
"""
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from agent.functions.discovery import agent_callable


# 定义工具函数
@agent_callable(description="获取指定城市的天气信息")
def get_weather(city: str) -> dict:
    """获取天气信息（模拟）"""
    # 这里是模拟数据，实际应用中应该调用真实的天气 API
    weather_data = {
        "北京": {"temperature": 22, "condition": "晴天", "humidity": 55},
        "上海": {"temperature": 25, "condition": "多云", "humidity": 70},
        "深圳": {"temperature": 28, "condition": "小雨", "humidity": 85},
    }
    
    city_weather = weather_data.get(city, {"temperature": 20, "condition": "未知", "humidity": 60})
    return {
        "city": city,
        **city_weather
    }


@agent_callable(description="计算两个数字的和")
def calculate_sum(a: float, b: float) -> float:
    """计算两个数字的和"""
    return a + b


@agent_callable(description="搜索并返回相关信息")
def search_info(query: str) -> str:
    """搜索信息（模拟）"""
    # 模拟搜索结果
    results = {
        "Python": "Python 是一种广泛使用的高级编程语言，以其简洁的语法和强大的功能而闻名。",
        "AI": "人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。",
        "MiniMax": "MiniMax 是一家 AI 公司，提供先进的大语言模型服务。",
    }
    
    for key, value in results.items():
        if key.lower() in query.lower():
            return value
    
    return f"关于 '{query}' 的搜索结果：暂无相关信息。"


async def example_1_basic_chat():
    """示例 1: 基础对话"""
    print("\n" + "="*60)
    print("示例 1: 基础对话")
    print("="*60)
    
    # 从环境变量获取 API Key
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置 MINIMAX_API_KEY 环境变量")
        return
    
    # 创建 Provider
    provider = create_provider(
        "minimax",
        api_key=api_key,
        model="MiniMax-M2.5"
    )
    
    # 创建 Agent
    agent = Agent(provider, system_prompt="你是一个友好、专业的助手。请用中文简洁回答。")
    
    # 发送消息
    print("\n用户: Python 的主要特点是什么？")
    response = await agent.chat("Python 的主要特点是什么？")
    
    print(f"\nAgent: {response['content']}")
    
    # 检查 thinking 内容
    if 'metadata' in response and response.get('metadata', {}).get('thinking'):
        print(f"\n💭 模型思考过程:\n{response['metadata']['thinking'][:200]}...")
    
    # Token 使用情况
    if 'metadata' in response and 'usage' in response['metadata']:
        usage = response['metadata']['usage']
        print(f"\n📊 Token 使用: 输入 {usage['input_tokens']}, 输出 {usage['output_tokens']}")


async def example_2_function_calling():
    """示例 2: 函数调用与 Interleaved Thinking"""
    print("\n" + "="*60)
    print("示例 2: 函数调用与 Interleaved Thinking")
    print("="*60)
    
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置 MINIMAX_API_KEY 环境变量")
        return
    
    # 创建 Provider
    provider = create_provider(
        "minimax",
        api_key=api_key,
        model="MiniMax-M2.5"
    )
    
    # 注册函数
    registry = FunctionRegistry()
    registry.register("get_weather", "获取城市天气", get_weather)
    registry.register("calculate_sum", "计算两个数字的和", calculate_sum)
    registry.register("search_info", "搜索信息", search_info)
    
    # 创建 Agent
    agent = Agent(
        provider,
        function_registry=registry,
        system_prompt="你是一个助手。当需要实时数据、计算或搜索时，使用提供的工具。"
    )
    
    # 测试 1: 天气查询
    print("\n[测试 1] 天气查询")
    print("用户: 上海今天天气怎么样？")
    response = await agent.chat("上海今天天气怎么样？", temperature=0.1)
    
    print(f"\nAgent: {response['content']}")
    print(f"📞 调用的函数: {[fc['name'] for fc in response['function_calls']]}")
    
    # 展示 Interleaved Thinking
    if 'metadata' in response and response.get('metadata', {}).get('thinking'):
        print(f"\n💭 工具调用前的思考:")
        print(response['metadata']['thinking'])
    
    # 测试 2: 计算
    agent.clear_history()
    print("\n[测试 2] 数学计算")
    print("用户: 帮我算一下 123 加 456")
    response = await agent.chat("帮我算一下 123 加 456", temperature=0.1)
    
    print(f"\nAgent: {response['content']}")
    print(f"📞 调用的函数: {[fc['name'] for fc in response['function_calls']]}")
    
    if 'metadata' in response and response.get('metadata', {}).get('thinking'):
        print(f"\n💭 思考过程:\n{response['metadata']['thinking']}")


async def example_3_multi_turn():
    """示例 3: 多轮对话"""
    print("\n" + "="*60)
    print("示例 3: 多轮对话")
    print("="*60)
    
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置 MINIMAX_API_KEY 环境变量")
        return
    
    provider = create_provider(
        "minimax",
        api_key=api_key,
        model="MiniMax-M2.5"
    )
    
    agent = Agent(provider, system_prompt="你是一个友好的助手。")
    
    # 第一轮
    print("\n[第 1 轮]")
    print("用户: 我喜欢编程，尤其是 Python")
    response = await agent.chat("我喜欢编程，尤其是 Python")
    print(f"Agent: {response['content']}")
    
    # 第二轮
    print("\n[第 2 轮]")
    print("用户: 我喜欢什么？")
    response = await agent.chat("我喜欢什么？")
    print(f"Agent: {response['content']}")
    
    # 第三轮
    print("\n[第 3 轮]")
    print("用户: 能推荐一些学习资源吗？")
    response = await agent.chat("能推荐一些学习资源吗？")
    print(f"Agent: {response['content']}")
    
    print(f"\n📝 对话历史: {len(agent.conversation_history)} 条消息")
    
    # 查看缓存效果
    if 'metadata' in response and 'usage' in response['metadata']:
        usage = response['metadata']['usage']
        cache_read = usage.get('cache_read_input_tokens', 0)
        if cache_read > 0:
            print(f"🚀 Prompt 缓存命中: {cache_read} tokens")


async def example_4_complex_task():
    """示例 4: 复杂任务（多步骤推理）"""
    print("\n" + "="*60)
    print("示例 4: 复杂任务（多步骤推理）")
    print("="*60)
    
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置 MINIMAX_API_KEY 环境变量")
        return
    
    provider = create_provider(
        "minimax",
        api_key=api_key,
        model="MiniMax-M2.5"
    )
    
    # 注册函数
    registry = FunctionRegistry()
    registry.register("get_weather", "获取城市天气", get_weather)
    registry.register("calculate_sum", "计算两个数字的和", calculate_sum)
    registry.register("search_info", "搜索信息", search_info)
    
    agent = Agent(
        provider,
        function_registry=registry,
        system_prompt="""你是一个智能助手，擅长解决复杂问题。
当遇到复杂任务时，请：
1. 分析问题
2. 确定需要使用的工具
3. 逐步执行
4. 综合结果给出答案"""
    )
    
    print("\n用户: 请帮我查一下北京和上海的天气，然后告诉我它们的平均温度是多少")
    response = await agent.chat(
        "请帮我查一下北京和上海的天气，然后告诉我它们的平均温度是多少",
        temperature=0.1
    )
    
    print(f"\nAgent: {response['content']}")
    print(f"\n📊 执行统计:")
    print(f"  - 迭代次数: {response['iterations']}")
    print(f"  - 调用的函数: {[fc['name'] for fc in response['function_calls']]}")
    
    # 展示完整的思考过程
    if 'metadata' in response and response.get('metadata', {}).get('thinking'):
        print(f"\n💭 完整思考过程:")
        print(response['metadata']['thinking'])


async def main():
    """主函数"""
    print("="*60)
    print("MiniMax Provider 使用示例")
    print("="*60)
    
    # 检查环境变量
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("\n❌ 错误: 未设置 MINIMAX_API_KEY 环境变量")
        print("\n使用方法:")
        print("  export MINIMAX_API_KEY='your-api-key'")
        print("  python examples/minimax_example.py")
        return
    
    print(f"\n✅ API Key 已设置: {api_key[:20]}...")
    print("\n运行示例...")
    
    try:
        # 运行各个示例
        await example_1_basic_chat()
        await example_2_function_calling()
        await example_3_multi_turn()
        await example_4_complex_task()
        
        print("\n" + "="*60)
        print("✅ 所有示例运行完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

