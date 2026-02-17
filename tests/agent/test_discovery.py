"""测试函数自动发现和注册机制。

覆盖：
- @agent_callable 装饰器
- register_instance_methods
- register_module_functions（含过滤）
- register_class_methods
- auto_discover_and_register
"""
import types
import asyncio
import pytest
from typing import Dict, Any

from agent.functions.registry import FunctionRegistry
from agent.functions.executor import ToolExecutor
from agent.functions.discovery import (
    agent_callable,
    register_instance_methods,
    register_module_functions,
    register_class_methods,
    auto_discover_and_register,
)
from tests.agent.conftest import SampleService


class TestAgentCallable:

    def test_basic(self):
        @agent_callable(description="测试")
        def fn(x: str) -> str:
            return x

        assert fn._agent_callable is True
        assert fn._agent_name == "fn"
        assert fn._agent_description == "测试"

    def test_custom_name(self):
        @agent_callable(name="custom", description="自定义")
        def fn():
            return ""

        assert fn._agent_name == "custom"

    def test_uses_docstring(self):
        @agent_callable()
        def fn():
            """文档字符串"""
            return ""

        assert fn._agent_description == "文档字符串"

    def test_default_description(self):
        @agent_callable()
        def fn():
            pass

        assert "调用 fn" in fn._agent_description

    def test_custom_parameters(self):
        schema = {"type": "object", "properties": {"p": {"type": "string"}}}

        @agent_callable(description="d", parameters=schema)
        def fn(p: str):
            return p

        assert fn._agent_parameters is schema


class TestRegisterInstanceMethods:

    def test_basic(self, function_registry, test_service):
        register_instance_methods(
            function_registry, test_service, prefix="svc_"
        )
        assert function_registry.has_function("svc_get_info")
        assert function_registry.has_function("svc_process_data")

    def test_default_prefix(self, function_registry, test_service):
        register_instance_methods(function_registry, test_service)
        assert function_registry.has_function("sampleservice_get_info")

    def test_skips_private(self, function_registry, test_service):
        register_instance_methods(
            function_registry, test_service, prefix="svc_"
        )
        assert not function_registry.has_function("svc__private_method")

    def test_skips_special(self, function_registry, test_service):
        register_instance_methods(
            function_registry, test_service, prefix="svc_"
        )
        assert not function_registry.has_function("svc___special_method__")

    def test_decorated_method(self, function_registry):
        class Svc:
            @agent_callable(name="custom_fn", description="自定义")
            def method(self):
                return "ok"

        register_instance_methods(
            function_registry, Svc(), prefix="svc_"
        )
        assert function_registry.has_function("custom_fn")
        assert not function_registry.has_function("svc_method")

    def test_execution(self, function_registry, test_service):
        register_instance_methods(
            function_registry, test_service, prefix="svc_"
        )
        ex = ToolExecutor(function_registry)
        result = asyncio.get_event_loop().run_until_complete(
            ex.execute("svc_get_info", {})
        )
        assert result == {"name": "test_service", "type": "service"}


class TestRegisterModuleFunctions:

    @staticmethod
    def _make_module():
        mod = types.ModuleType("test_mod")

        def func_a(x: str) -> str:
            """函数A"""
            return f"a_{x}"

        def func_b(x: int) -> int:
            """函数B"""
            return x + 1

        def _private():
            return "private"

        mod.func_a = func_a
        mod.func_b = func_b
        mod._private = _private
        return mod

    def test_basic(self, function_registry):
        mod = self._make_module()
        register_module_functions(function_registry, mod, prefix="m_")
        assert function_registry.has_function("m_func_a")
        assert function_registry.has_function("m_func_b")
        assert not function_registry.has_function("m__private")

    def test_with_filter(self, function_registry):
        mod = self._make_module()
        register_module_functions(
            function_registry, mod, prefix="m_",
            filter_func=lambda name, fn: name.startswith("func_a"),
        )
        assert function_registry.has_function("m_func_a")
        assert not function_registry.has_function("m_func_b")

    def test_decorated_module_function(self, function_registry):
        mod = types.ModuleType("test_mod")

        @agent_callable(name="custom_fn", description="自定义")
        def fn():
            return ""

        mod.fn = fn
        register_module_functions(function_registry, mod)
        assert function_registry.has_function("custom_fn")


class TestRegisterClassMethods:

    def test_with_instance(self, function_registry, test_service):
        register_class_methods(
            function_registry, SampleService,
            prefix="cls_", instance=test_service,
        )
        assert function_registry.has_function("cls_get_info")
        ex = ToolExecutor(function_registry)
        result = asyncio.get_event_loop().run_until_complete(
            ex.execute("cls_get_info", {})
        )
        assert result["name"] == "test_service"

    def test_without_instance(self, function_registry):
        register_class_methods(
            function_registry, SampleService, prefix="cls_"
        )
        assert function_registry.has_function("cls_get_info")


class TestAutoDiscoverAndRegister:

    def test_discover_instance(self, function_registry, test_service):
        auto_discover_and_register(function_registry, [test_service])
        assert function_registry.has_function("sampleservice_get_info")

    def test_discover_with_prefix(self, function_registry, test_service):
        auto_discover_and_register(
            function_registry, [(test_service, "x_")]
        )
        assert function_registry.has_function("x_get_info")

    def test_discover_multiple(self, function_registry, test_service):
        class Other:
            def other_method(self) -> str:
                return "other"

        auto_discover_and_register(function_registry, [
            test_service,
            (Other(), "o_"),
        ])
        assert function_registry.has_function("sampleservice_get_info")
        assert function_registry.has_function("o_other_method")

    def test_unknown_type_no_crash(self, function_registry):
        """未知类型不应崩溃。"""
        auto_discover_and_register(function_registry, ["just_a_string"])
        # 不崩溃即通过
