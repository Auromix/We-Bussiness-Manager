"""健身房业务数据库开发示例

本示例展示如何使用数据库模块进行健身房业务管理，包括：
1. 数据库初始化和表创建
2. 员工管理（私教、前台等）
3. 会员管理（年卡、季卡、月卡）
4. 服务记录（私教课程、团课）
5. 商品销售（蛋白粉、运动装备等）
6. 引流渠道管理
7. 会员积分系统
8. 数据查询和统计

运行方式：
    python examples/database/gym_example.py
"""
import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from db.repository import DatabaseRepository
from db.models import (
    Employee, Customer, Membership, ServiceType, ServiceRecord,
    Product, ProductSale, ReferralChannel
)
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


def setup_database():
    """初始化数据库
    
    Returns:
        DatabaseRepository: 数据库仓库实例
    """
    # 使用SQLite数据库（开发环境）
    # 生产环境可以使用PostgreSQL: postgresql://user:pass@host/db
    # 确保data目录存在
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "gym_example.db"
    db_url = f"sqlite:///{db_path}"
    
    logger.info(f"初始化数据库: {db_url}")
    
    # 创建数据库仓库
    repo = DatabaseRepository(database_url=db_url)
    
    # 创建所有表
    repo.create_tables()
    logger.info("数据库表创建完成")
    
    return repo


def setup_employees(repo: DatabaseRepository):
    """设置员工信息
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤1: 设置员工信息")
    logger.info("=" * 60)
    
    # 在session内完成所有操作
    with repo.get_session() as session:
        # 创建私教
        trainer_li = repo.get_or_create_employee("李教练", "trainer_li", session=session)
        trainer_li.role = "manager"
        trainer_li.commission_rate = 40.0  # 私教提成40%
        trainer_li.extra_data = {
            "position": "高级私教",
            "specialties": ["力量训练", "减脂", "增肌"],
            "certifications": ["健身教练资格证", "营养师资格证"]
        }
        
        # 创建前台
        receptionist = repo.get_or_create_employee("小张", "reception_zhang", session=session)
        receptionist.role = "staff"
        receptionist.commission_rate = 5.0
        receptionist.extra_data = {
            "position": "前台接待"
        }
        
        session.commit()
        
        # 在session内访问属性并记录日志
        logger.info(f"✓ 创建私教: {trainer_li.name} (ID: {trainer_li.id}, 提成率: {trainer_li.commission_rate}%)")
        logger.info(f"✓ 创建前台: {receptionist.name} (ID: {receptionist.id})")
    
    logger.info("")


def setup_service_types(repo: DatabaseRepository):
    """设置服务类型
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤2: 设置服务类型")
    logger.info("=" * 60)
    
    # 在session内完成所有操作
    with repo.get_session() as session:
        # 创建私教课程
        personal_training = repo.get_or_create_service_type(
            name="私教课程",
            default_price=300.0,
            category="training",
            session=session
        )
        
        # 创建团课
        group_class = repo.get_or_create_service_type(
            name="团课",
            default_price=50.0,
            category="class",
            session=session
        )
        
        session.commit()
        
        # 在session内访问属性并记录日志
        logger.info(f"✓ 创建服务类型: {personal_training.name} (价格: ¥{personal_training.default_price})")
        logger.info(f"✓ 创建服务类型: {group_class.name} (价格: ¥{group_class.default_price})")
    
    logger.info("")


def setup_referral_channels(repo: DatabaseRepository):
    """设置引流渠道
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤3: 设置引流渠道")
    logger.info("=" * 60)
    
    # 在session内完成所有操作
    with repo.get_session() as session:
        # 创建平台渠道（美团）
        meituan = repo.get_or_create_referral_channel(
            name="美团",
            channel_type="platform",
            commission_rate=15.0,
            session=session
        )
        
        # 创建外部渠道（朋友推荐）
        friend = repo.get_or_create_referral_channel(
            name="朋友推荐",
            channel_type="external",
            commission_rate=10.0,
            session=session
        )
        
        # 创建内部渠道（私教）
        trainer_channel = repo.get_or_create_referral_channel(
            name="李教练",
            channel_type="internal",
            commission_rate=40.0,
            session=session
        )
        
        session.commit()
        
        # 在session内访问属性并记录日志
        logger.info(f"✓ 创建平台渠道: {meituan.name} (提成率: {meituan.commission_rate}%)")
        logger.info(f"✓ 创建外部渠道: {friend.name} (提成率: {friend.commission_rate}%)")
        logger.info(f"✓ 创建内部渠道: {trainer_channel.name} (提成率: {trainer_channel.commission_rate}%)")
    
    logger.info("")


def create_memberships(repo: DatabaseRepository):
    """创建会员卡
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤4: 创建会员卡")
    logger.info("=" * 60)
    
    # 创建不同类型的会员
    customers_data = [
        ("王先生", "年卡", 3000.0, 365, "美团"),
        ("李女士", "季卡", 800.0, 90, "朋友推荐"),
        ("张先生", "月卡", 300.0, 30, "美团"),
    ]
    
    membership_ids = []
    
    for name, card_type, amount, days, source in customers_data:
        # 创建顾客
        customer = repo.get_or_create_customer(name)
        customer.extra_data = {
            "source": source,
            "preferred_trainer": "李教练" if name == "王先生" else None
        }
        
        # 保存原始消息
        msg_id = repo.save_raw_message({
            "wechat_msg_id": f"msg_member_{name}",
            "sender_nickname": "小张",
            "content": f"{name}开{card_type}{amount}元",
            "timestamp": datetime(2024, 1, 1, 10, 0, 0)
        })
        
        # 创建会员卡
        membership_data = {
            "customer_name": name,
            "date": "2024-01-01",
            "amount": amount,
            "card_type": card_type
        }
        
        membership_id = repo.save_membership(membership_data, msg_id)
        
        # 设置有效期和积分
        with repo.get_session() as session:
            from db.models import Membership
            membership = session.query(Membership).filter(
                Membership.id == membership_id
            ).first()
            membership.expires_at = membership.opened_at + timedelta(days=days)
            membership.points = int(amount / 10)  # 每10元1积分
            session.commit()
        
        membership_ids.append(membership_id)
        
        logger.info(f"✓ {name} 开通{card_type}: ¥{amount}, 有效期{days}天, 积分{int(amount/10)}")
    
    logger.info("")


def record_services(repo: DatabaseRepository):
    """记录服务
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤5: 记录服务")
    logger.info("=" * 60)
    
    # 获取私教渠道
    trainer_channel = repo.get_or_create_referral_channel(
        name="李教练",
        channel_type="internal",
        commission_rate=40.0
    )
    
    # 记录私教课程
    service_records = [
        {
            "customer_name": "王先生",
            "service_or_product": "私教课程",
            "date": "2024-01-28",
            "amount": 300.0,
            "commission": 120.0,  # 私教提成40% = 300 * 0.4 = 120
            "referral_channel_id": trainer_channel.id,
            "net_amount": 180.0,
            "recorder_nickname": "小张",
            "extra_data": {
                "course_type": "力量训练",
                "duration": 60,  # 60分钟
                "trainer": "李教练",
                "training_plan": "增肌计划"
            }
        },
        {
            "customer_name": "李女士",
            "service_or_product": "团课",
            "date": "2024-01-28",
            "amount": 50.0,
            "recorder_nickname": "小张",
            "extra_data": {
                "class_type": "瑜伽",
                "duration": 60
            }
        },
        {
            "customer_name": "张先生",
            "service_or_product": "私教课程",
            "date": "2024-01-29",
            "amount": 300.0,
            "commission": 120.0,
            "referral_channel_id": trainer_channel.id,
            "net_amount": 180.0,
            "recorder_nickname": "小张",
            "extra_data": {
                "course_type": "减脂",
                "duration": 60,
                "trainer": "李教练"
            }
        }
    ]
    
    for i, record_data in enumerate(service_records, 1):
        # 保存原始消息
        msg_id = repo.save_raw_message({
            "wechat_msg_id": f"msg_service_{i}",
            "sender_nickname": "小张",
            "content": f"{record_data['date']} {record_data['customer_name']} {record_data['service_or_product']} {record_data['amount']}",
            "timestamp": datetime(2024, 1, 28, 14, 0, 0)
        })
        
        # 保存服务记录
        record_id = repo.save_service_record(record_data, msg_id)
        
        logger.info(f"✓ 记录服务: {record_data['customer_name']} - {record_data['service_or_product']} ¥{record_data['amount']} (ID: {record_id})")
    
    logger.info("")


def record_product_sales(repo: DatabaseRepository):
    """记录商品销售
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤6: 记录商品销售")
    logger.info("=" * 60)
    
    # 在session内创建商品
    with repo.get_session() as session:
        protein = repo.get_or_create_product("蛋白粉", category="supplement", unit_price=200.0, session=session)
        protein.extra_data = {
            "brand": "知名品牌",
            "flavor": "巧克力味",
            "weight": "2kg"
        }
        
        equipment = repo.get_or_create_product("运动护腕", category="equipment", unit_price=50.0, session=session)
        equipment.extra_data = {
            "brand": "专业品牌",
            "material": "弹性材料"
        }
        
        session.commit()
    
    # 销售记录
    sales_data = [
        {
            "service_or_product": "蛋白粉",
            "date": "2024-01-28",
            "amount": 200.0,
            "quantity": 1,
            "unit_price": 200.0,
            "customer_name": "王先生",
            "recorder_nickname": "小张"
        },
        {
            "service_or_product": "运动护腕",
            "date": "2024-01-29",
            "amount": 50.0,
            "quantity": 1,
            "unit_price": 50.0,
            "customer_name": "李女士",
            "recorder_nickname": "小张"
        }
    ]
    
    for i, sale_data in enumerate(sales_data, 1):
        # 保存原始消息
        msg_id = repo.save_raw_message({
            "wechat_msg_id": f"msg_product_{i}",
            "sender_nickname": "小张",
            "content": f"{sale_data['date']} {sale_data['customer_name']}购买{sale_data['service_or_product']}{sale_data['amount']}元",
            "timestamp": datetime(2024, 1, 28, 16, 0, 0)
        })
        
        # 保存销售记录
        sale_id = repo.save_product_sale(sale_data, msg_id)
        
        logger.info(f"✓ 记录销售: {sale_data['customer_name']} - {sale_data['service_or_product']} ¥{sale_data['amount']} (ID: {sale_id})")
    
    logger.info("")


def manage_points_system(repo: DatabaseRepository):
    """管理会员积分系统
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤7: 管理会员积分系统")
    logger.info("=" * 60)
    
    # 获取顾客
    customer = repo.get_or_create_customer("王先生")
    
    # 使用插件数据存储积分历史
    repo.save_plugin_data(
        plugin_name="gym_points",
        entity_type="customer",
        entity_id=customer.id,
        data_key="points_history",
        data_value=[
            {"date": "2024-01-01", "points": 300, "reason": "开卡赠送"},
            {"date": "2024-01-28", "points": 30, "reason": "消费满300元"},
            {"date": "2024-01-28", "points": 20, "reason": "购买蛋白粉"}
        ]
    )
    
    # 读取积分历史
    points_history = repo.get_plugin_data(
        "gym_points", "customer", customer.id, "points_history"
    )
    
    logger.info(f"✓ {customer.name} 的积分历史:")
    total_points = 0
    for record in points_history:
        total_points += record["points"]
        logger.info(f"  - {record['date']}: +{record['points']}积分 ({record['reason']})")
    logger.info(f"  总积分: {total_points}")
    logger.info("")


def query_statistics(repo: DatabaseRepository):
    """查询统计数据
    
    Args:
        repo: 数据库仓库实例
    """
    logger.info("=" * 60)
    logger.info("步骤8: 查询统计数据")
    logger.info("=" * 60)
    
    with repo.get_session() as session:
        from sqlalchemy import func
        from db.models import ServiceRecord, ProductSale, Membership
        
        # 1. 统计服务记录
        service_stats = session.query(
            func.count(ServiceRecord.id).label("count"),
            func.sum(ServiceRecord.amount).label("total_amount"),
            func.sum(ServiceRecord.commission_amount).label("total_commission"),
            func.sum(ServiceRecord.net_amount).label("total_net")
        ).first()
        
        logger.info("服务记录统计:")
        logger.info(f"  - 总记录数: {service_stats.count}")
        logger.info(f"  - 总收入: ¥{float(service_stats.total_amount or 0):.2f}")
        logger.info(f"  - 总提成: ¥{float(service_stats.total_commission or 0):.2f}")
        logger.info(f"  - 净收入: ¥{float(service_stats.total_net or 0):.2f}")
        
        # 2. 统计商品销售
        product_stats = session.query(
            func.count(ProductSale.id).label("count"),
            func.sum(ProductSale.total_amount).label("total_amount")
        ).first()
        
        logger.info("商品销售统计:")
        logger.info(f"  - 总记录数: {product_stats.count}")
        logger.info(f"  - 总收入: ¥{float(product_stats.total_amount or 0):.2f}")
        
        # 3. 统计会员卡
        membership_stats = session.query(
            func.count(Membership.id).label("count"),
            func.sum(Membership.total_amount).label("total_amount")
        ).first()
        
        logger.info("会员卡统计:")
        logger.info(f"  - 总会员数: {membership_stats.count}")
        logger.info(f"  - 总收入: ¥{float(membership_stats.total_amount or 0):.2f}")
        
        # 4. 按日期查询服务记录
        target_date = date(2024, 1, 28)
        records = repo.get_records_by_date(target_date)
        
        logger.info(f"\n{target_date} 的服务记录:")
        for record in records:
            if record['type'] == 'service':
                logger.info(f"  - {record['customer_name']}: {record['service_type']} ¥{record['amount']}")
            else:
                logger.info(f"  - {record['customer_name']}: {record.get('product_name', '商品')} ¥{record.get('total_amount', record.get('amount', 0))}")
        
        # 5. 查询顾客的完整信息
        logger.info("\n顾客详细信息:")
        customer = session.query(Customer).filter(Customer.name == "王先生").first()
        if customer:
            logger.info(f"  - 姓名: {customer.name}")
            logger.info(f"  - 会员卡数: {len(customer.memberships)}")
            logger.info(f"  - 服务记录数: {len(customer.service_records)}")
            logger.info(f"  - 购买记录数: {len(customer.product_sales)}")
            if customer.extra_data:
                logger.info(f"  - 来源: {customer.extra_data.get('source', 'N/A')}")
    
    logger.info("")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("健身房业务数据库开发示例")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # 初始化数据库
        repo = setup_database()
        
        # 设置基础数据
        setup_employees(repo)
        setup_service_types(repo)
        setup_referral_channels(repo)
        
        # 业务操作
        create_memberships(repo)
        record_services(repo)
        record_product_sales(repo)
        manage_points_system(repo)
        
        # 查询统计
        query_statistics(repo)
        
        logger.info("=" * 60)
        logger.info("示例运行完成！")
        logger.info("=" * 60)
        logger.info(f"数据库文件位置: {project_root / 'data' / 'gym_example.db'}")
        logger.info("你可以使用SQLite工具查看数据库内容")
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

