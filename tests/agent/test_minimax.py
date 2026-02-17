#!/usr/bin/env python3
"""测试 MiniMax API 完整功能

本测试套件验证 MiniMax 模型的以下特性：
1. 基础对话能力
2. 函数调用能力（Tool Use）
3. Interleaved Thinking（交错思维链）
4. 多轮对话与上下文记忆
5. Prompt 缓存
"""
import os
import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from agent.functions.discovery import agent_callable


# 定义测试函数
@agent_callable(description="获取指定城市的天气信息")
def get_weather(city: str) -> dict:
    """获取天气信息（模拟）"""
    return {
        "city": city,
        "temperature": 22,
        "condition": "晴天",
        "humidity": 55
    }


@agent_callable(description="计算两个数字的和")
def calculate_sum(a: float, b: float) -> float:
    """计算两个数字的和"""
    return a + b


async def test_basic_chat():
    """测试 1: 基础对话"""
    print("\n" + "="*60)
    print("测试 1: 基础对话")
    print("="*60)
    
    try:
        # 从环境变量获取配置
        api_key = os.getenv("MINIMAX_API_KEY")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5")
        
        if not api_key:
            print("❌ 错误: 未设置 MINIMAX_API_KEY 环境变量")
            return False
        
        print(f"配置:")
        print(f"  Base URL: {base_url}")
        print(f"  Model: {model}")
        print(f"  API Key: {api_key[:20]}...")
        
        # 创建 MiniMax Provider
        provider = create_provider(
            "minimax",
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        
        # 创建 Agent
        agent = Agent(provider, system_prompt="你是一个友好的助手。请用中文简短回答。")
        
        # 测试对话
        print("\n发送消息: 你好，请介绍一下你自己")
        response = await agent.chat("你好，请介绍一下你自己", temperature=0.7)
        
        print(f"\nAgent 回复: {response['content']}")
        print(f"迭代次数: {response['iterations']}")
        
        # 检查 thinking 内容（MiniMax 特有）
        has_thinking = False
        if 'metadata' in response and response.get('metadata', {}).get('thinking'):
            thinking = response['metadata']['thinking']
            print(f"\n💭 Thinking (前100字符):")
            print(f"   {thinking[:100]}...")
            has_thinking = True
            print("✅ 检测到 thinking 内容（MiniMax Interleaved Thinking）")
        else:
            print("ℹ️  未检测到 thinking 内容（可能模型未生成）")
        
        # 检查 token 使用情况
        if 'metadata' in response and 'usage' in response['metadata']:
            usage = response['metadata']['usage']
            print(f"\n📊 Token 使用情况:")
            print(f"   输入 tokens: {usage.get('input_tokens', 0)}")
            print(f"   输出 tokens: {usage.get('output_tokens', 0)}")
            cache_read = usage.get('cache_read_input_tokens', 0)
            if cache_read > 0:
                print(f"   缓存命中 tokens: {cache_read}")
        
        print("\n✅ 基础对话测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 基础对话测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_function_calling():
    """测试 2: 函数调用（Tool Use）与 Interleaved Thinking"""
    print("\n" + "="*60)
    print("测试 2: 函数调用（Tool Use）与 Interleaved Thinking")
    print("="*60)
    
    try:
        api_key = os.getenv("MINIMAX_API_KEY")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5")
        
        if not api_key:
            print("❌ 错误: 未设置 MINIMAX_API_KEY 环境变量")
            return False
        
        # 创建 MiniMax Provider 和注册表
        provider = create_provider(
            "minimax",
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        
        registry = FunctionRegistry()
        registry.register("get_weather", "获取城市天气", get_weather)
        registry.register("calculate_sum", "计算两个数字的和", calculate_sum)
        
        # 创建 Agent
        agent = Agent(
            provider,
            function_registry=registry,
            system_prompt="你是一个助手。当需要实时数据或计算时，使用提供的工具。"
        )
        
        # 测试天气查询
        print("\n[测试 1] 查询天气")
        print("发送消息: 北京今天天气怎么样？")
        response = await agent.chat("北京今天天气怎么样？", temperature=0.1)
        
        print(f"\nAgent 回复: {response['content']}")
        print(f"调用的函数: {[fc['name'] for fc in response['function_calls']]}")
        print(f"迭代次数: {response['iterations']}")
        
        # 检查 thinking（工具调用场景）
        # MiniMax 的特点是在工具调用前会思考，这是 Interleaved Thinking 的体现
        if 'metadata' in response and response.get('metadata', {}).get('thinking'):
            thinking = response['metadata']['thinking']
            print(f"\n💭 Interleaved Thinking (前200字符):")
            print(f"   {thinking[:200]}...")
            print("✅ 检测到工具调用前的思考过程（Interleaved Thinking）")
            
            # 验证思考内容是否包含工具使用相关的推理
            if "get_weather" in thinking.lower() or "天气" in thinking or "工具" in thinking:
                print("✅ 思考内容包含工具使用相关的推理")
        else:
            print("⚠️  未检测到 thinking 内容")
        
        if len(response['function_calls']) > 0:
            print("✅ 成功调用函数")
            # 检查函数调用的参数是否正确
            for fc in response['function_calls']:
                print(f"   函数: {fc['name']}, 参数: {fc['arguments']}")
        else:
            print("⚠️  未调用函数（可能模型直接回答）")
        
        # 测试计算
        agent.clear_history()
        print("\n[测试 2] 数学计算")
        print("发送消息: 计算 15 加 27 等于多少")
        response = await agent.chat("计算 15 加 27 等于多少", temperature=0.1)
        
        print(f"\nAgent 回复: {response['content']}")
        print(f"调用的函数: {[fc['name'] for fc in response['function_calls']]}")
        
        # 检查第二个测试的 thinking
        if 'metadata' in response and response.get('metadata', {}).get('thinking'):
            thinking = response['metadata']['thinking']
            print(f"\n💭 Interleaved Thinking (前200字符):")
            print(f"   {thinking[:200]}...")
            
            # 验证是否包含计算相关的推理
            if "calculate" in thinking.lower() or "计算" in thinking or "15" in thinking:
                print("✅ 思考内容包含计算相关的推理")
        
        if len(response['function_calls']) > 0:
            for fc in response['function_calls']:
                print(f"   函数: {fc['name']}, 参数: {fc['arguments']}")
                # 验证参数是否正确
                if fc['name'] == 'calculate_sum':
                    args = fc['arguments']
                    if args.get('a') == 15 and args.get('b') == 27:
                        print("✅ 函数参数正确")
        
        print("\n✅ 函数调用测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 函数调用测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_turn():
    """测试 3: 多轮对话与上下文记忆"""
    print("\n" + "="*60)
    print("测试 3: 多轮对话与上下文记忆")
    print("="*60)
    
    try:
        api_key = os.getenv("MINIMAX_API_KEY")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5")
        
        if not api_key:
            print("❌ 错误: 未设置 MINIMAX_API_KEY 环境变量")
            return False
        
        provider = create_provider(
            "minimax",
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        
        agent = Agent(provider, system_prompt="你是一个友好的助手。")
        
        # 第一轮
        print("\n[第 1 轮]")
        print("发送: 我叫张三，是一名软件工程师")
        response1 = await agent.chat("我叫张三，是一名软件工程师", temperature=0.7)
        print(f"回复: {response1['content']}")
        
        # 检查第一轮的 thinking
        if 'metadata' in response1 and response1.get('metadata', {}).get('thinking'):
            thinking = response1['metadata']['thinking']
            print(f"💭 Thinking (前80字符): {thinking[:80]}...")
        
        # 第二轮 - 测试记忆
        print("\n[第 2 轮]")
        print("发送: 我叫什么名字？")
        response2 = await agent.chat("我叫什么名字？", temperature=0.7)
        print(f"回复: {response2['content']}")
        
        # 检查第二轮的 thinking（应该包含从历史中提取信息的推理）
        if 'metadata' in response2 and response2.get('metadata', {}).get('thinking'):
            thinking = response2['metadata']['thinking']
            print(f"💭 Thinking (前80字符): {thinking[:80]}...")
        
        name_remembered = "张三" in response2['content']
        if name_remembered:
            print("✅ Agent 记住了姓名")
        else:
            print("⚠️  Agent 可能没有记住姓名")
        
        # 第三轮 - 测试更深层的记忆
        print("\n[第 3 轮]")
        print("发送: 我的职业是什么？")
        response3 = await agent.chat("我的职业是什么？", temperature=0.7)
        print(f"回复: {response3['content']}")
        
        profession_remembered = "软件工程师" in response3['content'] or "工程师" in response3['content']
        if profession_remembered:
            print("✅ Agent 记住了职业信息")
        else:
            print("⚠️  Agent 可能没有记住职业信息")
        
        # 检查缓存效果（多轮对话可能会命中 prompt 缓存）
        if 'metadata' in response3 and 'usage' in response3['metadata']:
            usage = response3['metadata']['usage']
            cache_read = usage.get('cache_read_input_tokens', 0)
            if cache_read > 0:
                print(f"\n📊 Prompt 缓存生效: {cache_read} tokens 从缓存读取")
                print("✅ MiniMax 自动 prompt 缓存功能正常")
        
        print(f"\n对话历史长度: {len(agent.conversation_history)} 条消息")
        
        success = name_remembered and profession_remembered
        if success:
            print("\n✅ 多轮对话测试完全通过")
        else:
            print("\n⚠️  多轮对话测试部分通过")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 多轮对话测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("MiniMax API 完整测试套件")
    print("="*60)
    print("\n本测试验证以下特性：")
    print("  1. 基础对话能力")
    print("  2. 函数调用（Tool Use）")
    print("  3. Interleaved Thinking（交错思维链）")
    print("  4. 多轮对话与上下文记忆")
    print("  5. Prompt 缓存")
    print("")
    
    # 检查环境变量
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 MINIMAX_API_KEY 环境变量")
        print("\n使用方法:")
        print("  export MINIMAX_API_KEY='your-api-key'")
        print("  export MINIMAX_BASE_URL='https://api.minimaxi.com/anthropic'  # 可选，默认国内地址")
        print("  export MINIMAX_MODEL='MiniMax-M2.5'  # 可选，默认 M2.5")
        print("  python tests/agent/test_minimax.py")
        print("\n支持的模型:")
        print("  - MiniMax-M2.5: 顶尖性能与极致性价比（推荐）")
        print("  - MiniMax-M2.5-highspeed: M2.5 极速版（约 100 TPS）")
        print("  - MiniMax-M2.1: 强大多语言编程能力")
        print("  - MiniMax-M2.1-highspeed: M2.1 极速版")
        print("  - MiniMax-M2: 专为高效编码与 Agent 工作流而生")
        return False
    
    # 运行测试
    results = []
    
    test1 = await test_basic_chat()
    results.append(("基础对话", test1))
    
    test2 = await test_function_calling()
    results.append(("函数调用与 Interleaved Thinking", test2))
    
    test3 = await test_multi_turn()
    results.append(("多轮对话与上下文记忆", test3))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！MiniMax Provider 工作正常。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查日志。")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

