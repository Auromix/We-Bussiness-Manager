"""测试 ToolExecutor 工具执行器。

本模块测试工具执行器的所有功能，包括：
- 执行同步函数
- 执行异步函数
- 错误处理
- 结果格式化
"""
import pytest
import json
from typing import Dict, Any

from agent.functions.registry import FunctionRegistry
from agent.functions.executor import ToolExecutor
from tests.agent.conftest import (
    sync_test_function,
    async_test_function,
    sample_function_no_params
)


class TestToolExecutor:
    """ToolExecutor 测试类"""
    
    def test_init(self, function_registry):
        """测试初始化"""
        executor = ToolExecutor(function_registry)
        assert executor.registry == function_registry
    
    @pytest.mark.asyncio
    async def test_execute_sync_function(self, populated_registry):
        """测试执行同步函数"""
        executor = ToolExecutor(populated_registry)
        
        result = await executor.execute(
            "sync_test_function",
            {"param1": "test", "param2": 20}
        )
        
        assert result == {"result": "test_20", "type": "sync"}
    
    @pytest.mark.asyncio
    async def test_execute_async_function(self, populated_registry):
        """测试执行异步函数"""
        executor = ToolExecutor(populated_registry)
        
        result = await executor.execute(
            "async_test_function",
            {"param1": "test", "param2": 30}
        )
        
        assert result == {"result": "test_30", "type": "async"}
    
    @pytest.mark.asyncio
    async def test_execute_function_with_default(self, populated_registry):
        """测试执行带默认值的函数"""
        executor = ToolExecutor(populated_registry)
        
        # 不提供 param2，使用默认值
        result = await executor.execute(
            "sync_test_function",
            {"param1": "test"}
        )
        
        assert result == {"result": "test_10", "type": "sync"}  # 默认值是 10
    
    @pytest.mark.asyncio
    async def test_execute_function_not_found(self, function_registry):
        """测试执行不存在的函数"""
        executor = ToolExecutor(function_registry)
        
        with pytest.raises(ValueError, match="not found in registry"):
            await executor.execute("non_existent", {})
    
    @pytest.mark.asyncio
    async def test_execute_function_error(self, function_registry):
        """测试函数执行错误"""
        def error_function(param: str) -> str:
            raise ValueError("测试错误")
        
        function_registry.register(
            name="error_func",
            description="错误函数",
            func=error_function
        )
        
        executor = ToolExecutor(function_registry)
        
        with pytest.raises(ValueError, match="测试错误"):
            await executor.execute("error_func", {"param": "test"})
    
    @pytest.mark.asyncio
    async def test_execute_function_no_implementation(self, function_registry):
        """测试函数没有实现的情况"""
        from agent.functions.registry import FunctionDefinition
        
        # 创建一个没有实现的函数定义
        function_registry._functions["no_impl"] = FunctionDefinition(
            name="no_impl",
            description="无实现函数",
            parameters={"type": "object", "properties": {}},
            func=None  # 没有实现
        )
        
        executor = ToolExecutor(function_registry)
        
        with pytest.raises(ValueError, match="no implementation"):
            await executor.execute("no_impl", {})
    
    def test_format_result_none(self, function_registry):
        """测试格式化 None 结果"""
        executor = ToolExecutor(function_registry)
        result = executor.format_result(None)
        assert result == "执行成功"
    
    def test_format_result_string(self, function_registry):
        """测试格式化字符串结果"""
        executor = ToolExecutor(function_registry)
        result = executor.format_result("简单字符串")
        assert result == "简单字符串"
    
    def test_format_result_dict(self, function_registry):
        """测试格式化字典结果"""
        executor = ToolExecutor(function_registry)
        data = {"key1": "value1", "key2": 123, "key3": True}
        result = executor.format_result(data)
        
        # 应该是格式化的 JSON 字符串
        parsed = json.loads(result)
        assert parsed == data
        # 检查是否包含中文字符（ensure_ascii=False）
        assert "value1" in result
    
    def test_format_result_list(self, function_registry):
        """测试格式化列表结果"""
        executor = ToolExecutor(function_registry)
        data = [{"item1": "value1"}, {"item2": "value2"}]
        result = executor.format_result(data)
        
        parsed = json.loads(result)
        assert parsed == data
    
    def test_format_result_nested_structure(self, function_registry):
        """测试格式化嵌套结构"""
        executor = ToolExecutor(function_registry)
        data = {
            "users": [
                {"name": "张三", "age": 25},
                {"name": "李四", "age": 30}
            ],
            "total": 2
        }
        result = executor.format_result(data)
        
        parsed = json.loads(result)
        assert parsed == data
    
    def test_format_result_non_serializable(self, function_registry):
        """测试格式化不可序列化的对象"""
        executor = ToolExecutor(function_registry)
        
        class NonSerializable:
            def __str__(self):
                return "NonSerializable object"
        
        obj = NonSerializable()
        result = executor.format_result(obj)
        
        # 应该回退到 str() 转换
        assert "NonSerializable" in result
    
    @pytest.mark.asyncio
    async def test_execute_and_format(self, populated_registry):
        """测试执行并格式化结果"""
        executor = ToolExecutor(populated_registry)
        
        result = await executor.execute(
            "sync_test_function",
            {"param1": "test", "param2": 42}
        )
        
        formatted = executor.format_result(result)
        parsed = json.loads(formatted)
        assert parsed == result
    
    @pytest.mark.asyncio
    async def test_execute_with_extra_params(self, populated_registry):
        """测试执行时提供额外参数（应该导致错误）"""
        executor = ToolExecutor(populated_registry)
        
        # 提供额外的参数，函数不接受参数时会报错
        with pytest.raises(TypeError):
            await executor.execute(
                "sample_function_no_params",
                {"extra_param": "should_cause_error"}
            )

