# 数据库开发示例

本目录包含数据库相关的独立开发示例，展示如何使用数据库模块进行业务管理。

## 示例列表

### 健身房业务示例 (`gym_example.py`)

一个完整的健身房业务管理示例，展示以下功能：

1. **数据库初始化**
   - 创建数据库连接
   - 创建所有数据表

2. **员工管理**
   - 创建私教、前台等员工
   - 设置员工角色和提成率
   - 存储员工扩展信息（职位、技能等）

3. **服务类型管理**
   - 创建私教课程、团课等服务类型
   - 设置默认价格和分类

4. **引流渠道管理**
   - 创建平台渠道（如美团）
   - 创建外部渠道（如朋友推荐）
   - 创建内部渠道（如私教）
   - 设置不同渠道的提成率

5. **会员管理**
   - 创建不同类型的会员卡（年卡、季卡、月卡）
   - 设置会员卡有效期
   - 管理会员积分

6. **服务记录**
   - 记录私教课程、团课等服务
   - 关联引流渠道和提成
   - 存储服务扩展信息（课程类型、时长等）

7. **商品销售**
   - 创建商品（蛋白粉、运动装备等）
   - 记录商品销售
   - 关联顾客和记录员

8. **会员积分系统**
   - 使用插件数据存储积分历史
   - 查询积分记录

9. **数据查询和统计**
   - 统计服务记录、商品销售、会员卡
   - 按日期查询记录
   - 查询顾客完整信息

## 运行示例

### 前置要求

1. 确保已安装项目依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 确保项目根目录在 Python 路径中（示例代码会自动处理）

### 运行健身房示例

```bash
# 从项目根目录运行
python examples/database/gym_example.py
```

或者：

```bash
# 进入示例目录
cd examples/database
python gym_example.py
```

## 示例输出

运行示例后，你将看到：

1. 数据库初始化信息
2. 每个步骤的详细操作日志
3. 创建的数据记录ID
4. 统计数据汇总

示例会在 `data/` 目录下创建 `gym_example.db` SQLite 数据库文件。

## 查看数据库

你可以使用以下工具查看数据库内容：

### SQLite 命令行工具

```bash
sqlite3 data/gym_example.db
```

常用命令：
```sql
-- 查看所有表
.tables

-- 查看表结构
.schema employees
.schema customers
.schema service_records

-- 查询数据
SELECT * FROM employees;
SELECT * FROM customers;
SELECT * FROM service_records;
```

### 图形化工具

推荐使用以下工具：
- [DB Browser for SQLite](https://sqlitebrowser.org/)
- [DBeaver](https://dbeaver.io/)
- [DataGrip](https://www.jetbrains.com/datagrip/)

## 代码结构说明

### 主要函数

- `setup_database()`: 初始化数据库连接和表
- `setup_employees()`: 创建员工数据
- `setup_service_types()`: 创建服务类型
- `setup_referral_channels()`: 创建引流渠道
- `create_memberships()`: 创建会员卡
- `record_services()`: 记录服务
- `record_product_sales()`: 记录商品销售
- `manage_points_system()`: 管理积分系统
- `query_statistics()`: 查询统计数据

### 数据库操作模式

示例展示了两种数据库操作模式：

1. **使用 Repository 方法**（推荐）
   ```python
   customer = repo.get_or_create_customer("王先生")
   membership_id = repo.save_membership(membership_data, msg_id)
   ```

2. **直接使用 Session**（高级用法）
   ```python
   with repo.get_session() as session:
       membership = session.query(Membership).filter(...).first()
       membership.points = 300
       session.commit()
   ```

## 扩展示例

你可以基于这个示例创建其他业务场景的示例：

- 美发店业务示例
- 理疗店业务示例
- 其他服务行业示例

只需修改业务逻辑部分，数据库操作模式是通用的。

## 注意事项

1. **数据库文件位置**: 示例会在 `data/` 目录下创建数据库文件，每次运行会覆盖之前的数据库。数据库文件已通过 `.gitignore` 配置忽略，不会被提交到版本控制。

2. **生产环境**: 示例使用 SQLite 数据库，适合开发和测试。生产环境建议使用 PostgreSQL：
   ```python
   db_url = "postgresql://user:password@localhost/dbname"
   repo = DatabaseRepository(database_url=db_url)
   ```

3. **数据持久化**: 所有数据操作都会自动提交到数据库，确保数据持久化。

4. **错误处理**: 实际开发中应该添加更完善的错误处理和事务管理。

## 相关文档

- [数据库设计文档](../../design/database.md)
- [Repository API 文档](../../db/repository.py)

