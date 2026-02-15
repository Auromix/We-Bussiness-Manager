"""测试 FunctionRegistry 函数注册表。

本模块测试函数注册表的所有功能，包括：
- 函数注册
- 参数自动推断
- 函数查询
- 函数列表生成
"""
import pytest
from typing import Dict, Any, Optional

from agent.functions.registry import FunctionRegistry, FunctionDefinition
from tests.agent.conftest import (
    sync_test_function,
    async_test_function,
    sample_function_no_params,
    sample_function_with_optional
)


class TestFunctionRegistry:
    """FunctionRegistry 测试类"""
    
    def test_init(self):
        """测试初始化"""
        registry = FunctionRegistry()
        assert registry._functions == {}
    
    def test_register_simple_function(self, function_registry):
        """测试注册简单函数"""
        function_registry.register(
            name="test_func",
            description="测试函数",
            func=sync_test_function
        )
        
        assert function_registry.has_function("test_func")
        func_def = function_registry.get_function("test_func")
        assert func_def is not None
        assert func_def.name == "test_func"
        assert func_def.description == "测试函数"
        assert func_def.func == sync_test_function
    
    def test_register_with_custom_parameters(self, function_registry):
        """测试使用自定义参数 Schema 注册函数"""
        custom_params = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "参数1"},
                "param2": {"type": "integer", "description": "参数2"}
            },
            "required": ["param1"]
        }
        
        function_registry.register(
            name="test_func",
            description="测试函数",
            func=sync_test_function,
            parameters=custom_params
        )
        
        func_def = function_registry.get_function("test_func")
        assert func_def.parameters == custom_params
    
    def test_register_auto_infer_parameters(self, function_registry):
        """测试自动推断参数类型"""
        function_registry.register(
            name="test_func",
            description="测试函数",
            func=sync_test_function
        )
        
        func_def = function_registry.get_function("test_func")
        assert "properties" in func_def.parameters
        assert "param1" in func_def.parameters["properties"]
        assert "param2" in func_def.parameters["properties"]
        assert func_def.parameters["properties"]["param1"]["type"] == "string"
        assert func_def.parameters["properties"]["param2"]["type"] == "integer"
        assert "param1" in func_def.parameters["required"]
        assert "param2" not in func_def.parameters["required"]  # 有默认值
    
    def test_register_overwrite(self, function_registry):
        """测试覆盖已注册的函数"""
        function_registry.register(
            name="test_func",
            description="原始描述",
            func=sync_test_function
        )
        
        # 覆盖注册
        function_registry.register(
            name="test_func",
            description="新描述",
            func=sample_function_no_params
        )
        
        func_def = function_registry.get_function("test_func")
        assert func_def.description == "新描述"
        assert func_def.func == sample_function_no_params
    
    def test_register_async_function(self, function_registry):
        """测试注册异步函数"""
        function_registry.register(
            name="async_func",
            description="异步函数",
            func=async_test_function
        )
        
        func_def = function_registry.get_function("async_func")
        assert func_def.func == async_test_function
    
    def test_register_function_no_params(self, function_registry):
        """测试注册无参数函数"""
        function_registry.register(
            name="no_params_func",
            description="无参数函数",
            func=sample_function_no_params
        )
        
        func_def = function_registry.get_function("no_params_func")
        assert "properties" in func_def.parameters
        assert func_def.parameters["properties"] == {}
        assert "required" not in func_def.parameters or func_def.parameters["required"] == []
    
    def test_register_function_with_optional(self, function_registry):
        """测试注册带可选参数的函数"""
        function_registry.register(
            name="optional_func",
            description="可选参数函数",
            func=sample_function_with_optional
        )
        
        func_def = function_registry.get_function("optional_func")
        assert "param1" in func_def.parameters["properties"]
        assert "param2" in func_def.parameters["properties"]
        assert "param1" in func_def.parameters["required"]
        assert "param2" not in func_def.parameters["required"]
    
    def test_get_function_exists(self, populated_registry):
        """测试获取存在的函数"""
        func_def = populated_registry.get_function("sync_test_function")
        assert func_def is not None
        assert func_def.name == "sync_test_function"
    
    def test_get_function_not_exists(self, function_registry):
        """测试获取不存在的函数"""
        func_def = function_registry.get_function("non_existent")
        assert func_def is None
    
    def test_has_function(self, populated_registry):
        """测试检查函数是否存在"""
        assert populated_registry.has_function("sync_test_function")
        assert not populated_registry.has_function("non_existent")
    
    def test_list_functions(self, populated_registry):
        """测试列出所有函数"""
        functions = populated_registry.list_functions()
        
        assert isinstance(functions, list)
        assert len(functions) == 4  # 4 个测试函数
        
        # 检查函数格式
        for func in functions:
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert isinstance(func["parameters"], dict)
        
        # 检查函数名
        names = [f["name"] for f in functions]
        assert "sync_test_function" in names
        assert "async_test_function" in names
    
    def test_list_functions_empty(self, function_registry):
        """测试列出空注册表的函数"""
        functions = function_registry.list_functions()
        assert functions == []
    
    def test_infer_parameters_complex_types(self, function_registry):
        """测试推断复杂类型参数"""
        def complex_func(
            str_param: str,
            int_param: int,
            float_param: float,
            bool_param: bool,
            list_param: list,
            dict_param: dict,
            optional_str: Optional[str] = None
        ) -> Dict[str, Any]:
            return {}
        
        function_registry.register(
            name="complex_func",
            description="复杂类型函数",
            func=complex_func
        )
        
        func_def = function_registry.get_function("complex_func")
        params = func_def.parameters["properties"]
        
        assert params["str_param"]["type"] == "string"
        assert params["int_param"]["type"] == "integer"
        assert params["float_param"]["type"] == "number"
        assert params["bool_param"]["type"] == "boolean"
        assert params["list_param"]["type"] == "array"
        assert params["dict_param"]["type"] == "object"
        assert params["optional_str"]["type"] == "string"
        
        # optional_str 不应该在 required 中
        assert "optional_str" not in func_def.parameters.get("required", [])
    
    def test_infer_parameters_union_type(self, function_registry):
        """测试推断 Union 类型参数"""
        from typing import Union
        
        def union_func(param: Union[str, int]) -> str:
            return str(param)
        
        function_registry.register(
            name="union_func",
            description="Union 类型函数",
            func=union_func
        )
        
        func_def = function_registry.get_function("union_func")
        # Union 类型应该被推断为第一个非 None 类型
        assert func_def.parameters["properties"]["param"]["type"] in ["string", "integer"]
    
    def test_register_multiple_functions(self, function_registry):
        """测试注册多个函数"""
        functions = [
            ("func1", "函数1", sync_test_function),
            ("func2", "函数2", async_test_function),
            ("func3", "函数3", sample_function_no_params),
        ]
        
        for name, desc, func in functions:
            function_registry.register(name, desc, func)
        
        assert function_registry.has_function("func1")
        assert function_registry.has_function("func2")
        assert function_registry.has_function("func3")
        assert len(function_registry.list_functions()) == 3

