"""
健康理疗门店业务逻辑适配器实现

这是当前项目的业务逻辑实现。
新项目可以创建类似的适配器，实现 BusinessLogicAdapter 接口。
"""
from typing import Dict, Any, Optional, List
from datetime import date
from core.business_adapter import BusinessLogicAdapter
from database import DatabaseManager
from services.summary_svc import SummaryService
from services.inventory_svc import InventoryService
from services.membership_svc import MembershipService
from loguru import logger


class TherapyStoreAdapter(BusinessLogicAdapter):
    """健康理疗门店业务逻辑适配器"""
    
    def __init__(self, db_repo: DatabaseManager):
        self.db = db_repo
        self.summary_svc = SummaryService(db_repo)
        self.inventory_svc = InventoryService(db_repo)
        self.membership_svc = MembershipService(db_repo)
    
    def save_business_record(self, record_type: str, data: Dict[str, Any], 
                            raw_message_id: int, confirmed: bool) -> int:
        """保存业务记录"""
        data['confirmed'] = confirmed
        
        if record_type == 'service':
            return self.db.save_service_record(data, raw_message_id)
        elif record_type == 'product_sale':
            return self.db.save_product_sale(data, raw_message_id)
        elif record_type == 'membership':
            return self.db.save_membership(data, raw_message_id)
        elif record_type == 'correction':
            # 修正记录需要特殊处理
            logger.warning(f"Correction record not yet implemented: {data}")
            return 0
        else:
            raise ValueError(f"Unknown record type: {record_type}")
    
    def get_records_by_date(self, target_date: date, record_types: Optional[List[str]] = None) -> List[Dict]:
        """按日期查询记录"""
        records = self.db.get_daily_records(target_date)
        
        if record_types:
            # 过滤指定类型
            records = [r for r in records if r.get('type') in record_types]
        
        return records
    
    def generate_summary(self, summary_type: str, **kwargs) -> str:
        """生成汇总报告"""
        if summary_type == 'daily':
            target_date = kwargs.get('date', date.today())
            return self.summary_svc.generate_daily_summary(target_date)
        elif summary_type == 'monthly':
            year = kwargs.get('year', date.today().year)
            month = kwargs.get('month', date.today().month)
            return self.summary_svc.generate_monthly_summary(year, month)
        elif summary_type == 'inventory':
            return self.inventory_svc.get_inventory_summary()
        elif summary_type == 'membership':
            return self.membership_svc.get_membership_summary()
        else:
            return f"未知的汇总类型: {summary_type}"
    
    def handle_command(self, command: str, args: list, context: Dict[str, Any]) -> str:
        """处理命令"""
        # 这里可以添加项目特定的命令处理逻辑
        # 目前委托给 CommandHandler，但可以在这里扩展
        
        if command == 'restock':
            if len(args) < 2:
                return "❓ 格式：入库 商品名 数量"
            product_name = args[0]
            try:
                quantity = int(args[1])
                return self.inventory_svc.restock(product_name, quantity)
            except ValueError:
                return "❓ 数量必须是数字"
        
        elif command == 'adjust_inventory':
            if len(args) < 2:
                return "❓ 格式：库存调整 商品名 数量"
            product_name = args[0]
            try:
                quantity = int(args[1])
                reason = " ".join(args[2:]) if len(args) > 2 else ""
                return self.inventory_svc.adjust_inventory(product_name, quantity, reason)
            except ValueError:
                return "❓ 数量必须是数字"
        
        # 其他命令通过 generate_summary 处理
        command_map = {
            '今日总结': ('daily', {}),
            '本月总结': ('monthly', {}),
            '库存总结': ('inventory', {}),
            '会员总结': ('membership', {}),
        }
        
        if command in command_map:
            summary_type, kwargs = command_map[command]
            return self.generate_summary(summary_type, **kwargs)
        
        return f"未知命令: {command}"

