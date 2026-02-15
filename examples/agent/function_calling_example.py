"""Agent 函数调用示例

本示例展示如何使用 Agent 进行函数调用，包括：
1. 使用装饰器标记函数
2. 手动注册函数
3. 自动注册实例方法
4. 自动注册多个对象
5. Agent 自动调用函数并处理结果

运行方式：
    python examples/agent/function_calling_example.py
"""
import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider, FunctionRegistry
from agent.functions.discovery import (
    agent_callable,
    register_instance_methods,
    auto_discover_and_register
)
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


# ==================== 示例函数定义 ====================

@agent_callable(description="获取当前天气信息")
def get_weather(city: str, unit: str = "celsius") -> Dict[str, Any]:
    """获取指定城市的天气信息
    
    Args:
        city: 城市名称
        unit: 温度单位，'celsius' 或 'fahrenheit'，默认为 'celsius'
    
    Returns:
        包含天气信息的字典
    """
    # 模拟天气数据
    weather_data = {
        "北京": {"temp": 25, "condition": "晴天", "humidity": 60},
        "上海": {"temp": 28, "condition": "多云", "humidity": 70},
        "深圳": {"temp": 30, "condition": "小雨", "humidity": 80},
    }
    
    temp = weather_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})["temp"]
    condition = weather_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})["condition"]
    humidity = weather_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})["humidity"]
    
    if unit == "fahrenheit":
        temp = temp * 9 / 5 + 32
    
    return {
        "city": city,
        "temperature": temp,
        "unit": unit,
        "condition": condition,
        "humidity": humidity
    }


@agent_callable(description="计算两个数字的和")
def add_numbers(a: float, b: float) -> Dict[str, Any]:
    """计算两个数字的和
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        包含计算结果的字典
    """
    return {"result": a + b, "operation": "add"}


@agent_callable(description="获取用户信息")
def get_user_info(user_id: int) -> Dict[str, Any]:
    """根据用户ID获取用户信息
    
    Args:
        user_id: 用户ID
    
    Returns:
        用户信息字典
    """
    # 模拟用户数据
    users = {
        1: {"name": "张三", "email": "zhangsan@example.com", "age": 25},
        2: {"name": "李四", "email": "lisi@example.com", "age": 30},
        3: {"name": "王五", "email": "wangwu@example.com", "age": 28},
    }
    return users.get(user_id, {"name": "未知用户", "email": "", "age": 0})


# ==================== 示例类定义 ====================

class Calculator:
    """计算器类，用于演示实例方法注册"""
    
    def multiply(self, a: float, b: float) -> Dict[str, Any]:
        """计算两个数字的乘积"""
        return {"result": a * b, "operation": "multiply"}
    
    def divide(self, a: float, b: float) -> Dict[str, Any]:
        """计算两个数字的商"""
        if b == 0:
            return {"error": "除数不能为0"}
        return {"result": a / b, "operation": "divide"}
    
    def power(self, base: float, exponent: float) -> Dict[str, Any]:
        """计算幂次方"""
        return {"result": base ** exponent, "operation": "power"}


class DatabaseService:
    """数据库服务类，用于演示实例方法注册"""
    
    def __init__(self):
        # 模拟数据库
        self.data = {
            "customers": [
                {"id": 1, "name": "张三", "balance": 1000.0},
                {"id": 2, "name": "李四", "balance": 2000.0},
            ],
            "orders": [
                {"id": 1, "customer_id": 1, "amount": 100.0},
                {"id": 2, "customer_id": 2, "amount": 200.0},
            ]
        }
    
    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """根据ID获取顾客信息"""
        for customer in self.data["customers"]:
            if customer["id"] == customer_id:
                return customer
        return {"error": "顾客不存在"}
    
    def get_customer_orders(self, customer_id: int) -> List[Dict[str, Any]]:
        """获取顾客的所有订单"""
        return [order for order in self.data["orders"] if order["customer_id"] == customer_id]
    
    def get_customer_balance(self, customer_id: int) -> Dict[str, Any]:
        """获取顾客余额"""
        customer = self.get_customer(customer_id)
        if "error" in customer:
            return customer
        return {"customer_id": customer_id, "balance": customer["balance"]}


# ==================== 示例函数 ====================

async def example_decorator_functions():
    """示例：使用装饰器标记的函数"""
    logger.info("=" * 60)
    logger.info("示例 1: 使用装饰器标记的函数")
    logger.info("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    # 创建函数注册表
    registry = FunctionRegistry()
    
    # 自动注册使用装饰器标记的函数
    auto_discover_and_register(registry, [get_weather, add_numbers, get_user_info])
    
    # 创建 Agent
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(
        provider,
        registry,
        system_prompt="你是一个有用的助手，可以使用函数来获取信息或进行计算。"
    )
    
    # 查看注册的函数
    functions = registry.list_functions()
    logger.info(f"\n已注册 {len(functions)} 个函数:")
    for func in functions:
        logger.info(f"  - {func['name']}: {func['description']}")
    
    # 测试函数调用
    logger.info("\n用户: 北京今天天气怎么样？")
    response = await agent.chat("北京今天天气怎么样？")
    logger.info(f"助手: {response['content']}")
    logger.info(f"调用了 {len(response['function_calls'])} 个函数")
    
    logger.info("\n用户: 计算 123 + 456 的结果")
    response = await agent.chat("计算 123 + 456 的结果")
    logger.info(f"助手: {response['content']}")
    
    logger.info("")


async def example_manual_registration():
    """示例：手动注册函数"""
    logger.info("=" * 60)
    logger.info("示例 2: 手动注册函数")
    logger.info("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    # 定义函数
    def format_date(date_str: str, format_type: str = "YYYY-MM-DD") -> Dict[str, Any]:
        """格式化日期字符串"""
        return {"formatted_date": f"{date_str} ({format_type})", "original": date_str}
    
    # 创建函数注册表并手动注册
    registry = FunctionRegistry()
    registry.register(
        name="format_date",
        description="格式化日期字符串，支持多种格式",
        func=format_date
    )
    
    # 创建 Agent
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(provider, registry)
    
    logger.info("\n用户: 格式化日期 '2024-01-01'")
    response = await agent.chat("格式化日期 '2024-01-01'")
    logger.info(f"助手: {response['content']}")
    
    logger.info("")


async def example_instance_methods():
    """示例：自动注册实例方法"""
    logger.info("=" * 60)
    logger.info("示例 3: 自动注册实例方法")
    logger.info("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    # 创建实例
    calculator = Calculator()
    db_service = DatabaseService()
    
    # 创建函数注册表
    registry = FunctionRegistry()
    
    # 注册实例方法
    register_instance_methods(registry, calculator, class_name="Calculator", prefix="calc_")
    register_instance_methods(registry, db_service, class_name="DatabaseService", prefix="db_")
    
    # 创建 Agent
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(
        provider,
        registry,
        system_prompt="你是一个计算和数据库查询助手。"
    )
    
    # 查看注册的函数
    functions = registry.list_functions()
    logger.info(f"\n已注册 {len(functions)} 个函数:")
    for func in functions:
        logger.info(f"  - {func['name']}: {func['description']}")
    
    # 测试函数调用
    logger.info("\n用户: 计算 12 乘以 8 的结果")
    response = await agent.chat("计算 12 乘以 8 的结果")
    logger.info(f"助手: {response['content']}")
    
    logger.info("\n用户: 查询顾客ID为1的余额")
    response = await agent.chat("查询顾客ID为1的余额")
    logger.info(f"助手: {response['content']}")
    
    logger.info("")


async def example_auto_discover():
    """示例：自动发现并注册多个对象"""
    logger.info("=" * 60)
    logger.info("示例 4: 自动发现并注册多个对象")
    logger.info("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    # 创建多个实例
    calculator = Calculator()
    db_service = DatabaseService()
    
    # 创建函数注册表
    registry = FunctionRegistry()
    
    # 自动发现并注册（使用前缀避免命名冲突）
    auto_discover_and_register(registry, [
        (calculator, "calc_"),
        (db_service, "db_"),
        (get_weather, ""),  # 使用装饰器标记的函数
    ])
    
    # 创建 Agent
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(
        provider,
        registry,
        system_prompt="你是一个多功能的助手，可以进行计算、查询数据库和获取天气信息。"
    )
    
    # 查看注册的函数
    functions = registry.list_functions()
    logger.info(f"\n已注册 {len(functions)} 个函数:")
    for func in functions:
        logger.info(f"  - {func['name']}: {func['description']}")
    
    # 测试复杂查询（需要调用多个函数）
    logger.info("\n用户: 查询顾客1的余额，然后计算余额乘以2的结果")
    response = await agent.chat("查询顾客1的余额，然后计算余额乘以2的结果")
    logger.info(f"助手: {response['content']}")
    logger.info(f"迭代次数: {response['iterations']}")
    logger.info(f"调用了 {len(response['function_calls'])} 个函数")
    
    logger.info("")


async def example_multi_step_function_calling():
    """示例：多步骤函数调用"""
    logger.info("=" * 60)
    logger.info("示例 5: 多步骤函数调用")
    logger.info("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return
    
    # 创建函数注册表
    registry = FunctionRegistry()
    
    # 注册所有函数
    auto_discover_and_register(registry, [
        get_weather,
        add_numbers,
        get_user_info,
        (Calculator(), "calc_"),
        (DatabaseService(), "db_"),
    ])
    
    # 创建 Agent
    provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
    agent = Agent(
        provider,
        registry,
        system_prompt="你是一个智能助手，可以执行复杂的多步骤任务。"
    )
    
    # 测试复杂的多步骤查询
    logger.info("\n用户: 查询顾客1的信息，然后获取北京的天气，最后计算顾客余额加上1000")
    response = await agent.chat(
        "查询顾客1的信息，然后获取北京的天气，最后计算顾客余额加上1000",
        max_iterations=10
    )
    logger.info(f"\n助手: {response['content']}")
    logger.info(f"\n执行统计:")
    logger.info(f"  - 迭代次数: {response['iterations']}")
    logger.info(f"  - 函数调用次数: {len(response['function_calls'])}")
    logger.info("\n调用的函数:")
    for i, func_call in enumerate(response['function_calls'], 1):
        logger.info(f"  {i}. {func_call['name']}({func_call['arguments']})")
    
    logger.info("")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Agent 函数调用示例")
    logger.info("=" * 60)
    logger.info("")
    logger.info("提示: 请确保设置了 OPENAI_API_KEY 环境变量")
    logger.info("")
    
    try:
        # 运行各个示例
        await example_decorator_functions()
        await example_manual_registration()
        await example_instance_methods()
        await example_auto_discover()
        await example_multi_step_function_calling()
        
        logger.info("=" * 60)
        logger.info("示例运行完成！")
        logger.info("=" * 60)
        logger.info("\n关键要点:")
        logger.info("1. 使用 @agent_callable 装饰器可以自动标记函数")
        logger.info("2. 可以手动注册函数到 FunctionRegistry")
        logger.info("3. 可以自动注册实例方法、类方法或模块函数")
        logger.info("4. Agent 会自动处理函数调用和多轮迭代")
        logger.info("5. 函数调用结果会自动返回给 LLM 进行后续处理")
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

