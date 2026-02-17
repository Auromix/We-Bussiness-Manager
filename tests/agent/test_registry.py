"""测试 FunctionRegistry 函数注册表。

覆盖：
- 初始化
- 注册（手动参数 / 自动推断 / 覆盖 / 异步函数）
- 类型推断（基本类型 / Optional / Union）
- 查询（get_function / has_function / list_functions）
- 批量注册
"""
import pytest
from typing import Dict, Any, Optional, Union

from agent.functions.registry import FunctionRegistry, FunctionDefinition
from tests.agent.conftest import (
    sync_test_function,
    async_test_function,
    sample_function_no_params,
    sample_function_with_optional,
)


class TestFunctionRegistry:

    def test_init_empty(self):
        r = FunctionRegistry()
        assert r._functions == {}
        assert r.list_functions() == []

    def test_register_simple(self, function_registry):
        function_registry.register(
            "fn", "描述", sync_test_function,
        )
        assert function_registry.has_function("fn")
        fd = function_registry.get_function("fn")
        assert fd.name == "fn"
        assert fd.description == "描述"
        assert fd.func is sync_test_function

    def test_register_with_custom_parameters(self, function_registry):
        schema = {
            "type": "object",
            "properties": {"p": {"type": "string"}},
            "required": ["p"],
        }
        function_registry.register("fn", "d", sync_test_function, schema)
        assert function_registry.get_function("fn").parameters is schema

    def test_auto_infer_parameters(self, function_registry):
        function_registry.register("fn", "d", sync_test_function)
        fd = function_registry.get_function("fn")
        props = fd.parameters["properties"]
        assert props["param1"]["type"] == "string"
        assert props["param2"]["type"] == "integer"
        assert "param1" in fd.parameters["required"]
        assert "param2" not in fd.parameters["required"]

    def test_register_overwrite(self, function_registry):
        function_registry.register("fn", "old", sync_test_function)
        function_registry.register("fn", "new", sample_function_no_params)
        fd = function_registry.get_function("fn")
        assert fd.description == "new"
        assert fd.func is sample_function_no_params

    def test_register_async(self, function_registry):
        function_registry.register("fn", "d", async_test_function)
        assert function_registry.get_function("fn").func is async_test_function

    def test_register_no_params(self, function_registry):
        function_registry.register("fn", "d", sample_function_no_params)
        fd = function_registry.get_function("fn")
        assert fd.parameters["properties"] == {}

    def test_register_optional_param(self, function_registry):
        function_registry.register("fn", "d", sample_function_with_optional)
        fd = function_registry.get_function("fn")
        assert "param1" in fd.parameters["required"]
        assert "param2" not in fd.parameters.get("required", [])

    def test_get_function_not_exists(self, function_registry):
        assert function_registry.get_function("nope") is None

    def test_has_function(self, populated_registry):
        assert populated_registry.has_function("sync_test_function")
        assert not populated_registry.has_function("nope")

    def test_list_functions(self, populated_registry):
        fns = populated_registry.list_functions()
        assert len(fns) == 4
        for f in fns:
            assert "name" in f
            assert "description" in f
            assert "parameters" in f

    def test_infer_complex_types(self, function_registry):
        def complex_fn(
            s: str, i: int, f: float, b: bool,
            l: list, d: dict, o: Optional[str] = None,
        ) -> Dict[str, Any]:
            return {}

        function_registry.register("fn", "d", complex_fn)
        props = function_registry.get_function("fn").parameters["properties"]
        assert props["s"]["type"] == "string"
        assert props["i"]["type"] == "integer"
        assert props["f"]["type"] == "number"
        assert props["b"]["type"] == "boolean"
        assert props["l"]["type"] == "array"
        assert props["d"]["type"] == "object"
        assert props["o"]["type"] == "string"

    def test_infer_union_type(self, function_registry):
        def fn(p: Union[str, int]) -> str:
            return ""

        function_registry.register("fn", "d", fn)
        t = function_registry.get_function("fn").parameters[
            "properties"
        ]["p"]["type"]
        assert t in ("string", "integer")

    def test_register_multiple(self, function_registry):
        for i in range(3):
            function_registry.register(
                f"fn{i}", f"d{i}", sync_test_function,
            )
        assert len(function_registry.list_functions()) == 3
