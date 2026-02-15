"""函数自动发现和注册机制。

本模块提供了函数自动发现和注册功能，允许 Agent 自动发现代码库中的
函数并注册为可调用函数，无需手动包装。支持以下方式：
1. 使用装饰器标记函数
2. 自动注册对象实例的所有公共方法
3. 自动注册模块中的所有函数
4. 自动注册类的所有方法

使用示例：
    ```python
    from agent.functions.discovery import agent_callable, register_instance_methods

    # 使用装饰器标记函数
    @agent_callable(description="查询顾客信息")
    def get_customer(name: str) -> dict:
        ...

    # 自动注册对象的所有方法
    register_instance_methods(registry, db_repo, prefix="db_")
    ```
"""
from typing import Callable, Any, Dict, List, Optional, Type, Tuple, Union
from inspect import signature, Parameter, isfunction, getdoc
from loguru import logger

from agent.functions.registry import FunctionRegistry


# 全局标记：哪些函数可以被 Agent 调用
# 此字典存储所有使用 @agent_callable 装饰器标记的函数
_agent_callable_functions: Dict[str, Callable[..., Any]] = {}


def agent_callable(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """装饰器：标记函数可以被 Agent 调用。

    使用此装饰器标记的函数会被自动识别为可被 Agent 调用的函数。
    装饰器会在函数对象上添加特殊属性，用于后续的自动注册。

    Args:
        name: 可选的函数名称。如果不提供，使用函数的 __name__ 属性。
            如果提供，将使用此名称而不是函数名。
        description: 可选的函数描述。如果不提供，将使用函数的文档字符串
            （docstring）。如果函数没有文档字符串，将使用默认描述。
        parameters: 可选的参数 Schema（JSON Schema 格式）。如果不提供，
            将在注册时根据函数签名自动推断。

    Returns:
        装饰器函数，接受一个函数对象并返回标记后的函数对象。

    Example:
        ```python
        @agent_callable(description="查询顾客信息")
        def get_customer(name: str) -> dict:
            \"\"\"根据名称查询顾客信息。\"\"\"
            ...

        # 使用自定义名称
        @agent_callable(
            name="custom_get_customer",
            description="获取顾客详情",
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        )
        def get_customer_info(name: str) -> dict:
            ...
        ```

    Note:
        - 装饰器会在函数对象上添加 _agent_callable、_agent_name、
          _agent_description 和 _agent_parameters 属性。
        - 标记的函数会被添加到全局 _agent_callable_functions 字典中。
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """内部装饰器函数，实际执行标记逻辑。

        Args:
            func: 要标记的函数对象。

        Returns:
            标记后的函数对象（原函数对象，已添加属性）。
        """
        func_name: str = name or func.__name__
        func_description: str = (
            description or getdoc(func) or f"调用 {func_name} 函数"
        )
        func_parameters: Optional[Dict[str, Any]] = parameters
        
        # 在函数对象上添加标记属性
        func._agent_callable = True  # type: ignore[attr-defined]
        func._agent_name = func_name  # type: ignore[attr-defined]
        func._agent_description = func_description  # type: ignore[attr-defined]
        func._agent_parameters = func_parameters  # type: ignore[attr-defined]
        
        # 添加到全局字典
        _agent_callable_functions[func_name] = func
        
        return func
    return decorator


def register_instance_methods(
    registry: FunctionRegistry,
    instance: Any,
    class_name: Optional[str] = None,
    prefix: Optional[str] = None
) -> None:
    """注册对象实例的所有公共方法到函数注册表。

    此函数会自动发现对象实例的所有公共方法（非私有方法、非特殊方法），
    并将它们注册为可被 Agent 调用的函数。函数名会使用指定的前缀和类名。

    Args:
        registry: 函数注册表实例，方法将被注册到此注册表。
        instance: 要注册方法的对象实例。可以是任何 Python 对象。
        class_name: 可选的类名称，用于生成函数名和描述。如果不提供，
            将使用 instance.__class__.__name__。
        prefix: 可选的函数名前缀。如果不提供，将使用
            "{class_name.lower()}_" 作为前缀。例如，如果 class_name 是
            "DatabaseRepository"，prefix 默认为 "databaserepository_"。

    Example:
        ```python
        db_repo = DatabaseRepository()
        register_instance_methods(
            registry,
            db_repo,
            class_name="DatabaseRepository",
            prefix="db_"
        )
        # 会注册以下方法（假设它们存在）:
        # - db_get_customer
        # - db_save_service_record
        # - db_get_records_by_date
        # 等等...
        ```

    Note:
        - 只注册公共方法（不以 _ 开头的方法）。
        - 跳过特殊方法（如 __init__、__str__ 等）。
        - 如果方法已使用 @agent_callable 装饰器标记，会使用装饰器的
          配置（名称、描述、参数）。
        - 某些方法（如 get_session、create_tables）会被自动跳过。
        - 注册失败的方法会记录警告日志，但不会中断整个过程。
    """
    class_name = class_name or instance.__class__.__name__
    prefix = prefix or f"{class_name.lower()}_"
    
    # 遍历对象的所有属性
    for attr_name in dir(instance):
        # 跳过私有方法和特殊方法（以 _ 开头）
        if attr_name.startswith('_'):
            continue
        
        attr: Any = getattr(instance, attr_name)
        
        # 只注册可调用对象（方法），跳过属性
        if not callable(attr):
            continue
        
        # 跳过特殊方法（如 __init__、__str__ 等）
        if attr_name.startswith('__') and attr_name.endswith('__'):
            continue
        
        # 检查方法是否已使用 @agent_callable 装饰器标记
        if hasattr(attr, '_agent_callable'):
            # 使用装饰器提供的配置
            func_name: str = getattr(
                attr, '_agent_name', f"{prefix}{attr_name}"
            )
            description: str = getattr(
                attr, '_agent_description',
                f"调用 {class_name}.{attr_name}"
            )
            parameters: Optional[Dict[str, Any]] = getattr(
                attr, '_agent_parameters', None
            )
            
            registry.register(
                name=func_name,
                description=description,
                func=attr,
                parameters=parameters
            )
            logger.debug(f"Registered marked method: {func_name}")
        else:
            # 自动注册公共方法（未标记的方法）
            func_name = f"{prefix}{attr_name}"
            description = getdoc(attr) or f"调用 {class_name}.{attr_name} 方法"
            
            # 跳过一些不合适的方法（内部方法、初始化方法等）
            if attr_name in ['get_session', 'create_tables']:
                continue
            
            try:
                registry.register(
                    name=func_name,
                    description=description,
                    func=attr
                )
                logger.debug(f"Auto-registered method: {func_name}")
            except Exception as e:
                logger.warning(f"Failed to register {func_name}: {e}")


def register_module_functions(
    registry: FunctionRegistry,
    module: Any,
    prefix: Optional[str] = None,
    filter_func: Optional[Callable[[str, Callable[..., Any]], bool]] = None
) -> None:
    """注册模块中的所有函数到函数注册表。

    此函数会自动发现模块中的所有公共函数（非私有函数），并将它们注册为
    可被 Agent 调用的函数。可以通过 filter_func 参数过滤要注册的函数。

    Args:
        registry: 函数注册表实例，函数将被注册到此注册表。
        module: 要注册函数的模块对象。通常通过 import 语句导入的模块。
        prefix: 可选的函数名前缀。如果不提供，将使用空字符串（无前缀）。
        filter_func: 可选的过滤函数，用于决定哪些函数应该被注册。
            函数签名: (function_name: str, function: Callable) -> bool
            返回 True 表示注册该函数，False 表示跳过。
            如果不提供，将注册所有公共函数。

    Example:
        ```python
        import db.repository as repo_module

        # 注册所有公共函数
        register_module_functions(registry, repo_module, prefix="repo_")

        # 只注册特定函数
        def should_register(name: str, func: Callable) -> bool:
            return name.startswith("get_") or name.startswith("save_")

        register_module_functions(
            registry,
            repo_module,
            prefix="repo_",
            filter_func=should_register
        )
        ```

    Note:
        - 只注册公共函数（不以 _ 开头的函数）。
        - 使用 inspect.isfunction() 检查，只注册真正的函数对象。
        - 如果函数已使用 @agent_callable 装饰器标记，会使用装饰器的配置。
        - 注册失败的函数会记录警告日志，但不会中断整个过程。
    """
    prefix = prefix or ""
    
    # 遍历模块的所有属性
    for attr_name in dir(module):
        # 跳过私有函数（以 _ 开头）
        if attr_name.startswith('_'):
            continue
        
        attr: Any = getattr(module, attr_name)
        
        # 只注册真正的函数对象（使用 isfunction 检查）
        if not isfunction(attr):
            continue
        
        # 应用过滤函数（如果提供）
        if filter_func and not filter_func(attr_name, attr):
            continue
        
        # 检查函数是否已使用 @agent_callable 装饰器标记
        if hasattr(attr, '_agent_callable'):
            # 使用装饰器提供的配置
            func_name: str = getattr(
                attr, '_agent_name', f"{prefix}{attr_name}"
            )
            description: str = getattr(
                attr, '_agent_description', f"调用 {attr_name} 函数"
            )
            parameters: Optional[Dict[str, Any]] = getattr(
                attr, '_agent_parameters', None
            )
            
            registry.register(
                name=func_name,
                description=description,
                func=attr,
                parameters=parameters
            )
            logger.debug(f"Registered marked function: {func_name}")
        else:
            # 自动注册公共函数（未标记的函数）
            func_name = f"{prefix}{attr_name}"
            description = getdoc(attr) or f"调用 {attr_name} 函数"
            
            try:
                registry.register(
                    name=func_name,
                    description=description,
                    func=attr
                )
                logger.debug(f"Auto-registered function: {func_name}")
            except Exception as e:
                logger.warning(f"Failed to register {func_name}: {e}")


def register_class_methods(
    registry: FunctionRegistry,
    cls: Type[Any],
    prefix: Optional[str] = None,
    instance: Optional[Any] = None
) -> None:
    """注册类的所有方法到函数注册表。

    此函数会自动发现类的所有公共方法，并将它们注册为可被 Agent 调用的
    函数。如果提供了实例对象，方法会绑定到该实例；否则方法保持未绑定状态。

    Args:
        registry: 函数注册表实例，方法将被注册到此注册表。
        cls: 要注册方法的类对象（类本身，不是实例）。
        prefix: 可选的函数名前缀。如果不提供，将使用
            "{cls.__name__.lower()}_" 作为前缀。
        instance: 可选的实例对象。如果提供，方法会绑定到此实例，这样
            方法调用时会自动传入 self 参数。如果不提供，方法保持未绑定
            状态（调用时需要手动传入实例）。

    Example:
        ```python
        # 绑定到实例
        db_repo = DatabaseRepository()
        register_class_methods(
            registry,
            DatabaseRepository,
            prefix="db_",
            instance=db_repo
        )

        # 不绑定实例（不推荐，通常应该提供 instance）
        register_class_methods(
            registry,
            DatabaseRepository,
            prefix="db_"
        )
        ```

    Note:
        - 只注册公共方法（不以 _ 开头的方法）。
        - 跳过特殊方法（如 __init__、__str__ 等）。
        - 如果提供了 instance，建议使用 register_instance_methods 代替。
        - 注册失败的方法会记录警告日志，但不会中断整个过程。
    """
    prefix = prefix or f"{cls.__name__.lower()}_"
    
    # 遍历类的所有属性
    for attr_name in dir(cls):
        # 跳过私有方法
        if attr_name.startswith('_'):
            continue
        
        attr: Any = getattr(cls, attr_name)
        
        # 只注册可调用对象（方法）
        if not callable(attr):
            continue
        
        # 跳过特殊方法
        if attr_name.startswith('__') and attr_name.endswith('__'):
            continue
        
        # 如果提供了实例，创建绑定方法；否则使用未绑定方法
        if instance:
            bound_method: Callable[..., Any] = getattr(instance, attr_name)
        else:
            bound_method = attr
        
        func_name: str = f"{prefix}{attr_name}"
        description: str = (
            getdoc(bound_method) or f"调用 {cls.__name__}.{attr_name} 方法"
        )
        
        try:
            registry.register(
                name=func_name,
                description=description,
                func=bound_method
            )
            logger.debug(f"Registered class method: {func_name}")
        except Exception as e:
            logger.warning(f"Failed to register {func_name}: {e}")


def auto_discover_and_register(
    registry: FunctionRegistry,
    targets: List[Union[Any, Tuple[Any, str]]],
    naming_strategy: Optional[Callable[[Any, str], str]] = None
) -> None:
    """自动发现并注册目标对象中的函数。

    此函数是一个便捷方法，可以自动识别目标对象的类型（模块、类或实例），
    并调用相应的注册函数。支持批量注册多个对象。

    Args:
        registry: 函数注册表实例，函数将被注册到此注册表。
        targets: 目标对象列表。每个元素可以是：
            - 模块对象：会调用 register_module_functions
            - 类对象：会调用 register_class_methods
            - 实例对象：会调用 register_instance_methods
            - (对象, 前缀) 元组：对象和对应的函数名前缀
        naming_strategy: 可选的命名策略函数，用于自定义函数名生成。
            函数签名: (obj: Any, name: str) -> str
            如果不提供，使用默认的命名策略。

    Example:
        ```python
        # 注册多个对象
        auto_discover_and_register(registry, [
            db_repo,  # 实例对象
            (db_repo, "db_"),  # 带前缀的实例对象
            (membership_svc, "membership_"),  # 带前缀的服务实例
            some_module,  # 模块对象
        ])

        # 使用自定义命名策略
        def custom_naming(obj: Any, name: str) -> str:
            return f"custom_{name}"

        auto_discover_and_register(
            registry,
            [db_repo],
            naming_strategy=custom_naming
        )
        ```

    Note:
        - 对象类型通过检查属性自动判断，可能不够精确。
        - 如果无法识别对象类型，会记录警告日志并跳过。
        - 元组格式 (obj, prefix) 会覆盖默认的前缀设置。
    """
    for target in targets:
        # 处理元组格式 (obj, prefix)
        if isinstance(target, tuple):
            obj: Any = target[0]
            prefix: Optional[str] = target[1]
        else:
            obj = target
            prefix = None
        
        # 判断对象类型并调用相应的注册函数
        # 检查是否是实例对象（有 __class__ 和 __dict__ 或 __class__）
        if hasattr(obj, '__class__') and (
            hasattr(obj, '__dict__') or hasattr(obj, '__class__')
        ):
            # 是实例对象
            class_name: str = obj.__class__.__name__
            register_instance_methods(registry, obj, class_name, prefix)
        # 检查是否是类对象（有 __class__ 但没有 __dict__）
        elif hasattr(obj, '__class__') and not hasattr(obj, '__module__'):
            # 是类对象
            register_class_methods(registry, obj, prefix)
        # 检查是否是模块对象（有 __name__ 和 __file__）
        elif hasattr(obj, '__name__') and hasattr(obj, '__file__'):
            # 是模块对象
            register_module_functions(registry, obj, prefix)
        else:
            # 无法识别的对象类型
            logger.warning(
                f"Unknown target type: {type(target)}, "
                f"skipping registration"
            )

