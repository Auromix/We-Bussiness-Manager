#!/usr/bin/env python3
"""健身房智能管理助手 - MiniMax Agent + 数据库集成

本示例展示如何使用 MiniMax Agent 结合数据库，实现健身房的智能管理：
- 自然语言记账（会员卡、私教课、团课、商品销售）
- 自动计算提成
- 智能查询统计
- 会员信息管理

使用方法：
    export MINIMAX_API_KEY="your-api-key"
    python examples/gym_agent_manager.py
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from agent.functions.discovery import agent_callable
from database import DatabaseManager
from database.models import ServiceRecord, Membership, Customer, Employee, ProductSale
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# 全局数据库仓库实例
repo: Optional[DatabaseManager] = None


def init_database() -> DatabaseManager:
    """初始化数据库"""
    global repo
    
    # 确保data目录存在
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "gym_agent_example.db"
    db_url = f"sqlite:///{db_path}"
    
    repo = DatabaseManager(database_url=db_url)
    repo.create_tables()
    
    # 初始化基础数据
    _init_base_data()
    
    logger.info(f"✅ 数据库初始化完成: {db_path}")
    return repo


def _init_base_data():
    """初始化基础数据（员工、服务类型等）"""
    with repo.get_session() as session:
        # 创建员工
        trainer = repo.staff.get_or_create("李教练", "trainer_li", session=session)
        trainer.role = "manager"
        trainer.commission_rate = 40.0
        
        receptionist = repo.staff.get_or_create("小王", "reception_wang", session=session)
        receptionist.role = "staff"
        
        # 创建服务类型
        repo.service_types.get_or_create("私教课程", 300.0, "training", session=session)
        repo.service_types.get_or_create("团课", 50.0, "class", session=session)
        
        # 创建商品
        repo.products.get_or_create("蛋白粉", "supplement", 200.0, session=session)
        repo.products.get_or_create("运动护腕", "equipment", 50.0, session=session)
        
        # 创建引流渠道
        repo.channels.get_or_create("美团", "platform", None, 15.0, session=session)
        repo.channels.get_or_create("朋友推荐", "external", None, 10.0, session=session)
        
        session.commit()


# ========== Agent 可调用的数据库函数 ==========

@agent_callable(description="""记录健身房的服务收入。
参数说明：
- customer_name: 顾客姓名（必填）
- service_type: 服务类型，如"私教课程"、"团课"（必填）
- amount: 服务金额（必填）
- date_str: 日期，格式YYYY-MM-DD，默认今天
- trainer_name: 私教名称，如"李教练"（可选）
- notes: 备注信息（可选）
""")
def record_service_income(
    customer_name: str,
    service_type: str,
    amount: float,
    date_str: Optional[str] = None,
    trainer_name: Optional[str] = None,
    notes: Optional[str] = None
) -> dict:
    """记录服务收入（私教课、团课等）"""
    try:
        # 解析日期
        if date_str:
            service_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            service_date = date.today()
        
        # 计算提成（私教课40%，团课0%）
        commission = 0.0
        trainer_channel_id = None
        if trainer_name and "私教" in service_type:
            # 获取私教渠道
            trainer_channel = repo.channels.get_or_create(
                trainer_name, "internal", None, 40.0
            )
            trainer_channel_id = trainer_channel.id
            commission = amount * 0.4
        
        # 创建原始消息记录
        msg_id = repo.save_raw_message({
            "wechat_msg_id": f"agent_service_{datetime.now().timestamp()}",
            "sender_nickname": "Agent",
            "content": f"{customer_name} {service_type} {amount}元",
            "timestamp": datetime.now()
        })
        
        # 保存服务记录
        record_data = {
            "customer_name": customer_name,
            "service_or_product": service_type,
            "date": service_date,
            "amount": amount,
            "commission": commission,
            "referral_channel_id": trainer_channel_id,
            "net_amount": amount - commission,
            "notes": notes,
            "confirmed": True
        }
        
        record_id = repo.save_service_record(record_data, msg_id)
        
        result = {
            "success": True,
            "record_id": record_id,
            "customer": customer_name,
            "service": service_type,
            "amount": amount,
            "commission": commission,
            "net_income": amount - commission,
            "date": str(service_date)
        }
        
        logger.debug(f"记录服务收入: {result}")
        return result
        
    except Exception as e:
        logger.error(f"记录服务收入失败: {e}")
        return {"success": False, "error": str(e)}


@agent_callable(description="""开会员卡。
参数说明：
- customer_name: 顾客姓名（必填）
- card_type: 卡类型，如"年卡"、"季卡"、"月卡"（必填）
- amount: 充值金额（必填）
- date_str: 开卡日期，格式YYYY-MM-DD，默认今天
""")
def open_membership_card(
    customer_name: str,
    card_type: str,
    amount: float,
    date_str: Optional[str] = None
) -> dict:
    """开会员卡"""
    try:
        # 解析日期
        if date_str:
            opened_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            opened_date = date.today()
        
        # 根据卡类型计算有效期
        days_map = {
            "年卡": 365,
            "季卡": 90,
            "月卡": 30
        }
        days = days_map.get(card_type, 30)
        
        # 创建原始消息
        msg_id = repo.save_raw_message({
            "wechat_msg_id": f"agent_membership_{datetime.now().timestamp()}",
            "sender_nickname": "Agent",
            "content": f"{customer_name}开{card_type}{amount}元",
            "timestamp": datetime.now()
        })
        
        # 保存会员卡
        membership_data = {
            "customer_name": customer_name,
            "card_type": card_type,
            "date": opened_date,
            "amount": amount
        }
        
        membership_id = repo.save_membership(membership_data, msg_id)
        
        # 设置有效期和积分
        with repo.get_session() as session:
            membership = session.query(Membership).filter(
                Membership.id == membership_id
            ).first()
            membership.expires_at = opened_date + timedelta(days=days)
            membership.points = int(amount / 10)  # 每10元1积分
            session.commit()
        
        result = {
            "success": True,
            "membership_id": membership_id,
            "customer": customer_name,
            "card_type": card_type,
            "amount": amount,
            "valid_days": days,
            "expires_at": str(opened_date + timedelta(days=days)),
            "points": int(amount / 10)
        }
        
        logger.debug(f"开会员卡: {result}")
        return result
        
    except Exception as e:
        logger.error(f"开会员卡失败: {e}")
        return {"success": False, "error": str(e)}


@agent_callable(description="""记录商品销售。
参数说明：
- customer_name: 顾客姓名（可选）
- product_name: 商品名称（必填）
- quantity: 数量（默认1）
- amount: 总金额（必填）
- date_str: 日期，格式YYYY-MM-DD，默认今天
""")
def record_product_sale(
    product_name: str,
    amount: float,
    customer_name: Optional[str] = None,
    quantity: int = 1,
    date_str: Optional[str] = None
) -> dict:
    """记录商品销售"""
    try:
        # 解析日期
        if date_str:
            sale_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            sale_date = date.today()
        
        # 创建原始消息
        msg_id = repo.save_raw_message({
            "wechat_msg_id": f"agent_product_{datetime.now().timestamp()}",
            "sender_nickname": "Agent",
            "content": f"{customer_name or '顾客'}购买{product_name}{amount}元",
            "timestamp": datetime.now()
        })
        
        # 保存商品销售
        sale_data = {
            "service_or_product": product_name,
            "date": sale_date,
            "amount": amount,
            "quantity": quantity,
            "unit_price": amount / quantity,
            "customer_name": customer_name,
            "confirmed": True
        }
        
        sale_id = repo.save_product_sale(sale_data, msg_id)
        
        result = {
            "success": True,
            "sale_id": sale_id,
            "product": product_name,
            "quantity": quantity,
            "amount": amount,
            "customer": customer_name or "散客",
            "date": str(sale_date)
        }
        
        logger.debug(f"记录商品销售: {result}")
        return result
        
    except Exception as e:
        logger.error(f"记录商品销售失败: {e}")
        return {"success": False, "error": str(e)}


@agent_callable(description="""查询指定日期的收入统计。
参数说明：
- date_str: 日期，格式YYYY-MM-DD，默认今天
返回当天的服务收入、商品收入、提成支出和净收入。
""")
def query_daily_income(date_str: Optional[str] = None) -> dict:
    """查询每日收入"""
    try:
        # 解析日期
        if date_str:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            query_date = date.today()
        
        with repo.get_session() as session:
            from sqlalchemy import func
            
            # 统计服务收入
            service_stats = session.query(
                func.count(ServiceRecord.id).label("count"),
                func.coalesce(func.sum(ServiceRecord.amount), 0).label("total"),
                func.coalesce(func.sum(ServiceRecord.commission_amount), 0).label("commission"),
                func.coalesce(func.sum(ServiceRecord.net_amount), 0).label("net")
            ).filter(ServiceRecord.service_date == query_date).first()
            
            # 统计商品销售
            product_stats = session.query(
                func.count(ProductSale.id).label("count"),
                func.coalesce(func.sum(ProductSale.total_amount), 0).label("total")
            ).filter(ProductSale.sale_date == query_date).first()
            
            # 获取详细记录
            records = repo.get_daily_records(query_date)
        
        result = {
            "date": str(query_date),
            "service": {
                "count": service_stats.count,
                "revenue": float(service_stats.total),
                "commission": float(service_stats.commission),
                "net": float(service_stats.net)
            },
            "product": {
                "count": product_stats.count,
                "revenue": float(product_stats.total)
            },
            "total_revenue": float(service_stats.total + product_stats.total),
            "total_commission": float(service_stats.commission),
            "total_net": float(service_stats.net + product_stats.total),
            "records": records[:10]  # 最多返回10条记录
        }
        
        logger.debug(f"查询日收入: {result}")
        return result
        
    except Exception as e:
        logger.error(f"查询日收入失败: {e}")
        return {"success": False, "error": str(e)}


@agent_callable(description="""查询会员信息。
参数说明：
- customer_name: 顾客姓名（必填）
返回顾客的所有会员卡、余额、有效期等信息。
""")
def query_member_info(customer_name: str) -> dict:
    """查询会员信息"""
    try:
        with repo.get_session() as session:
            # 查询顾客
            customer = session.query(Customer).filter(
                Customer.name == customer_name
            ).first()
            
            if not customer:
                return {
                    "success": False,
                    "message": f"未找到顾客：{customer_name}"
                }
            
            # 获取会员卡信息
            memberships = []
            for m in customer.memberships:
                memberships.append({
                    "card_type": m.card_type,
                    "balance": float(m.balance),
                    "total_amount": float(m.total_amount),
                    "opened_at": str(m.opened_at),
                    "expires_at": str(m.expires_at) if m.expires_at else None,
                    "points": m.points,
                    "is_active": m.is_active
                })
            
            # 统计消费记录
            service_count = len(customer.service_records)
            product_count = len(customer.product_sales)
        
        result = {
            "success": True,
            "customer": customer_name,
            "memberships": memberships,
            "statistics": {
                "total_cards": len(memberships),
                "service_count": service_count,
                "product_count": product_count
            }
        }
        
        logger.debug(f"查询会员信息: {result}")
        return result
        
    except Exception as e:
        logger.error(f"查询会员信息失败: {e}")
        return {"success": False, "error": str(e)}


@agent_callable(description="""查询私教提成统计。
参数说明：
- trainer_name: 私教姓名，如"李教练"（可选，不填则查询所有私教）
- date_str: 日期，格式YYYY-MM-DD（可选，不填则查询所有日期）
返回私教的提成统计信息。
""")
def query_trainer_commission(
    trainer_name: Optional[str] = None,
    date_str: Optional[str] = None
) -> dict:
    """查询私教提成"""
    try:
        with repo.get_session() as session:
            from sqlalchemy import func
            from database.models import ReferralChannel
            
            query = session.query(
                ReferralChannel.name.label("trainer"),
                func.count(ServiceRecord.id).label("count"),
                func.coalesce(func.sum(ServiceRecord.commission_amount), 0).label("total_commission")
            ).join(
                ServiceRecord,
                ServiceRecord.referral_channel_id == ReferralChannel.id
            ).filter(
                ReferralChannel.channel_type == "internal"
            )
            
            # 过滤条件
            if trainer_name:
                query = query.filter(ReferralChannel.name == trainer_name)
            if date_str:
                query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                query = query.filter(ServiceRecord.service_date == query_date)
            
            query = query.group_by(ReferralChannel.name)
            results = query.all()
            
            commissions = []
            total = 0
            for r in results:
                commission_amount = float(r.total_commission)
                commissions.append({
                    "trainer": r.trainer,
                    "count": r.count,
                    "commission": commission_amount
                })
                total += commission_amount
        
        result = {
            "success": True,
            "date": date_str or "所有日期",
            "trainers": commissions,
            "total_commission": total
        }
        
        logger.debug(f"查询私教提成: {result}")
        return result
        
    except Exception as e:
        logger.error(f"查询私教提成失败: {e}")
        return {"success": False, "error": str(e)}


# ========== 主程序 ==========

async def main():
    """主程序"""
    print("="*60)
    print("健身房智能管理助手 - MiniMax Agent + 数据库")
    print("="*60)
    print()
    
    # 检查 API Key
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 MINIMAX_API_KEY 环境变量")
        print("\n使用方法:")
        print("  export MINIMAX_API_KEY='your-api-key'")
        print("  python examples/gym_agent_manager.py")
        return
    
    # 初始化数据库
    print("📊 初始化数据库...")
    init_database()
    print()
    
    # 创建 MiniMax Provider
    print("🤖 创建 MiniMax Agent...")
    provider = create_provider(
        "minimax",
        api_key=api_key,
        model="MiniMax-M2.5"
    )
    
    # 注册所有工具函数
    registry = FunctionRegistry()
    registry.register("record_service_income", "记录服务收入", record_service_income)
    registry.register("open_membership_card", "开会员卡", open_membership_card)
    registry.register("record_product_sale", "记录商品销售", record_product_sale)
    registry.register("query_daily_income", "查询每日收入", query_daily_income)
    registry.register("query_member_info", "查询会员信息", query_member_info)
    registry.register("query_trainer_commission", "查询私教提成", query_trainer_commission)
    
    # 创建 Agent
    agent = Agent(
        provider,
        function_registry=registry,
        system_prompt="""你是健身房的智能管理助手。你能帮助健身房经营者：
1. 记录每日收入（私教课、团课、会员卡、商品销售）
2. 自动计算私教提成（私教课提成40%）
3. 查询统计数据（日收入、会员信息、提成统计）

重要规则：
- 私教课程提成40%，团课无提成
- 每10元充值获得1积分
- 年卡365天，季卡90天，月卡30天
- 认真理解用户的自然语言输入，准确调用相应的工具
- 结果用中文简洁回复，包含关键数字"""
    )
    
    print("✅ Agent 初始化完成")
    print()
    
    # 模拟健身房经营者的日常操作
    scenarios = [
        "今天张三上了李教练的私教课，收费300元",
        "李四开了一张年卡，充值3000元",
        "王五买了一瓶蛋白粉，200元",
        "查询一下今天的收入情况",
        "查一下李四的会员信息",
        "统计一下李教练今天的提成"
    ]
    
    print("="*60)
    print("开始模拟健身房经营场景")
    print("="*60)
    print()
    
    for i, user_input in enumerate(scenarios, 1):
        print(f"{'='*60}")
        print(f"场景 {i}")
        print(f"{'='*60}")
        print(f"👤 经营者: {user_input}")
        print()
        
        try:
            # 每个场景使用独立的 Agent（清除历史）
            agent.clear_history()
            
            response = await agent.chat(user_input, temperature=0.1)
            
            print(f"🤖 助手: {response['content']}")
            
            if response['function_calls']:
                print(f"\n📞 调用的工具: {[fc['name'] for fc in response['function_calls']]}")
            
            # 显示 Interleaved Thinking
            if 'metadata' in response and response.get('metadata', {}).get('thinking'):
                thinking = response['metadata']['thinking']
                print(f"\n💭 思考过程 (前150字符):")
                print(f"   {thinking[:150]}...")
            
            print()
            
            # 等待一下，避免请求太快
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("="*60)
    print("✅ 所有场景测试完成！")
    print("="*60)
    print(f"\n📁 数据库文件: {project_root / 'data' / 'gym_agent_example.db'}")
    print("你可以使用 SQLite 工具查看数据库内容")


if __name__ == "__main__":
    asyncio.run(main())

