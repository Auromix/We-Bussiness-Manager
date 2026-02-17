"""测试 ToolExecutor 工具执行器。

覆盖：
- 执行同步 / 异步函数
- 默认参数
- 函数不存在 / 无实现 / 执行错误
- 结果格式化（None / str / dict / list / 不可序列化）
"""
import json
import pytest

from agent.functions.registry import FunctionRegistry, FunctionDefinition
from agent.functions.executor import ToolExecutor
from tests.agent.conftest import (
    sync_test_function,
    async_test_function,
    sample_function_no_params,
)


class TestToolExecutor:

    def test_init(self, function_registry):
        ex = ToolExecutor(function_registry)
        assert ex.registry is function_registry

    @pytest.mark.asyncio
    async def test_execute_sync(self, populated_registry):
        ex = ToolExecutor(populated_registry)
        result = await ex.execute(
            "sync_test_function", {"param1": "a", "param2": 5}
        )
        assert result == {"result": "a_5", "type": "sync"}

    @pytest.mark.asyncio
    async def test_execute_async(self, populated_registry):
        ex = ToolExecutor(populated_registry)
        result = await ex.execute(
            "async_test_function", {"param1": "b", "param2": 7}
        )
        assert result == {"result": "b_7", "type": "async"}

    @pytest.mark.asyncio
    async def test_execute_with_default(self, populated_registry):
        ex = ToolExecutor(populated_registry)
        result = await ex.execute("sync_test_function", {"param1": "c"})
        assert result == {"result": "c_10", "type": "sync"}

    @pytest.mark.asyncio
    async def test_execute_not_found(self, function_registry):
        ex = ToolExecutor(function_registry)
        with pytest.raises(ValueError, match="not found"):
            await ex.execute("nope", {})

    @pytest.mark.asyncio
    async def test_execute_no_implementation(self, function_registry):
        function_registry._functions["bad"] = FunctionDefinition(
            name="bad", description="d",
            parameters={"type": "object", "properties": {}},
            func=None,
        )
        ex = ToolExecutor(function_registry)
        with pytest.raises(ValueError, match="no implementation"):
            await ex.execute("bad", {})

    @pytest.mark.asyncio
    async def test_execute_error(self, function_registry):
        def boom(x: str):
            raise RuntimeError("boom")

        function_registry.register("boom", "d", boom)
        ex = ToolExecutor(function_registry)
        with pytest.raises(RuntimeError, match="boom"):
            await ex.execute("boom", {"x": "1"})

    # ---- format_result ----

    def test_format_none(self, function_registry):
        ex = ToolExecutor(function_registry)
        assert ex.format_result(None) == "执行成功"

    def test_format_string(self, function_registry):
        ex = ToolExecutor(function_registry)
        assert ex.format_result("hello") == "hello"

    def test_format_dict(self, function_registry):
        ex = ToolExecutor(function_registry)
        data = {"k": "v", "n": 1}
        assert json.loads(ex.format_result(data)) == data

    def test_format_list(self, function_registry):
        ex = ToolExecutor(function_registry)
        data = [{"a": 1}, {"b": 2}]
        assert json.loads(ex.format_result(data)) == data

    def test_format_non_serializable(self, function_registry):
        ex = ToolExecutor(function_registry)

        class Obj:
            def __str__(self):
                return "Obj!"

        assert "Obj!" in ex.format_result(Obj())

    @pytest.mark.asyncio
    async def test_execute_and_format(self, populated_registry):
        ex = ToolExecutor(populated_registry)
        result = await ex.execute(
            "sync_test_function", {"param1": "z", "param2": 99}
        )
        formatted = ex.format_result(result)
        assert json.loads(formatted) == result
