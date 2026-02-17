#!/usr/bin/env python3
"""MiniMax 真实 API 集成测试。

使用 MiniMax API 验证 Agent 能否：
1. 基础对话（含 Interleaved Thinking）
2. 函数调用（Tool Use）
3. 多轮对话与上下文记忆
4. 模拟用户输入 → Agent 理解 → 调用数据库函数 → 返回结果

运行方式：
    export MINIMAX_API_KEY='sk-api-...'
    pytest tests/agent/test_minimax.py -v -s

或直接运行：
    python tests/agent/test_minimax.py
"""
import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import date, datetime
from typing import Dict, Any, List, Optional

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry

# ================================================================
# MiniMax API 配置
# ================================================================
# 安全提示：API Key 必须通过环境变量提供，不要硬编码在代码中
# 使用方法：export MINIMAX_API_KEY='your-api-key'

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")  # 必须从环境变量获取，无默认值
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5")
MINIMAX_BASE_URL = os.getenv(
    "MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic"
)

# 如果没有 API Key 则跳过所有测试
skip_no_key = pytest.mark.skipif(
    not MINIMAX_API_KEY,
    reason="需要 MINIMAX_API_KEY",
)


# ================================================================
# 模拟数据库 —— 内存存储
# ================================================================

class MockDatabase:
    """模拟数据库，用内存字典存储数据，验证 Agent 的数据库交互能力。"""

    def __init__(self):
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.service_records: List[Dict[str, Any]] = []
        self.memberships: List[Dict[str, Any]] = []
        self.product_sales: List[Dict[str, Any]] = []
        self._next_id = 1

    def _gen_id(self) -> int:
        _id = self._next_id
        self._next_id += 1
        return _id

    # ---- 顾客管理 ----

    def get_or_create_customer(self, name: str) -> Dict[str, Any]:
        """获取或创建顾客。"""
        if name not in self.customers:
            self.customers[name] = {
                "id": self._gen_id(),
                "name": name,
                "phone": None,
                "notes": "",
                "created_at": datetime.now().isoformat(),
            }
        return self.customers[name]

    def get_customer_info(self, name: str) -> Dict[str, Any]:
        """查询顾客信息（含会员卡和消费记录）。"""
        if name not in self.customers:
            return {"error": f"未找到顾客: {name}"}
        customer = self.customers[name]
        # 附加会员卡信息
        cards = [
            m for m in self.memberships
            if m["customer_name"] == name
        ]
        # 附加消费记录
        records = [
            r for r in self.service_records
            if r["customer_name"] == name
        ]
        return {
            **customer,
            "memberships": cards,
            "service_records": records,
            "total_spent": sum(r["amount"] for r in records),
        }

    # ---- 服务记录 ----

    def save_service_record(
        self,
        customer_name: str,
        service_type: str,
        amount: float,
        staff_name: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        """保存服务记录。"""
        self.get_or_create_customer(customer_name)
        record = {
            "id": self._gen_id(),
            "customer_name": customer_name,
            "service_type": service_type,
            "amount": amount,
            "staff_name": staff_name,
            "notes": notes,
            "date": date.today().isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        self.service_records.append(record)
        return {"success": True, "record_id": record["id"], "message": f"已记录 {customer_name} 的 {service_type}，金额 {amount} 元"}

    # ---- 会员卡 ----

    def open_membership(
        self,
        customer_name: str,
        card_type: str,
        amount: float,
    ) -> Dict[str, Any]:
        """开通会员卡。"""
        self.get_or_create_customer(customer_name)
        card = {
            "id": self._gen_id(),
            "customer_name": customer_name,
            "card_type": card_type,
            "balance": amount,
            "total_amount": amount,
            "points": int(amount / 10),
            "is_active": True,
            "created_at": datetime.now().isoformat(),
        }
        self.memberships.append(card)
        return {"success": True, "card_id": card["id"], "message": f"已为 {customer_name} 开通 {card_type}，充值 {amount} 元，获得 {card['points']} 积分"}

    # ---- 商品销售 ----

    def record_product_sale(
        self,
        customer_name: str,
        product_name: str,
        amount: float,
        quantity: int = 1,
    ) -> Dict[str, Any]:
        """记录商品销售。"""
        self.get_or_create_customer(customer_name)
        sale = {
            "id": self._gen_id(),
            "customer_name": customer_name,
            "product_name": product_name,
            "amount": amount,
            "quantity": quantity,
            "date": date.today().isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        self.product_sales.append(sale)
        return {"success": True, "sale_id": sale["id"], "message": f"已记录 {customer_name} 购买 {product_name}，金额 {amount} 元"}

    # ---- 查询统计 ----

    def query_daily_income(
        self, target_date: str = "",
    ) -> Dict[str, Any]:
        """查询指定日期的收入汇总。"""
        if not target_date:
            target_date = date.today().isoformat()
        services = [
            r for r in self.service_records if r["date"] == target_date
        ]
        sales = [
            s for s in self.product_sales if s["date"] == target_date
        ]
        service_total = sum(r["amount"] for r in services)
        sales_total = sum(s["amount"] for s in sales)
        membership_total = sum(
            m["total_amount"]
            for m in self.memberships
            if m["created_at"].startswith(target_date)
        )
        return {
            "date": target_date,
            "service_income": service_total,
            "product_income": sales_total,
            "membership_income": membership_total,
            "total_income": service_total + sales_total + membership_total,
            "service_count": len(services),
            "sale_count": len(sales),
        }

    def get_all_customers(self) -> List[Dict[str, Any]]:
        """获取所有顾客列表。"""
        return list(self.customers.values())


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def mock_db():
    """创建模拟数据库。"""
    return MockDatabase()


@pytest.fixture
def db_registry(mock_db):
    """创建注册了数据库函数的 FunctionRegistry。"""
    registry = FunctionRegistry()

    registry.register(
        "save_service_record",
        "保存服务/消费记录。参数: customer_name(顾客姓名), service_type(服务类型), amount(金额), staff_name(员工姓名,可选), notes(备注,可选)",
        mock_db.save_service_record,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
                "service_type": {"type": "string", "description": "服务类型，如：私教课、团课、理疗、剪发等"},
                "amount": {"type": "number", "description": "金额（元）"},
                "staff_name": {"type": "string", "description": "服务员工姓名"},
                "notes": {"type": "string", "description": "备注信息"},
            },
            "required": ["customer_name", "service_type", "amount"],
        },
    )

    registry.register(
        "open_membership",
        "为顾客开通会员卡。参数: customer_name(顾客姓名), card_type(卡类型), amount(充值金额)",
        mock_db.open_membership,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
                "card_type": {"type": "string", "description": "会员卡类型，如：月卡、季卡、年卡"},
                "amount": {"type": "number", "description": "充值金额（元）"},
            },
            "required": ["customer_name", "card_type", "amount"],
        },
    )

    registry.register(
        "record_product_sale",
        "记录商品销售。参数: customer_name(顾客姓名), product_name(商品名称), amount(金额), quantity(数量,默认1)",
        mock_db.record_product_sale,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
                "product_name": {"type": "string", "description": "商品名称"},
                "amount": {"type": "number", "description": "金额（元）"},
                "quantity": {"type": "integer", "description": "数量，默认1"},
            },
            "required": ["customer_name", "product_name", "amount"],
        },
    )

    registry.register(
        "get_customer_info",
        "查询顾客信息，包括会员卡和消费记录。参数: name(顾客姓名)",
        mock_db.get_customer_info,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "顾客姓名"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "query_daily_income",
        "查询指定日期的收入汇总。参数: target_date(日期,格式YYYY-MM-DD,默认今天)",
        mock_db.query_daily_income,
        {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "日期，格式 YYYY-MM-DD，默认为今天",
                },
            },
            "required": [],
        },
    )

    return registry


@pytest.fixture
def minimax_agent(db_registry):
    """创建使用 MiniMax 的 Agent（带数据库函数）。"""
    provider = create_provider(
        "minimax",
        api_key=MINIMAX_API_KEY,
        model=MINIMAX_MODEL,
        base_url=MINIMAX_BASE_URL,
    )
    return Agent(
        provider,
        function_registry=db_registry,
        system_prompt="""你是一个店铺管理助手。你可以帮助店主：
1. 记录顾客的消费（服务记录、商品销售）
2. 开通会员卡
3. 查询顾客信息
4. 查询每日收入

请根据用户的自然语言描述，准确调用对应的工具函数。
- 金额请使用数字（不要带"元"字）
- 如果用户描述了多个操作，请依次调用对应的函数
- 查询时请直接使用工具获取数据，不要猜测""",
    )


@pytest.fixture
def minimax_simple_agent():
    """创建不带函数的简单 MiniMax Agent。"""
    provider = create_provider(
        "minimax",
        api_key=MINIMAX_API_KEY,
        model=MINIMAX_MODEL,
        base_url=MINIMAX_BASE_URL,
    )
    return Agent(
        provider,
        system_prompt="你是一个友好的助手。请用中文简短回答。",
    )


# ================================================================
# 测试 1: 基础对话
# ================================================================

@skip_no_key
@pytest.mark.asyncio
async def test_basic_chat(minimax_simple_agent):
    """基础对话：Agent 应能正常回复。"""
    response = await minimax_simple_agent.chat(
        "你好，请用一句话介绍一下你自己", temperature=0.7
    )

    assert response["content"], "回复不应为空"
    assert response["iterations"] == 1
    assert response["function_calls"] == []
    print(f"\n[基础对话] 回复: {response['content']}")


@skip_no_key
@pytest.mark.asyncio
async def test_thinking_content(minimax_simple_agent):
    """MiniMax 应支持 Interleaved Thinking。"""
    response = await minimax_simple_agent.chat(
        "请分析一下为什么天空是蓝色的", temperature=0.7
    )

    assert response["content"], "回复不应为空"
    print(f"\n[Thinking] 回复: {response['content'][:100]}...")

    # 检查对话历史中 assistant 消息的 raw_response
    assistant_msgs = [
        m for m in minimax_simple_agent.conversation_history
        if m.role == "assistant"
    ]
    assert len(assistant_msgs) > 0


# ================================================================
# 测试 2: 函数调用 —— 模拟用户输入触发数据库操作
# ================================================================

@skip_no_key
@pytest.mark.asyncio
async def test_record_service(minimax_agent, mock_db):
    """用户描述消费 → Agent 调用 save_service_record。"""
    response = await minimax_agent.chat(
        "张三今天做了一次头疗，收费80元", temperature=0.1
    )

    print(f"\n[记录服务] 回复: {response['content']}")
    print(f"  函数调用: {response['function_calls']}")

    assert len(response["function_calls"]) > 0, "应调用函数"
    assert any(
        fc["name"] == "save_service_record"
        for fc in response["function_calls"]
    ), "应调用 save_service_record"

    # 验证数据库
    assert len(mock_db.service_records) > 0, "数据库应有记录"
    record = mock_db.service_records[0]
    assert record["customer_name"] == "张三"
    assert record["amount"] == 80
    print(f"  数据库记录: {record}")


@skip_no_key
@pytest.mark.asyncio
async def test_open_membership(minimax_agent, mock_db):
    """用户描述开卡 → Agent 调用 open_membership。"""
    response = await minimax_agent.chat(
        "李四要办一张年卡，充值2000元", temperature=0.1
    )

    print(f"\n[开会员卡] 回复: {response['content']}")
    print(f"  函数调用: {response['function_calls']}")

    assert len(response["function_calls"]) > 0
    assert any(
        fc["name"] == "open_membership"
        for fc in response["function_calls"]
    )

    # 验证数据库
    assert len(mock_db.memberships) > 0
    card = mock_db.memberships[0]
    assert card["customer_name"] == "李四"
    assert card["total_amount"] == 2000
    assert card["points"] == 200  # 2000/10
    print(f"  会员卡: {card}")


@skip_no_key
@pytest.mark.asyncio
async def test_record_product_sale(minimax_agent, mock_db):
    """用户描述购买商品 → Agent 调用 record_product_sale。"""
    response = await minimax_agent.chat(
        "王五买了一瓶洗发水，50元", temperature=0.1
    )

    print(f"\n[商品销售] 回复: {response['content']}")
    print(f"  函数调用: {response['function_calls']}")

    assert len(response["function_calls"]) > 0
    assert any(
        fc["name"] == "record_product_sale"
        for fc in response["function_calls"]
    )

    assert len(mock_db.product_sales) > 0
    sale = mock_db.product_sales[0]
    assert sale["customer_name"] == "王五"
    assert sale["amount"] == 50
    print(f"  销售记录: {sale}")


# ================================================================
# 测试 3: 查询 —— Agent 调用查询函数并汇总结果
# ================================================================

@skip_no_key
@pytest.mark.asyncio
async def test_query_customer_info(minimax_agent, mock_db):
    """先创建数据，再查询顾客信息。"""
    # 预置数据
    mock_db.save_service_record("赵六", "按摩", 120)
    mock_db.save_service_record("赵六", "头疗", 80)
    mock_db.open_membership("赵六", "季卡", 1500)

    response = await minimax_agent.chat(
        "查一下赵六的信息", temperature=0.1
    )

    print(f"\n[查询顾客] 回复: {response['content']}")
    print(f"  函数调用: {response['function_calls']}")

    assert len(response["function_calls"]) > 0
    assert any(
        fc["name"] == "get_customer_info"
        for fc in response["function_calls"]
    )
    # 回复应包含顾客相关信息
    assert "赵六" in response["content"]


@skip_no_key
@pytest.mark.asyncio
async def test_query_daily_income(minimax_agent, mock_db):
    """先创建数据，再查询今日收入。"""
    mock_db.save_service_record("A", "剪发", 30)
    mock_db.save_service_record("B", "烫发", 200)
    mock_db.record_product_sale("C", "护发素", 60)

    response = await minimax_agent.chat(
        "今天的收入情况怎么样？", temperature=0.1
    )

    print(f"\n[查询收入] 回复: {response['content']}")
    print(f"  函数调用: {response['function_calls']}")

    assert len(response["function_calls"]) > 0
    assert any(
        fc["name"] == "query_daily_income"
        for fc in response["function_calls"]
    )


# ================================================================
# 测试 4: 多轮对话 —— 上下文记忆
# ================================================================

@skip_no_key
@pytest.mark.asyncio
async def test_multi_turn_memory(minimax_simple_agent):
    """多轮对话应保持上下文。"""
    # 第 1 轮
    r1 = await minimax_simple_agent.chat(
        "我叫张三，是一名理发师", temperature=0.7
    )
    print(f"\n[多轮-1] 回复: {r1['content']}")

    # 第 2 轮
    r2 = await minimax_simple_agent.chat(
        "我叫什么名字？", temperature=0.7
    )
    print(f"[多轮-2] 回复: {r2['content']}")
    assert "张三" in r2["content"], "应记住姓名"

    # 第 3 轮
    r3 = await minimax_simple_agent.chat(
        "我的职业是什么？", temperature=0.7
    )
    print(f"[多轮-3] 回复: {r3['content']}")
    assert "理发" in r3["content"] or "理发师" in r3["content"], "应记住职业"


# ================================================================
# 测试 5: 多轮函数调用 —— 先记录再查询
# ================================================================

@skip_no_key
@pytest.mark.asyncio
async def test_multi_turn_with_functions(minimax_agent, mock_db):
    """多轮对话：先记录消费，再查询。"""
    # 第 1 轮：记录
    r1 = await minimax_agent.chat(
        "张三做了一次按摩，收费150元", temperature=0.1
    )
    print(f"\n[多轮FC-1] 回复: {r1['content']}")
    assert len(mock_db.service_records) > 0

    # 第 2 轮：查询（同一个 Agent，有历史上下文）
    r2 = await minimax_agent.chat(
        "查一下张三的消费记录", temperature=0.1
    )
    print(f"[多轮FC-2] 回复: {r2['content']}")
    assert any(
        fc["name"] == "get_customer_info"
        for fc in r2["function_calls"]
    )
    assert "张三" in r2["content"]


# ================================================================
# 测试 6: 复杂场景 —— 一句话包含多个操作
# ================================================================

@skip_no_key
@pytest.mark.asyncio
async def test_complex_input(minimax_agent, mock_db):
    """一句话描述多个操作，Agent 应依次调用多个函数。"""
    response = await minimax_agent.chat(
        "今天有三笔消费：小明剪发30元，小红烫发200元，小刚买了一瓶洗发水50元",
        temperature=0.1,
    )

    print(f"\n[复杂输入] 回复: {response['content']}")
    print(f"  函数调用: {[fc['name'] for fc in response['function_calls']]}")

    # 应该至少调用了多个函数
    assert len(response["function_calls"]) >= 2, \
        f"应调用多个函数，实际: {len(response['function_calls'])}"

    # 数据库应有多条记录
    total_records = (
        len(mock_db.service_records) + len(mock_db.product_sales)
    )
    assert total_records >= 2, f"数据库应有多条记录，实际: {total_records}"
    print(f"  服务记录: {len(mock_db.service_records)}")
    print(f"  商品销售: {len(mock_db.product_sales)}")


# ================================================================
# 主函数（可直接运行）
# ================================================================

async def main():
    """直接运行测试。"""
    print("=" * 60)
    print("MiniMax Agent 集成测试")
    print("=" * 60)

    if not MINIMAX_API_KEY:
        print("\n❌ 未设置 MINIMAX_API_KEY")
        print("export MINIMAX_API_KEY='sk-api-...'")
        return False

    print(f"\n配置:")
    print(f"  Model: {MINIMAX_MODEL}")
    print(f"  Base URL: {MINIMAX_BASE_URL}")
    if MINIMAX_API_KEY:
        print(f"  API Key: {MINIMAX_API_KEY[:20]}...")
    else:
        print(f"  API Key: 未设置")

    # 创建模拟数据库和 Agent
    db = MockDatabase()
    registry = FunctionRegistry()

    registry.register(
        "save_service_record", "保存服务记录",
        db.save_service_record,
        {"type": "object", "properties": {
            "customer_name": {"type": "string"},
            "service_type": {"type": "string"},
            "amount": {"type": "number"},
            "staff_name": {"type": "string"},
            "notes": {"type": "string"},
        }, "required": ["customer_name", "service_type", "amount"]},
    )
    registry.register(
        "get_customer_info", "查询顾客信息",
        db.get_customer_info,
        {"type": "object", "properties": {
            "name": {"type": "string"},
        }, "required": ["name"]},
    )
    registry.register(
        "query_daily_income", "查询日收入",
        db.query_daily_income,
        {"type": "object", "properties": {
            "target_date": {"type": "string"},
        }, "required": []},
    )
    registry.register(
        "open_membership", "开会员卡",
        db.open_membership,
        {"type": "object", "properties": {
            "customer_name": {"type": "string"},
            "card_type": {"type": "string"},
            "amount": {"type": "number"},
        }, "required": ["customer_name", "card_type", "amount"]},
    )
    registry.register(
        "record_product_sale", "记录商品销售",
        db.record_product_sale,
        {"type": "object", "properties": {
            "customer_name": {"type": "string"},
            "product_name": {"type": "string"},
            "amount": {"type": "number"},
            "quantity": {"type": "integer"},
        }, "required": ["customer_name", "product_name", "amount"]},
    )

    provider = create_provider(
        "minimax",
        api_key=MINIMAX_API_KEY,
        model=MINIMAX_MODEL,
        base_url=MINIMAX_BASE_URL,
    )

    agent = Agent(
        provider,
        function_registry=registry,
        system_prompt="你是店铺管理助手。根据用户描述调用对应工具。",
    )

    results = []

    # 测试 1: 基础对话
    print("\n" + "=" * 50)
    print("测试 1: 基础对话")
    print("=" * 50)
    try:
        simple_agent = Agent(provider, system_prompt="你是友好的助手，用中文简短回答。")
        r = await simple_agent.chat("你好", temperature=0.7)
        print(f"回复: {r['content']}")
        results.append(("基础对话", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("基础对话", False))

    # 测试 2: 记录服务
    print("\n" + "=" * 50)
    print("测试 2: 记录服务")
    print("=" * 50)
    try:
        r = await agent.chat("张三做了头疗，80元", temperature=0.1)
        print(f"回复: {r['content']}")
        print(f"函数调用: {r['function_calls']}")
        print(f"数据库记录: {db.service_records}")
        assert len(db.service_records) > 0
        results.append(("记录服务", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("记录服务", False))

    # 测试 3: 查询
    agent.clear_history()
    print("\n" + "=" * 50)
    print("测试 3: 查询收入")
    print("=" * 50)
    try:
        r = await agent.chat("今天收入多少？", temperature=0.1)
        print(f"回复: {r['content']}")
        print(f"函数调用: {r['function_calls']}")
        results.append(("查询收入", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("查询收入", False))

    # 测试 4: 开会员卡
    agent.clear_history()
    print("\n" + "=" * 50)
    print("测试 4: 开会员卡")
    print("=" * 50)
    try:
        r = await agent.chat("李四办年卡充值3000", temperature=0.1)
        print(f"回复: {r['content']}")
        print(f"函数调用: {r['function_calls']}")
        print(f"会员卡: {db.memberships}")
        assert len(db.memberships) > 0
        results.append(("开会员卡", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("开会员卡", False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n总计: {passed}/{len(results)} 通过")

    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
