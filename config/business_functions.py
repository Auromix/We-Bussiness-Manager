"""业务函数模块 —— Agent 可调用的数据库操作工具集。

提供灵活的数据库增删改查函数，供 Agent 根据用户自然语言指令动态调用。
所有写操作（增/删/改）返回操作预览信息，需用户确认后才真正执行。

设计原则：
- 查询操作直接执行并返回结果
- 写操作分两步：先预览（prepare），再确认执行（confirm）
- 函数覆盖所有核心业务实体的增删改查
- 使用中文描述，方便 LLM 理解
"""
import json
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List

from loguru import logger

# 全局数据库实例引用（由 app.py 设置）
_db = None
# 待确认的操作缓存 {session_id: {operation_id: operation_data}}
_pending_operations: Dict[str, Dict[str, Any]] = {}
# 操作计数器
_op_counter = 0


def set_db(db_manager):
    """设置数据库管理器实例（由 app.py 调用）。"""
    global _db
    _db = db_manager


def _get_db():
    """获取数据库实例。"""
    assert _db is not None, "数据库未初始化，请先调用 set_db()"
    return _db


def _next_op_id() -> str:
    """生成下一个操作 ID。"""
    global _op_counter
    _op_counter += 1
    return f"op_{_op_counter}"


def _parse_date(date_str: Optional[str] = None) -> date:
    """解析日期字符串，默认今天。"""
    if not date_str:
        return date.today()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return date.today()


# ================================================================
# 服务记录相关
# ================================================================


def record_service(
    customer_name: str,
    service_type: str,
    amount: float,
    employee_name: Optional[str] = None,
    date_str: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    notes: Optional[str] = None,
) -> dict:
    """记录一笔服务收入。

    Args:
        customer_name: 顾客姓名（必填）
        service_type: 服务类型名称，如"推拿按摩"、"艾灸理疗"（必填）
        amount: 服务金额（必填）
        employee_name: 服务员工/技师名称（可选）
        date_str: 日期，格式YYYY-MM-DD，默认今天（可选）
        duration_minutes: 服务时长（分钟）（可选）
        notes: 备注信息（可选）

    Returns:
        操作结果，包含记录详情
    """
    db = _get_db()
    try:
        service_date = _parse_date(date_str)

        # 查找员工和提成
        commission = 0.0
        referral_channel_id = None
        if employee_name:
            with db.get_session() as session:
                from database.models import Employee
                emp = session.query(Employee).filter(
                    Employee.name == employee_name
                ).first()
                if emp and emp.commission_rate:
                    rate = float(emp.commission_rate)
                    commission = amount * (rate / 100.0)

            # 创建/获取渠道
            channel = db.channels.get_or_create(
                employee_name, "internal", None,
                float(emp.commission_rate) if emp and emp.commission_rate else 0
            )
            referral_channel_id = channel.id

        # 构建备注
        full_notes = ""
        if duration_minutes:
            full_notes += f"时长{duration_minutes}分钟"
        if notes:
            full_notes += f"；{notes}" if full_notes else notes

        msg_id = db.save_raw_message({
            "msg_id": f"agent_svc_{datetime.now().timestamp()}",
            "sender_nickname": "管理助手",
            "content": f"{customer_name} {service_type} {amount}元",
            "timestamp": datetime.now(),
        })

        record_id = db.save_service_record({
            "customer_name": customer_name,
            "service_or_product": service_type,
            "date": service_date,
            "amount": amount,
            "commission": commission,
            "referral_channel_id": referral_channel_id,
            "net_amount": amount - commission,
            "notes": full_notes or None,
            "confirmed": True,
        }, msg_id)

        return {
            "success": True,
            "message": f"✅ 已记录服务：{customer_name} - {service_type} {amount}元",
            "record_id": record_id,
            "customer": customer_name,
            "service": service_type,
            "amount": amount,
            "employee": employee_name or "未指定",
            "commission": commission,
            "net_income": amount - commission,
            "duration": f"{duration_minutes}分钟" if duration_minutes else "未记录",
            "date": str(service_date),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_service_record(record_id: int, reason: Optional[str] = None) -> dict:
    """删除一条服务记录。

    Args:
        record_id: 服务记录ID（必填）
        reason: 删除原因（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import ServiceRecord
        with db.get_session() as session:
            record = session.query(ServiceRecord).filter(
                ServiceRecord.id == record_id
            ).first()
            if not record:
                return {"success": False, "message": f"未找到ID为{record_id}的服务记录"}

            info = {
                "customer": record.customer.name if record.customer else "未知",
                "service": record.service_type.name if record.service_type else "未知",
                "amount": float(record.amount),
                "date": str(record.service_date),
            }

        # 保存修正记录
        db.messages.save_correction({
            "original_record_type": "service_records",
            "original_record_id": record_id,
            "correction_type": "delete",
            "old_value": info,
            "reason": reason or "用户通过助手删除",
        })

        # 执行删除
        from database.models import ServiceRecord
        result = db.service_records.delete_by_id(ServiceRecord, record_id)

        if result:
            return {
                "success": True,
                "message": f"✅ 已删除服务记录 #{record_id}：{info['customer']} - {info['service']} {info['amount']}元",
                "deleted_record": info,
            }
        return {"success": False, "message": "删除失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_service_record(
    record_id: int,
    amount: Optional[float] = None,
    service_type: Optional[str] = None,
    date_str: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """修改一条服务记录的信息。

    Args:
        record_id: 服务记录ID（必填）
        amount: 新金额（可选）
        service_type: 新服务类型（可选）
        date_str: 新日期，格式YYYY-MM-DD（可选）
        notes: 新备注（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import ServiceRecord
        update_kwargs = {}
        if amount is not None:
            update_kwargs["amount"] = amount
            update_kwargs["net_amount"] = amount  # 简化处理
        if date_str:
            update_kwargs["service_date"] = _parse_date(date_str)
        if notes is not None:
            update_kwargs["notes"] = notes

        if not update_kwargs:
            return {"success": False, "message": "未提供需要修改的字段"}

        result = db.service_records.update_by_id(
            ServiceRecord, record_id, **update_kwargs
        )
        if result:
            return {
                "success": True,
                "message": f"✅ 已更新服务记录 #{record_id}",
                "updated_fields": {k: str(v) for k, v in update_kwargs.items()},
            }
        return {"success": False, "message": f"未找到ID为{record_id}的服务记录"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 会员管理相关
# ================================================================


def open_membership(
    customer_name: str,
    card_type: str,
    amount: float,
    date_str: Optional[str] = None,
) -> dict:
    """为顾客开通会员卡/疗程卡。

    Args:
        customer_name: 顾客姓名（必填）
        card_type: 卡类型，如"年卡"、"季卡"、"月卡"、"次卡"、"疗程卡"（必填）
        amount: 充值金额（必填）
        date_str: 开卡日期，格式YYYY-MM-DD，默认今天（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import Membership
        opened_date = _parse_date(date_str)

        days_map = {"年卡": 365, "季卡": 90, "月卡": 30, "次卡": 365, "疗程卡": 180, "储值卡": 365}
        days = days_map.get(card_type, 365)

        msg_id = db.save_raw_message({
            "msg_id": f"agent_mem_{datetime.now().timestamp()}",
            "sender_nickname": "管理助手",
            "content": f"{customer_name}开{card_type}{amount}元",
            "timestamp": datetime.now(),
        })

        membership_id = db.save_membership({
            "customer_name": customer_name,
            "card_type": card_type,
            "date": opened_date,
            "amount": amount,
        }, msg_id)

        # 设置有效期和积分
        with db.get_session() as session:
            membership = session.query(Membership).filter(
                Membership.id == membership_id
            ).first()
            if membership:
                membership.expires_at = opened_date + timedelta(days=days)
                membership.points = int(amount / 10)
                session.commit()

        return {
            "success": True,
            "message": f"✅ 已为{customer_name}开通{card_type}，充值{amount}元",
            "membership_id": membership_id,
            "customer": customer_name,
            "card_type": card_type,
            "amount": amount,
            "valid_days": days,
            "expires_at": str(opened_date + timedelta(days=days)),
            "points": int(amount / 10),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_member_info(customer_name: str) -> dict:
    """查询顾客/会员信息，包括会员卡、余额、有效期等。

    Args:
        customer_name: 顾客姓名（必填）

    Returns:
        顾客信息
    """
    db = _get_db()
    try:
        from database.models import Customer
        with db.get_session() as session:
            customer = session.query(Customer).filter(
                Customer.name == customer_name
            ).first()

            if not customer:
                return {"success": False, "message": f"未找到顾客：{customer_name}"}

            memberships = []
            for m in customer.memberships:
                memberships.append({
                    "id": m.id,
                    "card_type": m.card_type,
                    "balance": float(m.balance),
                    "total_amount": float(m.total_amount),
                    "opened_at": str(m.opened_at),
                    "expires_at": str(m.expires_at) if m.expires_at else None,
                    "points": m.points,
                    "is_active": m.is_active,
                    "remaining_sessions": m.remaining_sessions,
                })

            service_count = len(customer.service_records)
            product_count = len(customer.product_sales)

        return {
            "success": True,
            "customer": customer_name,
            "phone": customer.phone,
            "notes": customer.notes,
            "memberships": memberships,
            "statistics": {
                "total_cards": len(memberships),
                "service_count": service_count,
                "product_count": product_count,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_expiring_members(days: int = 7) -> dict:
    """查询即将到期的会员卡。

    Args:
        days: 查询未来多少天内到期的会员卡，默认7天

    Returns:
        即将到期的会员列表
    """
    db = _get_db()
    try:
        from database.models import Membership
        today = date.today()
        deadline = today + timedelta(days=days)

        with db.get_session() as session:
            expiring = session.query(Membership).filter(
                Membership.is_active == True,
                Membership.expires_at != None,
                Membership.expires_at <= deadline,
                Membership.expires_at >= today,
            ).all()

            results = []
            for m in expiring:
                results.append({
                    "customer": m.customer.name if m.customer else "未知",
                    "card_type": m.card_type,
                    "expires_at": str(m.expires_at),
                    "balance": float(m.balance),
                    "days_left": (m.expires_at - today).days,
                })

        return {
            "success": True,
            "message": f"未来{days}天内有{len(results)}张会员卡即将到期",
            "expiring_count": len(results),
            "members": results,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def deduct_membership_balance(
    membership_id: int,
    amount: float,
) -> dict:
    """扣减会员卡余额。

    Args:
        membership_id: 会员卡ID（必填）
        amount: 扣减金额（必填）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        result = db.memberships.deduct_balance(membership_id, amount)
        if result:
            return {
                "success": True,
                "message": f"✅ 已扣减会员卡 #{membership_id} 余额 {amount}元，剩余 {float(result.balance)}元",
                "remaining_balance": float(result.balance),
            }
        return {"success": False, "message": "扣减失败，可能余额不足"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 产品销售相关
# ================================================================


def record_product_sale(
    product_name: str,
    amount: float,
    customer_name: Optional[str] = None,
    quantity: int = 1,
    date_str: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """记录产品/商品销售。

    Args:
        product_name: 产品名称（必填）
        amount: 总金额（必填）
        customer_name: 顾客姓名（可选）
        quantity: 数量，默认1
        date_str: 日期，格式YYYY-MM-DD，默认今天（可选）
        notes: 备注（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        sale_date = _parse_date(date_str)

        msg_id = db.save_raw_message({
            "msg_id": f"agent_prod_{datetime.now().timestamp()}",
            "sender_nickname": "管理助手",
            "content": f"{customer_name or '顾客'}购买{product_name}{amount}元",
            "timestamp": datetime.now(),
        })

        sale_id = db.save_product_sale({
            "service_or_product": product_name,
            "date": sale_date,
            "amount": amount,
            "quantity": quantity,
            "unit_price": amount / quantity if quantity > 0 else amount,
            "customer_name": customer_name,
            "notes": notes,
            "confirmed": True,
        }, msg_id)

        return {
            "success": True,
            "message": f"✅ 已记录产品销售：{product_name} x{quantity} 共{amount}元",
            "sale_id": sale_id,
            "product": product_name,
            "quantity": quantity,
            "amount": amount,
            "customer": customer_name or "散客",
            "date": str(sale_date),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_product_sale(record_id: int, reason: Optional[str] = None) -> dict:
    """删除一条产品销售记录。

    Args:
        record_id: 销售记录ID（必填）
        reason: 删除原因（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import ProductSale
        result = db.product_sales.delete_by_id(ProductSale, record_id)
        if result:
            return {
                "success": True,
                "message": f"✅ 已删除产品销售记录 #{record_id}",
            }
        return {"success": False, "message": f"未找到ID为{record_id}的销售记录"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 员工管理相关
# ================================================================


def get_staff_list() -> dict:
    """获取员工/技师列表。

    Returns:
        所有在职员工信息
    """
    db = _get_db()
    try:
        staff = db.get_staff_list(active_only=True)
        return {
            "success": True,
            "message": f"共有{len(staff)}名在职员工",
            "staff_count": len(staff),
            "staff": staff,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_employee(
    name: str,
    role: str = "staff",
    commission_rate: float = 0,
) -> dict:
    """添加新员工/技师。

    Args:
        name: 员工姓名（必填）
        role: 角色，如"staff"（普通员工）、"manager"（管理员）（可选，默认staff）
        commission_rate: 提成率（百分比，如30表示30%）（可选，默认0）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import Employee
        with db.get_session() as session:
            existing = session.query(Employee).filter(
                Employee.name == name
            ).first()
            if existing:
                return {"success": False, "message": f"员工'{name}'已存在"}

        employee = db.staff.get_or_create(name)
        # 更新角色和提成率
        from database.models import Employee
        db.staff.update_by_id(
            Employee, employee.id,
            role=role,
            commission_rate=commission_rate,
        )

        return {
            "success": True,
            "message": f"✅ 已添加员工：{name}（{role}，提成率{commission_rate}%）",
            "employee_id": employee.id,
            "name": name,
            "role": role,
            "commission_rate": commission_rate,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_employee(
    name: str,
    role: Optional[str] = None,
    commission_rate: Optional[float] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """修改员工信息。

    Args:
        name: 员工姓名（必填，用于查找员工）
        role: 新角色（可选）
        commission_rate: 新提成率（可选）
        is_active: 是否在职（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import Employee
        with db.get_session() as session:
            employee = session.query(Employee).filter(
                Employee.name == name
            ).first()
            if not employee:
                return {"success": False, "message": f"未找到员工：{name}"}
            emp_id = employee.id

        update_kwargs = {}
        if role is not None:
            update_kwargs["role"] = role
        if commission_rate is not None:
            update_kwargs["commission_rate"] = commission_rate
        if is_active is not None:
            update_kwargs["is_active"] = is_active

        if not update_kwargs:
            return {"success": False, "message": "未提供需要修改的字段"}

        db.staff.update_by_id(Employee, emp_id, **update_kwargs)
        return {
            "success": True,
            "message": f"✅ 已更新员工 {name} 的信息",
            "updated_fields": update_kwargs,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_employee(name: str) -> dict:
    """停用员工（软删除，标记为不在职）。

    Args:
        name: 员工姓名（必填）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import Employee
        with db.get_session() as session:
            employee = session.query(Employee).filter(
                Employee.name == name
            ).first()
            if not employee:
                return {"success": False, "message": f"未找到员工：{name}"}
            emp_id = employee.id

        db.staff.deactivate(emp_id)
        return {
            "success": True,
            "message": f"✅ 已将员工 {name} 标记为离职",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 顾客管理相关
# ================================================================


def add_customer(
    name: str,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """添加新顾客。

    Args:
        name: 顾客姓名（必填）
        phone: 联系电话（可选）
        notes: 备注信息（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        customer = db.customers.get_or_create(name)
        from database.models import Customer
        update_kwargs = {}
        if phone:
            update_kwargs["phone"] = phone
        if notes:
            update_kwargs["notes"] = notes
        if update_kwargs:
            db.customers.update_by_id(Customer, customer.id, **update_kwargs)

        return {
            "success": True,
            "message": f"✅ 已添加顾客：{name}",
            "customer_id": customer.id,
            "name": name,
            "phone": phone,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_customer(
    name: str,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """修改顾客信息。

    Args:
        name: 顾客姓名（必填，用于查找顾客）
        phone: 新电话（可选）
        notes: 新备注（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import Customer
        with db.get_session() as session:
            customer = session.query(Customer).filter(
                Customer.name == name
            ).first()
            if not customer:
                return {"success": False, "message": f"未找到顾客：{name}"}
            cust_id = customer.id

        update_kwargs = {}
        if phone is not None:
            update_kwargs["phone"] = phone
        if notes is not None:
            update_kwargs["notes"] = notes

        if not update_kwargs:
            return {"success": False, "message": "未提供需要修改的字段"}

        db.customers.update_by_id(Customer, cust_id, **update_kwargs)
        return {
            "success": True,
            "message": f"✅ 已更新顾客 {name} 的信息",
            "updated_fields": update_kwargs,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_customers(keyword: str) -> dict:
    """搜索顾客（按姓名或电话模糊搜索）。

    Args:
        keyword: 搜索关键词（必填）

    Returns:
        匹配的顾客列表
    """
    db = _get_db()
    try:
        customers = db.customers.search(keyword)
        return {
            "success": True,
            "message": f"找到{len(customers)}名匹配的顾客",
            "count": len(customers),
            "customers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "phone": c.phone,
                    "notes": c.notes,
                }
                for c in customers
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 服务类型管理
# ================================================================


def list_service_types() -> dict:
    """列出所有服务类型及其默认价格。

    Returns:
        服务类型列表
    """
    db = _get_db()
    try:
        from database.models import ServiceType
        with db.get_session() as session:
            types = session.query(ServiceType).all()
            result = [
                {
                    "id": t.id,
                    "name": t.name,
                    "default_price": float(t.default_price) if t.default_price else None,
                    "category": t.category,
                }
                for t in types
            ]
        return {
            "success": True,
            "message": f"共有{len(result)}种服务类型",
            "service_types": result,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_service_type(
    name: str,
    default_price: Optional[float] = None,
    category: Optional[str] = None,
) -> dict:
    """添加新的服务类型。

    Args:
        name: 服务类型名称（必填）
        default_price: 默认价格（可选）
        category: 类别（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        st = db.service_types.get_or_create(name, default_price, category)
        return {
            "success": True,
            "message": f"✅ 已添加服务类型：{name}" + (f"（默认价格{default_price}元）" if default_price else ""),
            "service_type_id": st.id,
            "name": name,
            "default_price": default_price,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_service_type(
    name: str,
    new_price: Optional[float] = None,
    new_category: Optional[str] = None,
) -> dict:
    """修改服务类型信息（价格、类别等）。

    Args:
        name: 服务类型名称（必填，用于查找）
        new_price: 新默认价格（可选）
        new_category: 新类别（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import ServiceType
        with db.get_session() as session:
            st = session.query(ServiceType).filter(
                ServiceType.name == name
            ).first()
            if not st:
                return {"success": False, "message": f"未找到服务类型：{name}"}
            st_id = st.id

        update_kwargs = {}
        if new_price is not None:
            update_kwargs["default_price"] = new_price
        if new_category is not None:
            update_kwargs["category"] = new_category

        if not update_kwargs:
            return {"success": False, "message": "未提供需要修改的字段"}

        db.service_types.update_by_id(ServiceType, st_id, **update_kwargs)
        return {
            "success": True,
            "message": f"✅ 已更新服务类型 {name}",
            "updated_fields": update_kwargs,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 产品管理
# ================================================================


def list_products() -> dict:
    """列出所有产品/商品及其价格和库存。

    Returns:
        产品列表
    """
    db = _get_db()
    try:
        from database.models import Product
        with db.get_session() as session:
            products = session.query(Product).all()
            result = [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "unit_price": float(p.unit_price) if p.unit_price else None,
                    "stock_quantity": p.stock_quantity,
                }
                for p in products
            ]
        return {
            "success": True,
            "message": f"共有{len(result)}种产品",
            "products": result,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_product(
    name: str,
    category: Optional[str] = None,
    unit_price: Optional[float] = None,
    stock_quantity: int = 0,
) -> dict:
    """添加新产品/商品。

    Args:
        name: 产品名称（必填）
        category: 类别，如"consumable"（消耗品）、"tool"（工具）（可选）
        unit_price: 单价（可选）
        stock_quantity: 初始库存数量（可选，默认0）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        product = db.products.get_or_create(name, category, unit_price)
        if stock_quantity > 0:
            from database.models import Product
            db.products.update_by_id(Product, product.id, stock_quantity=stock_quantity)

        return {
            "success": True,
            "message": f"✅ 已添加产品：{name}" + (f"（单价{unit_price}元）" if unit_price else ""),
            "product_id": product.id,
            "name": name,
            "unit_price": unit_price,
            "stock_quantity": stock_quantity,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_product_stock(
    product_name: str,
    quantity_change: int,
    reason: Optional[str] = None,
) -> dict:
    """更新产品库存（入库或出库）。

    Args:
        product_name: 产品名称（必填）
        quantity_change: 数量变动，正数表示入库，负数表示出库（必填）
        reason: 变动原因（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        from database.models import Product
        with db.get_session() as session:
            product = session.query(Product).filter(
                Product.name == product_name
            ).first()
            if not product:
                return {"success": False, "message": f"未找到产品：{product_name}"}
            pid = product.id

        result = db.products.update_stock(pid, quantity_change)
        if result:
            action = "入库" if quantity_change > 0 else "出库"
            return {
                "success": True,
                "message": f"✅ {product_name} {action} {abs(quantity_change)}件，当前库存 {result.stock_quantity}件",
                "product": product_name,
                "change": quantity_change,
                "current_stock": result.stock_quantity,
            }
        return {"success": False, "message": "库存更新失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 渠道管理
# ================================================================


def list_channels() -> dict:
    """列出所有引流渠道。

    Returns:
        渠道列表
    """
    db = _get_db()
    try:
        channels = db.get_channel_list()
        return {
            "success": True,
            "message": f"共有{len(channels)}个引流渠道",
            "channels": channels,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_channel(
    name: str,
    channel_type: str = "external",
    commission_rate: Optional[float] = None,
) -> dict:
    """添加引流渠道。

    Args:
        name: 渠道名称（必填）
        channel_type: 渠道类型，"internal"（内部）、"external"（外部合作）、"platform"（平台）（可选，默认external）
        commission_rate: 提成率（百分比）（可选）

    Returns:
        操作结果
    """
    db = _get_db()
    try:
        channel = db.channels.get_or_create(
            name, channel_type, None, commission_rate
        )
        return {
            "success": True,
            "message": f"✅ 已添加渠道：{name}（{channel_type}）",
            "channel_id": channel.id,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 统计查询
# ================================================================


def query_daily_summary(date_str: Optional[str] = None) -> dict:
    """查询指定日期的收入统计汇总。

    Args:
        date_str: 日期，格式YYYY-MM-DD，默认今天（可选）

    Returns:
        当天的服务收入、产品收入、提成支出和净收入
    """
    db = _get_db()
    try:
        from database.models import ServiceRecord, ProductSale
        from sqlalchemy import func

        query_date = _parse_date(date_str)

        with db.get_session() as session:
            svc = session.query(
                func.count(ServiceRecord.id).label("count"),
                func.coalesce(func.sum(ServiceRecord.amount), 0).label("total"),
                func.coalesce(func.sum(ServiceRecord.commission_amount), 0).label("commission"),
                func.coalesce(func.sum(ServiceRecord.net_amount), 0).label("net"),
            ).filter(ServiceRecord.service_date == query_date).first()

            prod = session.query(
                func.count(ProductSale.id).label("count"),
                func.coalesce(func.sum(ProductSale.total_amount), 0).label("total"),
            ).filter(ProductSale.sale_date == query_date).first()

            records = db.get_daily_records(query_date)

        return {
            "success": True,
            "date": str(query_date),
            "service": {
                "count": svc.count,
                "revenue": float(svc.total),
                "commission": float(svc.commission),
                "net": float(svc.net),
            },
            "product": {
                "count": prod.count,
                "revenue": float(prod.total),
            },
            "total_revenue": float(svc.total) + float(prod.total),
            "total_commission": float(svc.commission),
            "total_net": float(svc.net) + float(prod.total),
            "records": records[:20],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_date_range_summary(
    start_date: str,
    end_date: str,
) -> dict:
    """查询日期范围内的收入统计。

    Args:
        start_date: 开始日期，格式YYYY-MM-DD（必填）
        end_date: 结束日期，格式YYYY-MM-DD（必填）

    Returns:
        日期范围内的统计汇总
    """
    db = _get_db()
    try:
        from database.models import ServiceRecord, ProductSale
        from sqlalchemy import func

        start = _parse_date(start_date)
        end = _parse_date(end_date)

        with db.get_session() as session:
            svc = session.query(
                func.count(ServiceRecord.id).label("count"),
                func.coalesce(func.sum(ServiceRecord.amount), 0).label("total"),
                func.coalesce(func.sum(ServiceRecord.commission_amount), 0).label("commission"),
                func.coalesce(func.sum(ServiceRecord.net_amount), 0).label("net"),
            ).filter(
                ServiceRecord.service_date >= start,
                ServiceRecord.service_date <= end,
            ).first()

            prod = session.query(
                func.count(ProductSale.id).label("count"),
                func.coalesce(func.sum(ProductSale.total_amount), 0).label("total"),
            ).filter(
                ProductSale.sale_date >= start,
                ProductSale.sale_date <= end,
            ).first()

        return {
            "success": True,
            "period": f"{start} ~ {end}",
            "service": {
                "count": svc.count,
                "revenue": float(svc.total),
                "commission": float(svc.commission),
                "net": float(svc.net),
            },
            "product": {
                "count": prod.count,
                "revenue": float(prod.total),
            },
            "total_revenue": float(svc.total) + float(prod.total),
            "total_commission": float(svc.commission),
            "total_net": float(svc.net) + float(prod.total),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_employee_commission(
    employee_name: Optional[str] = None,
    date_str: Optional[str] = None,
) -> dict:
    """查询员工/技师提成统计。

    Args:
        employee_name: 员工姓名（可选，不填则查询所有员工）
        date_str: 日期，格式YYYY-MM-DD（可选，不填则查询所有日期）

    Returns:
        员工提成统计
    """
    db = _get_db()
    try:
        from database.models import ServiceRecord, ReferralChannel
        from sqlalchemy import func

        with db.get_session() as session:
            query = session.query(
                ReferralChannel.name.label("employee"),
                func.count(ServiceRecord.id).label("count"),
                func.coalesce(func.sum(ServiceRecord.commission_amount), 0).label("total_commission"),
                func.coalesce(func.sum(ServiceRecord.amount), 0).label("total_revenue"),
            ).join(
                ServiceRecord,
                ServiceRecord.referral_channel_id == ReferralChannel.id,
            ).filter(
                ReferralChannel.channel_type == "internal",
            )

            if employee_name:
                query = query.filter(ReferralChannel.name == employee_name)
            if date_str:
                qd = _parse_date(date_str)
                query = query.filter(ServiceRecord.service_date == qd)

            query = query.group_by(ReferralChannel.name)
            results = query.all()

            commissions = []
            total = 0.0
            for r in results:
                amt = float(r.total_commission)
                commissions.append({
                    "employee": r.employee,
                    "service_count": r.count,
                    "commission": amt,
                    "total_revenue": float(r.total_revenue),
                })
                total += amt

        return {
            "success": True,
            "date": date_str or "所有日期",
            "employees": commissions,
            "total_commission": total,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_customer_history(
    customer_name: str,
    limit: int = 10,
) -> dict:
    """查询顾客的历史消费记录。

    Args:
        customer_name: 顾客姓名（必填）
        limit: 返回记录条数，默认10条

    Returns:
        顾客消费历史
    """
    db = _get_db()
    try:
        from database.models import Customer, ServiceRecord, ProductSale

        with db.get_session() as session:
            customer = session.query(Customer).filter(
                Customer.name == customer_name
            ).first()

            if not customer:
                return {"success": False, "message": f"未找到顾客：{customer_name}"}

            services = session.query(ServiceRecord).filter(
                ServiceRecord.customer_id == customer.id
            ).order_by(ServiceRecord.service_date.desc()).limit(limit).all()

            service_history = [{
                "id": s.id,
                "date": str(s.service_date),
                "service": s.service_type.name if s.service_type else "未知",
                "amount": float(s.amount),
                "notes": s.notes,
            } for s in services]

            products = session.query(ProductSale).filter(
                ProductSale.customer_id == customer.id
            ).order_by(ProductSale.sale_date.desc()).limit(limit).all()

            product_history = [{
                "id": p.id,
                "date": str(p.sale_date),
                "product": p.product.name if p.product else "未知",
                "amount": float(p.total_amount),
                "quantity": p.quantity,
            } for p in products]

        return {
            "success": True,
            "customer": customer_name,
            "service_records": service_history,
            "product_records": product_history,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_low_stock_products() -> dict:
    """查询低库存产品，方便及时补货。

    Returns:
        低库存产品列表
    """
    db = _get_db()
    try:
        products = db.products.get_low_stock()
        result = [{
            "id": p.id,
            "name": p.name,
            "stock_quantity": p.stock_quantity,
            "low_stock_threshold": p.low_stock_threshold,
        } for p in products]

        return {
            "success": True,
            "message": f"有{len(result)}种产品库存偏低",
            "products": result,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================================================================
# 业务配置查看
# ================================================================


def get_business_overview() -> dict:
    """获取当前业务概览（服务类型、产品、员工、渠道的汇总信息）。

    Returns:
        业务概览信息
    """
    db = _get_db()
    try:
        from database.models import ServiceType, Product, Employee, ReferralChannel, Customer, Membership

        with db.get_session() as session:
            service_count = session.query(ServiceType).count()
            product_count = session.query(Product).count()
            staff_count = session.query(Employee).filter(Employee.is_active == True).count()
            customer_count = session.query(Customer).count()
            active_membership_count = session.query(Membership).filter(Membership.is_active == True).count()
            channel_count = session.query(ReferralChannel).filter(ReferralChannel.is_active == True).count()

        return {
            "success": True,
            "overview": {
                "service_types": service_count,
                "products": product_count,
                "active_staff": staff_count,
                "customers": customer_count,
                "active_memberships": active_membership_count,
                "channels": channel_count,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

