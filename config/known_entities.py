"""已知实体定义（顾客、员工、服务类型等）"""

# 已知服务类型
SERVICE_TYPES = [
    {"name": "头疗", "default_price": 30.0, "category": "therapy"},
    {"name": "理疗", "default_price": 198.0, "category": "therapy"},
    {"name": "泡脚", "default_price": 50.0, "category": "foot_bath"},
    {"name": "按摩", "default_price": 100.0, "category": "therapy"},
    {"name": "推拿", "default_price": 120.0, "category": "therapy"},
    {"name": "刮痧", "default_price": 80.0, "category": "therapy"},
    {"name": "拔罐", "default_price": 60.0, "category": "therapy"},
]

# 已知商品类型
PRODUCT_CATEGORIES = [
    "supplement",  # 保健品
    "medicine",    # 药品
    "accessory",   # 配件
]

# 会员卡类型
MEMBERSHIP_CARD_TYPES = [
    "理疗卡",
    "头疗卡",
    "泡脚卡",
    "通用卡",
]

# 常见顾客称呼（用于实体识别）
COMMON_CUSTOMER_PATTERNS = [
    r".*老师",  # 段老师、姚老师等
    r".*哥",    # 李哥等
    r".*姐",    # 王姐等
]

