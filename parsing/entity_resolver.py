"""实体消歧（"段老师"→ customer_id）"""
from typing import Optional
from db.repository import DatabaseRepository


class EntityResolver:
    """实体解析器 - 将自然语言中的实体名称映射到数据库ID"""
    
    def __init__(self, db_repo: DatabaseRepository):
        self.db = db_repo
    
    def resolve_customer(self, name: str) -> int:
        """解析顾客名称，返回 customer_id"""
        customer = self.db.get_or_create_customer(name)
        return customer.id
    
    def resolve_employee(self, name: str, wechat_nickname: Optional[str] = None) -> int:
        """解析员工名称，返回 employee_id"""
        employee = self.db.get_or_create_employee(name, wechat_nickname)
        return employee.id
    
    def resolve_service_type(self, name: str) -> int:
        """解析服务类型，返回 service_type_id"""
        service_type = self.db.get_or_create_service_type(name)
        return service_type.id

