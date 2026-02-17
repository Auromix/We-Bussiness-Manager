# Database 模块使用示例

本目录提供了 `database/` 模块的完整使用示例，帮助您快速上手并独立使用数据库功能。

## 📚 目录结构

```
examples/database/
├── README.md                    # 本文档
├── QUICKSTART.md                # 快速开始指南
├── basic_usage.py               # 基础使用示例
├── entity_repos_example.py      # 实体仓库示例（员工、顾客、服务类型等）
├── business_repos_example.py    # 业务仓库示例（服务记录、商品销售、会员卡）
├── system_repos_example.py      # 系统仓库示例（消息、汇总、插件数据）
├── gym_example.py               # 健身房完整业务场景
└── hair_salon_example.py        # 理发店完整业务场景
```

## 🚀 快速开始

如果您是第一次使用，建议按以下顺序学习：

1. **快速开始** → 阅读 `QUICKSTART.md`，5 分钟了解基本用法
2. **基础示例** → 运行 `basic_usage.py`，了解初始化和基本操作
3. **功能示例** → 依次运行：
   - `entity_repos_example.py` - 学习实体管理
   - `business_repos_example.py` - 学习业务记录
   - `system_repos_example.py` - 学习系统功能
4. **完整场景** → 运行 `gym_example.py` 或 `hair_salon_example.py`，了解完整业务流程

## 📖 示例说明

### 1. 基础使用 (`basic_usage.py`)

展示最基本的操作：
- 初始化数据库管理器
- 创建数据表
- 保存和查询数据的基本流程

**适用场景**：第一次使用，需要了解基本操作流程

### 2. 实体仓库示例 (`entity_repos_example.py`)

展示基础实体的管理：
- **员工管理**：创建员工、查询在职员工、停用员工
- **顾客管理**：创建顾客、搜索顾客
- **服务类型管理**：创建服务类型、按分类查询
- **商品管理**：创建商品、库存管理、低库存提醒
- **渠道管理**：创建引流渠道、查询活跃渠道

**适用场景**：需要管理基础数据（员工、顾客、商品等）

### 3. 业务仓库示例 (`business_repos_example.py`)

展示核心业务记录的操作：
- **服务记录**：保存服务记录、查询日报、确认记录
- **商品销售**：保存销售记录、查询销售记录
- **会员卡管理**：开卡、余额扣减、次数扣减、积分管理

**适用场景**：日常业务操作（记录服务、销售、会员卡操作）

### 4. 系统仓库示例 (`system_repos_example.py`)

展示系统级功能：
- **消息管理**：保存原始消息、更新解析状态、消息去重
- **每日汇总**：保存和查询每日经营汇总
- **插件数据**：存储和查询扩展数据（如健身房体测数据）

**适用场景**：消息追溯、报表生成、扩展功能开发

### 5. 完整业务场景

#### 健身房示例 (`gym_example.py`)

完整的健身房业务场景：
- 会员开卡（年卡、次卡）
- 私教课程记录
- 商品销售（蛋白粉、运动装备）
- 渠道提成计算
- 积分系统（通过插件数据）
- 每日汇总

#### 理发店示例 (`hair_salon_example.py`)

完整的理发店业务场景：
- 美发服务记录（剪发、染发、烫发）
- 储值卡管理
- 零售商品销售
- 会员余额和积分
- 每日汇总

## 💡 核心概念

### DatabaseManager - 统一门面

`DatabaseManager` 是数据库模块的统一入口，提供两套 API：

1. **便捷方法**（推荐新手使用）：
   ```python
   db.save_service_record(data, msg_id)
   db.get_daily_records("2024-01-28")
   db.get_customer_info("张三")
   ```

2. **子仓库访问**（适合精细控制）：
   ```python
   db.staff.get_or_create("张三")
   db.customers.search("张")
   db.memberships.deduct_balance(membership_id, 100)
   ```

### 自动创建关联实体

业务仓库的 `save()` 方法会自动创建关联实体，无需手动查找 ID：

```python
# 只需传入名称字符串，系统会自动创建顾客和服务类型
db.save_service_record({
    "customer_name": "张三",  # 自动创建顾客（如果不存在）
    "service_or_product": "头疗",  # 自动创建服务类型（如果不存在）
    "date": "2024-01-28",
    "amount": 198
}, msg_id)
```

### 扩展机制

支持三种扩展方式：

1. **extra_data 字段**：每个实体都有 JSON 扩展字段
   ```python
   db.save_service_record({
       ...
       "extra_data": {"duration_minutes": 60, "goal": "fat_loss"}
   }, msg_id)
   ```

2. **PluginData 表**：完全独立的 KV 存储
   ```python
   db.plugins.save("gym", "customer", customer_id, "body_fat", 18.5)
   body_fat = db.plugins.get("gym", "customer", customer_id, "body_fat")
   ```

3. **子类继承**：继承现有仓库，添加业态特有方法

## 🔧 运行示例

### 前置条件

```bash
# 安装依赖
pip install -r requirements.txt
```

### 运行单个示例

```bash
# 基础示例
python examples/database/basic_usage.py

# 实体仓库示例
python examples/database/entity_repos_example.py

# 业务仓库示例
python examples/database/business_repos_example.py

# 系统仓库示例
python examples/database/system_repos_example.py

# 完整场景
python examples/database/gym_example.py
python examples/database/hair_salon_example.py
```

### 查看生成的数据库

示例运行后会创建 SQLite 数据库文件（位于 `data/` 目录）：

```bash
# 查看数据库
sqlite3 data/basic_usage_example.db

# 在 SQLite 中执行
.tables                    # 查看所有表
SELECT * FROM customers;   # 查看顾客表
SELECT * FROM service_records;  # 查看服务记录表
.quit                      # 退出
```

## 📝 数据模型概览

数据库模块包含以下核心表：

### 实体表（基础数据）
- `employees` - 员工表
- `customers` - 顾客表
- `service_types` - 服务类型表
- `products` - 商品表
- `referral_channels` - 引流渠道表

### 业务表（交易数据）
- `service_records` - 服务记录表
- `product_sales` - 商品销售表
- `memberships` - 会员卡表
- `inventory_logs` - 库存变更日志表

### 系统表（辅助数据）
- `raw_messages` - 原始消息表
- `corrections` - 修正记录表
- `daily_summaries` - 每日汇总表
- `plugin_data` - 插件数据表

详细的数据模型设计请参考 `design/database.md`。

## 🎯 使用建议

### 对于新手

1. 先运行 `basic_usage.py` 了解基本流程
2. 阅读 `QUICKSTART.md` 快速上手
3. 根据业务需求选择对应的示例学习

### 对于开发者

1. 查看 `design/database.md` 了解架构设计
2. 参考测试文件 `tests/database/` 了解边界情况
3. 使用子仓库进行精细控制，使用便捷方法简化代码

### 对于不同业态

- **理发店**：参考 `hair_salon_example.py`
- **健身房**：参考 `gym_example.py`
- **理疗馆**：可参考健身房示例，服务类型改为理疗相关
- **餐厅**：可参考理发店示例，服务类型改为堂食/外卖

## 📚 相关文档

- **设计文档**：`design/database.md` - 详细的架构设计和设计决策
- **API 文档**：查看 `database/` 目录下各文件的 docstring
- **测试用例**：`tests/database/` - 了解各种使用场景和边界情况

## ❓ 常见问题

### Q: 如何切换数据库（SQLite → PostgreSQL）？

A: 只需修改连接 URL：
```python
# SQLite（开发环境）
db = DatabaseManager("sqlite:///data/store.db")

# PostgreSQL（生产环境）
db = DatabaseManager("postgresql://user:pass@localhost/dbname")
```

### Q: 如何自定义扩展字段？

A: 使用 `extra_data` 字段或 `PluginData` 表，详见 `system_repos_example.py`。

### Q: 如何实现事务？

A: 使用 `get_session()` 获取会话，在 `with` 块中执行多个操作：
```python
with db.get_session() as session:
    # 多个操作在同一事务中
    db.staff.create(..., session=session)
    db.customers.create(..., session=session)
    # 自动提交或回滚
```

### Q: 如何查询历史数据？

A: 使用子仓库的查询方法，或直接使用 SQL：
```python
# 使用仓库方法
records = db.service_records.get_by_date(date(2024, 1, 1))

# 使用原始 SQL
results = db.execute_raw_sql(
    "SELECT * FROM service_records WHERE service_date >= :start",
    {"start": "2024-01-01"}
)
```

## 🤝 贡献

如果您发现示例有问题或需要添加新的示例，欢迎提交 Issue 或 Pull Request。
