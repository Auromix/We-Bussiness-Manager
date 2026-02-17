#!/usr/bin/env python3
"""验证 MiniMax 集成是否正确

快速测试脚本，验证所有关键功能。
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def verify_imports():
    """验证必要的导入"""
    print("1️⃣  验证导入...")
    try:
        from agent import Agent, create_provider
        from agent.functions.registry import FunctionRegistry
        from agent.functions.discovery import agent_callable
        print("   ✅ 所有必要的模块都可以导入")
        return True
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False


def verify_provider_creation():
    """验证 Provider 创建"""
    print("\n2️⃣  验证 Provider 创建...")
    try:
        from agent import create_provider
        
        # 使用假的 API key 测试创建（不会实际调用 API）
        provider = create_provider(
            "claude",
            api_key="test-key",
            model="MiniMax-M2.5",
            base_url="https://api.minimaxi.com/anthropic"
        )
        
        print(f"   ✅ Provider 创建成功: {provider.model_name}")
        print(f"   ✅ 支持函数调用: {provider.supports_function_calling()}")
        return True
    except Exception as e:
        print(f"   ❌ Provider 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_thinking_support():
    """验证 Thinking 支持"""
    print("\n3️⃣  验证 Thinking 支持...")
    try:
        from agent.providers.claude_provider import ClaudeProvider
        import inspect
        
        # 检查 chat 方法的实现
        source = inspect.getsource(ClaudeProvider.chat)
        
        checks = {
            "thinking 提取": '"thinking"' in source and 'content_block.thinking' in source,
            "metadata 存储": 'metadata["thinking"]' in source,
            "thinking 日志": 'thinking' in source.lower()
        }
        
        all_passed = all(checks.values())
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        return all_passed
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False


def verify_function_registry():
    """验证函数注册"""
    print("\n4️⃣  验证函数注册...")
    try:
        from agent.functions.registry import FunctionRegistry
        from agent.functions.discovery import agent_callable
        
        # 定义测试函数
        @agent_callable(description="测试函数")
        def test_func(x: int) -> int:
            return x * 2
        
        # 注册
        registry = FunctionRegistry()
        registry.register("test_func", "测试", test_func)
        
        # 验证
        specs = registry.get_function_specs()
        assert len(specs) == 1
        assert specs[0]["name"] == "test_func"
        
        print("   ✅ 函数注册成功")
        print(f"   ✅ 函数规范生成: {specs[0]['name']}")
        return True
    except Exception as e:
        print(f"   ❌ 函数注册失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_documentation():
    """验证文档存在"""
    print("\n5️⃣  验证文档...")
    
    docs = {
        "最佳实践": "docs/MINIMAX_BEST_PRACTICES.md",
        "快速入门": "docs/MINIMAX_QUICKSTART.md",
        "完整示例": "examples/agent/minimax_interleaved_thinking_demo.py",
        "基础示例": "examples/agent/minimax_example.py",
        "测试脚本": "tests/agent/test_minimax.py",
        "集成报告": "MINIMAX_INTEGRATION_COMPLETE.md"
    }
    
    all_exist = True
    for name, path in docs.items():
        full_path = project_root / path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {path}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_example_code_syntax():
    """验证示例代码语法"""
    print("\n6️⃣  验证示例代码语法...")
    
    examples = [
        "examples/agent/minimax_example.py",
        "examples/agent/minimax_interleaved_thinking_demo.py",
    ]
    
    all_valid = True
    for example in examples:
        try:
            example_path = project_root / example
            with open(example_path, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, example, 'exec')
            print(f"   ✅ {example}")
        except SyntaxError as e:
            print(f"   ❌ {example}: {e}")
            all_valid = False
    
    return all_valid


def print_summary(results):
    """打印总结"""
    print("\n" + "="*70)
    print("验证总结")
    print("="*70)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有验证通过！MiniMax 集成已完成。")
        print("\n下一步:")
        print("  1. 设置 API Key: export MINIMAX_API_KEY='your-key'")
        print("  2. 运行测试: python tests/agent/test_minimax.py")
        print("  3. 运行示例: python examples/agent/minimax_example.py")
        print("  4. 阅读文档: docs/MINIMAX_BEST_PRACTICES.md")
    else:
        print("\n⚠️  部分验证失败，请检查上述错误。")
    
    print("="*70)


def main():
    """主函数"""
    print("="*70)
    print("MiniMax 集成验证")
    print("="*70)
    print("\n本脚本验证 MiniMax 集成的完整性，不会调用实际的 API。\n")
    
    results = {
        "导入检查": verify_imports(),
        "Provider 创建": verify_provider_creation(),
        "Thinking 支持": verify_thinking_support(),
        "函数注册": verify_function_registry(),
        "文档完整性": verify_documentation(),
        "代码语法": verify_example_code_syntax(),
    }
    
    print_summary(results)
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

