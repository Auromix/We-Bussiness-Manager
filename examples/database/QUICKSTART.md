# 快速开始

## 运行健身房数据库示例

### 1. 创建conda环境（推荐）

使用conda创建独立环境：

```bash
# 创建conda环境
conda create -n test_db python=3.11 -y

# 激活环境
conda activate test_db

# 安装依赖
pip install -r requirements.txt
```

### 2. 或使用pip直接安装

如果不想使用conda，可以直接安装依赖：

```bash
pip install -r requirements.txt
```

主要依赖包括：
- sqlalchemy>=2.0.0
- loguru>=0.7.0

### 3. 运行示例

从项目根目录运行：

```bash
python examples/database/gym_example.py
```

### 4. 查看结果

运行后你会看到：
- 详细的步骤日志
- 创建的数据记录
- 统计数据汇总
- 数据库文件位置

数据库文件会保存在：`data/gym_example.db`

### 5. 查看数据库

使用 SQLite 命令行工具：

```bash
sqlite3 data/gym_example.db

# 查看所有表
.tables

# 查看数据
SELECT * FROM customers;
SELECT * FROM service_records;
SELECT * FROM memberships;
```

## 示例功能

示例展示了以下功能：

✅ 数据库初始化和表创建  
✅ 员工管理（私教、前台）  
✅ 服务类型管理（私教课程、团课）  
✅ 引流渠道管理（美团、朋友推荐、私教）  
✅ 会员管理（年卡、季卡、月卡）  
✅ 服务记录（私教课程、团课）  
✅ 商品销售（蛋白粉、运动装备）  
✅ 会员积分系统  
✅ 数据查询和统计  

## 下一步

- 查看 [README.md](README.md) 了解详细说明
- 查看 [gym_example.py](gym_example.py) 学习代码实现
- 基于示例创建你自己的业务场景

