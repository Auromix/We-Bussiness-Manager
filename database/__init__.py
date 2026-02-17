"""database 模块 —— 统一的数据库访问层。

本模块采用 Repository 模式，将数据库操作分为以下层次：

┌─────────────────────────────────────────────────┐
│                 DatabaseManager                 │  ← 统一门面
│              (database/manager.py)              │
├─────────────────────────────────────────────────┤
│  实体仓库          │  业务仓库        │  系统仓库 │
│  StaffRepo         │  ServiceRecord   │  Message │  ← 领域仓库
│  CustomerRepo      │  ProductSale     │  Summary │
│  ServiceTypeRepo   │  Membership      │  Plugin  │
│  ProductRepo       │                  │          │
│  ChannelRepo       │                  │          │
├─────────────────────────────────────────────────┤
│                   BaseCRUD                      │  ← 通用CRUD
│              (database/base_crud.py)            │
├─────────────────────────────────────────────────┤
│              DatabaseConnection                 │  ← 基础设施
│            (database/connection.py)             │
├─────────────────────────────────────────────────┤
│           SQLAlchemy ORM Models                 │  ← 数据模型
│            (database/models.py)                 │
└─────────────────────────────────────────────────┘

快速上手：
    ```python
    from database import DatabaseManager

    db = DatabaseManager("sqlite:///data/store.db")
    db.create_tables()

    # 保存服务记录
    db.save_service_record({
        "customer_name": "张三",
        "service_or_product": "头疗",
        "date": "2024-01-28",
        "amount": 198
    }, raw_message_id=1)

    # 查询记录
    records = db.get_daily_records("2024-01-28")

    # 通过子仓库操作
    employee = db.staff.get_or_create("李四")
    ```
"""

# === 核心类导出 ===
from .manager import DatabaseManager
from .connection import DatabaseConnection
from .base_crud import BaseCRUD

# === 仓库类导出 ===
from .entity_repos import (
    StaffRepository,
    CustomerRepository,
    ServiceTypeRepository,
    ProductRepository,
    ChannelRepository,
)
from .business_repos import (
    ServiceRecordRepository,
    ProductSaleRepository,
    MembershipRepository,
)
from .system_repos import (
    MessageRepository,
    SummaryRepository,
    PluginRepository,
)

__all__ = [
    # 核心
    "DatabaseManager",
    "DatabaseConnection",
    "BaseCRUD",
    # 实体仓库
    "StaffRepository",
    "CustomerRepository",
    "ServiceTypeRepository",
    "ProductRepository",
    "ChannelRepository",
    # 业务仓库
    "ServiceRecordRepository",
    "ProductSaleRepository",
    "MembershipRepository",
    # 系统仓库
    "MessageRepository",
    "SummaryRepository",
    "PluginRepository",
]
