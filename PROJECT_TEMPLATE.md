# 新项目模板

## 📋 快速创建新项目

使用此模板快速创建新项目，只需实现业务逻辑，核心框架完全复用。

## 🗂️ 项目结构

```
new-project/
├── business/
│   ├── __init__.py
│   └── new_project_adapter.py    # ⭐ 实现业务逻辑适配器
├── config/
│   └── new_project_config.py     # ⭐ 实现业务配置
├── db/
│   ├── new_project_models.py     # ⭐ 定义数据库模型
│   └── new_project_repository.py # ⭐ 实现数据库访问层
├── main.py                      # ⭐ 修改适配器实例
└── requirements.txt               # 复用原项目的依赖
```

## 📝 实现步骤

### 步骤 1: 复制核心框架

```bash
# 复制核心框架代码（不需要修改）
cp -r core/ new-project/
cp -r parsing/ new-project/
cp -r config/settings.py new-project/config/
```

### 步骤 2: 实现业务逻辑适配器

创建 `business/new_project_adapter.py`:

```python
from core.business_adapter import BusinessLogicAdapter
from db.new_project_repository import NewProjectRepository
from typing import Dict, Any, Optional, List
from datetime import date

class NewProjectAdapter(BusinessLogicAdapter):
    """新项目的业务逻辑适配器"""
    
    def __init__(self, db_repo: NewProjectRepository):
        self.db = db_repo
    
    def save_business_record(self, record_type: str, data: Dict[str, Any], 
                            raw_message_id: int, confirmed: bool) -> int:
        """保存业务记录"""
        # 根据新项目的业务逻辑实现
        if record_type == 'order':
            return self.db.save_order(data, raw_message_id)
        elif record_type == 'payment':
            return self.db.save_payment(data, raw_message_id)
        else:
            raise ValueError(f"Unknown record type: {record_type}")
    
    def get_records_by_date(self, target_date: date, 
                            record_types: Optional[List[str]] = None) -> List[Dict]:
        """按日期查询记录"""
        return self.db.get_records_by_date(target_date, record_types)
    
    def generate_summary(self, summary_type: str, **kwargs) -> str:
        """生成汇总报告"""
        if summary_type == 'daily':
            # 实现每日汇总
            return "每日汇总..."
        return ""
    
    def handle_command(self, command: str, args: list, 
                      context: Dict[str, Any]) -> str:
        """处理命令"""
        if command == '订单查询':
            return "订单查询结果..."
        return f"未知命令: {command}"
```

### 步骤 3: 实现业务配置

创建 `config/new_project_config.py`:

```python
from config.business_config import BusinessConfig
from typing import List, Dict

class NewProjectConfig(BusinessConfig):
    """新项目的业务配置"""
    
    def get_service_types(self) -> List[Dict[str, Any]]:
        return []  # 根据新项目定义
    
    def get_product_categories(self) -> List[str]:
        return ["category_a", "category_b"]
    
    def get_membership_card_types(self) -> List[str]:
        return []  # 如果有会员功能
    
    def get_llm_system_prompt(self) -> str:
        return """你是一个新项目的数据录入助手。
        
## 业务类型
1. 订单：客户下单
2. 支付：客户付款

## 输出格式
返回 JSON 数组...
"""
    
    def get_noise_patterns(self) -> List[str]:
        return [r'^好的$', r'^收到$']
    
    def get_service_keywords(self) -> List[str]:
        return []  # 如果有服务
    
    def get_product_keywords(self) -> List[str]:
        return ['商品A', '商品B']
    
    def get_membership_keywords(self) -> List[str]:
        return []  # 如果有会员
```

### 步骤 4: 定义数据库模型

创建 `db/new_project_models.py`:

```python
from sqlalchemy import Column, Integer, String, DECIMAL, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(50))
    order_date = Column(Date)
    amount = Column(DECIMAL(10, 2))
    # ... 其他字段
```

### 步骤 5: 实现数据库 Repository

创建 `db/new_project_repository.py`:

```python
from db.base_repository import BaseRepository
from db.new_project_models import Base, Order
from typing import Dict, Any, List
from datetime import date

class NewProjectRepository(BaseRepository):
    """新项目的数据库访问层"""
    
    def save_order(self, data: Dict[str, Any], raw_message_id: int) -> int:
        """保存订单"""
        with self.get_session() as session:
            order = Order(
                customer_name=data.get('customer_name'),
                order_date=data.get('date'),
                amount=data.get('amount'),
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return order.id
    
    def get_records_by_date(self, target_date: date, 
                           record_types: List[str] = None) -> List[Dict]:
        """按日期查询记录"""
        with self.get_session() as session:
            orders = session.query(Order).filter(
                Order.order_date == target_date
            ).all()
            
            return [{
                'type': 'order',
                'id': o.id,
                'customer_name': o.customer_name,
                'amount': float(o.amount),
            } for o in orders]
```

### 步骤 6: 修改主程序

修改 `main.py`:

```python
# 导入新项目的适配器和配置
from business.new_project_adapter import NewProjectAdapter
from config.new_project_config import NewProjectConfig
from db.new_project_repository import NewProjectRepository

def main():
    # ... 其他初始化代码 ...
    
    # ⭐ 使用新项目的配置
    business_config = NewProjectConfig()
    
    # ⭐ 使用新项目的数据库
    db_repo = NewProjectRepository()
    db_repo.create_tables()
    
    # ⭐ 使用新项目的业务逻辑适配器
    business_adapter = NewProjectAdapter(db_repo)
    
    # 使用新配置初始化预处理器
    preprocessor = MessagePreProcessor(config=business_config)
    
    # 使用新配置的提示词初始化 LLM
    llm_parser = create_llm_parser(
        system_prompt=business_config.get_llm_system_prompt()
    )
    
    # 其他代码不需要修改！
    pipeline = MessagePipeline(preprocessor, llm_parser, db_repo, business_adapter)
    command_handler = CommandHandler(db_repo, business_adapter)
    # ...
```

## ✅ 检查清单

### 必须实现

- [ ] `business/new_project_adapter.py` - 业务逻辑适配器
- [ ] `config/new_project_config.py` - 业务配置
- [ ] `db/new_project_models.py` - 数据库模型
- [ ] `db/new_project_repository.py` - 数据库访问层
- [ ] 修改 `main.py` 中的适配器实例

### 不需要修改

- [x] `parsing/pipeline.py` - 核心框架
- [x] `core/bot.py` - 核心框架
- [x] `parsing/llm_parser.py` - 核心框架
- [x] `core/command_handler.py` - 核心框架
- [x] `core/scheduler.py` - 核心框架

## 📊 工作量估算

- **业务逻辑适配器**: 1-2小时
- **业务配置**: 30分钟
- **数据库模型**: 1小时
- **数据库 Repository**: 1-2小时
- **修改主程序**: 10分钟

**总计**: 约 4-6 小时即可完成新项目迁移

## 🎯 优势

1. **核心框架完全复用** - 不需要修改 Pipeline、Bot 等核心代码
2. **业务逻辑完全独立** - 通过接口解耦，易于替换
3. **配置可替换** - 业务配置通过接口管理
4. **快速迁移** - 只需实现接口，工作量小

