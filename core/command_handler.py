"""命令处理系统"""
import re
from datetime import date, datetime
from typing import List, Optional
from db.repository import DatabaseRepository
from core.business_adapter import BusinessLogicAdapter


# 命令注册表
COMMANDS = {
    # ---- 查询类 ----
    "今日总结": {"handler": "daily_summary", "args": 0, "desc": "生成今日经营数据汇总"},
    "库存总结": {"handler": "inventory_summary", "args": 0, "desc": "显示当前库存情况"},
    "会员总结": {"handler": "membership_summary", "args": 0, "desc": "显示会员充值/余额汇总"},
    "本月总结": {"handler": "monthly_summary", "args": 0, "desc": "生成本月经营报表"},
    "查询": {"handler": "query_records", "args": "*", "desc": "查询XX老师/查询1月28日"},
    
    # ---- 操作类 ----
    "确认": {"handler": "confirm_records", "args": 0, "desc": "确认今日所有待确认记录"},
    "撤销": {"handler": "undo_last", "args": "?", "desc": "撤销上一条/撤销指定记录"},
    "修改": {"handler": "modify_record", "args": "*", "desc": "修改 #记录ID 金额为XX"},
    
    # ---- 库存管理 ----
    "入库": {"handler": "restock", "args": "*", "desc": "入库 泡脚液 100瓶"},
    "库存调整": {"handler": "adjust_inventory", "args": "*", "desc": "手动调整库存"},
    
    # ---- 帮助 ----
    "帮助": {"handler": "show_help", "args": 0, "desc": "显示所有可用命令"},
}


class CommandHandler:
    """命令处理器
    
    通过 BusinessLogicAdapter 解耦业务逻辑，支持不同项目的业务逻辑替换
    """
    
    def __init__(self, db_repo: DatabaseRepository, business_adapter: BusinessLogicAdapter):
        self.db = db_repo
        self.business_adapter = business_adapter  # 业务逻辑适配器
    
    async def daily_summary(self, group_id: str, args: List[str]) -> str:
        """生成今日汇总"""
        return self.business_adapter.generate_summary('daily', date=date.today())
    
    async def inventory_summary(self, group_id: str, args: List[str]) -> str:
        """库存总结"""
        return self.business_adapter.generate_summary('inventory')
    
    async def membership_summary(self, group_id: str, args: List[str]) -> str:
        """会员总结"""
        return self.business_adapter.generate_summary('membership')
    
    async def monthly_summary(self, group_id: str, args: List[str]) -> str:
        """本月总结"""
        today = date.today()
        return self.business_adapter.generate_summary('monthly', year=today.year, month=today.month)
    
    async def query_records(self, group_id: str, args: List[str]) -> str:
        """查询记录"""
        if not args:
            return "❓ 请指定查询条件，如：查询 段老师 或 查询 1月28日"
        
        query_text = " ".join(args)
        
        # 尝试解析日期
        date_match = re.search(r'(\d{1,2})[月/.](\d{1,2})', query_text)
        if date_match:
            month, day = int(date_match.group(1)), int(date_match.group(2))
            today = date.today()
            target_date = date(today.year, month, day)
            records = self.db.get_records_by_date(target_date)
            
            if not records:
                return f"📅 {target_date.strftime('%Y年%m月%d日')} 暂无记录"
            
            result = f"📅 {target_date.strftime('%Y年%m月%d日')} 记录:\n"
            for r in records:
                if r['type'] == 'service':
                    result += f"  {r['customer_name']} {r['service_type']} ¥{r['amount']:.0f}\n"
                elif r['type'] == 'product_sale':
                    result += f"  {r['customer_name']} {r['product_name']} ¥{r['total_amount']:.0f}\n"
            return result
        
        # 尝试查询顾客
        if "老师" in query_text or "哥" in query_text or "姐" in query_text:
            # TODO: 实现按顾客查询
            return f"🔍 查询 {query_text} 的功能开发中..."
        
        return "❓ 无法识别查询条件，请使用：查询 XX老师 或 查询 1月28日"
    
    async def confirm_records(self, group_id: str, args: List[str]) -> str:
        """确认今日所有待确认记录"""
        # TODO: 实现确认逻辑
        return "✅ 确认功能开发中..."
    
    async def undo_last(self, group_id: str, args: List[str]) -> str:
        """撤销上一条记录"""
        # TODO: 实现撤销逻辑
        return "↩️ 撤销功能开发中..."
    
    async def modify_record(self, group_id: str, args: List[str]) -> str:
        """修改记录"""
        # TODO: 实现修改逻辑
        return "✏️ 修改功能开发中..."
    
    async def restock(self, group_id: str, args: List[str]) -> str:
        """入库"""
        return self.business_adapter.handle_command('restock', args, {'group_id': group_id})
    
    async def adjust_inventory(self, group_id: str, args: List[str]) -> str:
        """库存调整"""
        return self.business_adapter.handle_command('adjust_inventory', args, {'group_id': group_id})
    
    async def show_help(self, group_id: str, args: List[str]) -> str:
        """显示帮助"""
        help_text = "📖 可用命令：\n\n"
        for cmd, config in COMMANDS.items():
            help_text += f"• {cmd}: {config['desc']}\n"
        return help_text

