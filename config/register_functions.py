"""Agent 函数注册模块

将 business_functions 中的所有业务函数注册到 Agent 的 FunctionRegistry 中，
使 Agent 能够根据用户的自然语言指令灵活调用这些函数。

函数分为两类：
1. 查询函数（只读）：直接执行并返回结果
2. 写入函数（增删改）：Agent 会在执行前向用户确认
"""
from agent.functions.registry import FunctionRegistry
from config import business_functions as bf


def register_all_functions(registry: FunctionRegistry) -> None:
    """将所有业务函数注册到函数注册表。

    Args:
        registry: FunctionRegistry 实例
    """

    # ================================================================
    # 服务记录管理
    # ================================================================

    registry.register(
        "record_service",
        "记录一笔服务收入（顾客到店消费）。需要顾客姓名、服务类型和金额。",
        bf.record_service,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
                "service_type": {
                    "type": "string",
                    "description": "服务类型名称，如：推拿按摩、艾灸理疗、拔罐刮痧、足疗、头疗、肩颈调理、全身精油SPA、中药熏蒸",
                },
                "amount": {"type": "number", "description": "服务金额（元）"},
                "employee_name": {
                    "type": "string",
                    "description": "服务员工/技师名称（可选）",
                },
                "date_str": {
                    "type": "string",
                    "description": "日期，格式YYYY-MM-DD，默认今天",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "服务时长（分钟），如60、90",
                },
                "notes": {"type": "string", "description": "备注信息"},
            },
            "required": ["customer_name", "service_type", "amount"],
        },
    )

    registry.register(
        "update_service_record",
        "修改一条已有的服务记录（金额、日期、备注等）。需要记录ID。",
        bf.update_service_record,
        {
            "type": "object",
            "properties": {
                "record_id": {"type": "integer", "description": "服务记录ID"},
                "amount": {"type": "number", "description": "新金额（元）"},
                "service_type": {"type": "string", "description": "新服务类型"},
                "date_str": {"type": "string", "description": "新日期，格式YYYY-MM-DD"},
                "notes": {"type": "string", "description": "新备注"},
            },
            "required": ["record_id"],
        },
    )

    registry.register(
        "delete_service_record",
        "删除一条服务记录。需要记录ID。",
        bf.delete_service_record,
        {
            "type": "object",
            "properties": {
                "record_id": {"type": "integer", "description": "服务记录ID"},
                "reason": {"type": "string", "description": "删除原因"},
            },
            "required": ["record_id"],
        },
    )

    # ================================================================
    # 会员管理
    # ================================================================

    registry.register(
        "open_membership",
        "为顾客开通会员卡/疗程卡/储值卡。需要顾客姓名、卡类型和充值金额。",
        bf.open_membership,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
                "card_type": {
                    "type": "string",
                    "description": "卡类型：年卡、季卡、月卡、次卡、疗程卡、储值卡",
                },
                "amount": {"type": "number", "description": "充值金额（元）"},
                "date_str": {"type": "string", "description": "开卡日期，格式YYYY-MM-DD，默认今天"},
            },
            "required": ["customer_name", "card_type", "amount"],
        },
    )

    registry.register(
        "query_member_info",
        "查询顾客/会员信息（会员卡、余额、有效期、积分、消费统计）。",
        bf.query_member_info,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
            },
            "required": ["customer_name"],
        },
    )

    registry.register(
        "query_expiring_members",
        "查询即将到期的会员卡，方便提前联系顾客续卡。",
        bf.query_expiring_members,
        {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "查询未来多少天内到期，默认7"},
            },
            "required": [],
        },
    )

    registry.register(
        "deduct_membership_balance",
        "扣减会员卡余额（会员消费时使用）。",
        bf.deduct_membership_balance,
        {
            "type": "object",
            "properties": {
                "membership_id": {"type": "integer", "description": "会员卡ID"},
                "amount": {"type": "number", "description": "扣减金额（元）"},
            },
            "required": ["membership_id", "amount"],
        },
    )

    # ================================================================
    # 产品销售
    # ================================================================

    registry.register(
        "record_product_sale",
        "记录产品/商品销售。需要产品名称和金额。",
        bf.record_product_sale,
        {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "产品名称"},
                "amount": {"type": "number", "description": "总金额（元）"},
                "customer_name": {"type": "string", "description": "顾客姓名（可选）"},
                "quantity": {"type": "integer", "description": "数量，默认1"},
                "date_str": {"type": "string", "description": "日期，格式YYYY-MM-DD，默认今天"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["product_name", "amount"],
        },
    )

    registry.register(
        "delete_product_sale",
        "删除一条产品销售记录。",
        bf.delete_product_sale,
        {
            "type": "object",
            "properties": {
                "record_id": {"type": "integer", "description": "销售记录ID"},
                "reason": {"type": "string", "description": "删除原因"},
            },
            "required": ["record_id"],
        },
    )

    # ================================================================
    # 员工管理
    # ================================================================

    registry.register(
        "get_staff_list",
        "获取所有在职员工/技师列表（姓名、角色、提成率）。",
        bf.get_staff_list,
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "add_employee",
        "添加新员工/技师。需要姓名，可选角色和提成率。",
        bf.add_employee,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "员工姓名"},
                "role": {"type": "string", "description": "角色：staff（员工）或manager（管理员），默认staff"},
                "commission_rate": {"type": "number", "description": "提成率（百分比，如30表示30%），默认0"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "update_employee",
        "修改员工信息（角色、提成率、在职状态）。",
        bf.update_employee,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "员工姓名（用于查找）"},
                "role": {"type": "string", "description": "新角色"},
                "commission_rate": {"type": "number", "description": "新提成率（百分比）"},
                "is_active": {"type": "boolean", "description": "是否在职"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "remove_employee",
        "停用/离职员工（软删除）。",
        bf.remove_employee,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "员工姓名"},
            },
            "required": ["name"],
        },
    )

    # ================================================================
    # 顾客管理
    # ================================================================

    registry.register(
        "add_customer",
        "添加新顾客。需要姓名，可选电话和备注。",
        bf.add_customer,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "顾客姓名"},
                "phone": {"type": "string", "description": "联系电话"},
                "notes": {"type": "string", "description": "备注信息"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "update_customer",
        "修改顾客信息（电话、备注）。",
        bf.update_customer,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "顾客姓名（用于查找）"},
                "phone": {"type": "string", "description": "新电话"},
                "notes": {"type": "string", "description": "新备注"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "search_customers",
        "搜索顾客（按姓名或电话模糊搜索）。",
        bf.search_customers,
        {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["keyword"],
        },
    )

    # ================================================================
    # 服务类型和产品配置
    # ================================================================

    registry.register(
        "list_service_types",
        "列出所有服务类型及其默认价格。",
        bf.list_service_types,
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "add_service_type",
        "添加新的服务类型。需要名称，可选默认价格和类别。",
        bf.add_service_type,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "服务类型名称"},
                "default_price": {"type": "number", "description": "默认价格（元）"},
                "category": {"type": "string", "description": "类别"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "update_service_type",
        "修改服务类型信息（价格、类别）。",
        bf.update_service_type,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "服务类型名称（用于查找）"},
                "new_price": {"type": "number", "description": "新默认价格（元）"},
                "new_category": {"type": "string", "description": "新类别"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "list_products",
        "列出所有产品/商品及其价格和库存。",
        bf.list_products,
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "add_product",
        "添加新产品/商品。需要名称，可选类别、单价和初始库存。",
        bf.add_product,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "产品名称"},
                "category": {"type": "string", "description": "类别：consumable（消耗品）或tool（工具）"},
                "unit_price": {"type": "number", "description": "单价（元）"},
                "stock_quantity": {"type": "integer", "description": "初始库存数量"},
            },
            "required": ["name"],
        },
    )

    registry.register(
        "update_product_stock",
        "更新产品库存（入库或出库）。正数入库，负数出库。",
        bf.update_product_stock,
        {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "产品名称"},
                "quantity_change": {"type": "integer", "description": "数量变动（正数入库，负数出库）"},
                "reason": {"type": "string", "description": "变动原因"},
            },
            "required": ["product_name", "quantity_change"],
        },
    )

    # ================================================================
    # 渠道管理
    # ================================================================

    registry.register(
        "list_channels",
        "列出所有引流渠道。",
        bf.list_channels,
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "add_channel",
        "添加新的引流渠道。",
        bf.add_channel,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "渠道名称"},
                "channel_type": {
                    "type": "string",
                    "description": "渠道类型：internal（内部）、external（外部合作）、platform（平台）",
                },
                "commission_rate": {"type": "number", "description": "提成率（百分比）"},
            },
            "required": ["name"],
        },
    )

    # ================================================================
    # 统计查询
    # ================================================================

    registry.register(
        "query_daily_summary",
        "查询指定日期的收入统计汇总（服务收入、产品收入、提成、净收入等）。",
        bf.query_daily_summary,
        {
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "日期，格式YYYY-MM-DD，默认今天"},
            },
            "required": [],
        },
    )

    registry.register(
        "query_date_range_summary",
        "查询日期范围内的收入统计（如本周、本月的营收汇总）。",
        bf.query_date_range_summary,
        {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "开始日期，格式YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期，格式YYYY-MM-DD"},
            },
            "required": ["start_date", "end_date"],
        },
    )

    registry.register(
        "query_employee_commission",
        "查询员工/技师提成统计（服务次数和提成金额）。",
        bf.query_employee_commission,
        {
            "type": "object",
            "properties": {
                "employee_name": {"type": "string", "description": "员工姓名（不填则查询所有）"},
                "date_str": {"type": "string", "description": "日期，格式YYYY-MM-DD（不填则查询所有日期）"},
            },
            "required": [],
        },
    )

    registry.register(
        "query_customer_history",
        "查询顾客的历史消费记录（服务记录和产品购买记录）。",
        bf.query_customer_history,
        {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "顾客姓名"},
                "limit": {"type": "integer", "description": "返回记录条数，默认10"},
            },
            "required": ["customer_name"],
        },
    )

    registry.register(
        "query_low_stock_products",
        "查询低库存产品，方便及时补货。",
        bf.query_low_stock_products,
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "get_business_overview",
        "获取当前业务概览（服务类型数、产品数、员工数、顾客数、会员卡数等）。",
        bf.get_business_overview,
        {"type": "object", "properties": {}, "required": []},
    )


