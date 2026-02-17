"""业务命令处理器 - 处理具体的业务命令逻辑

这个模块包含所有业务相关的命令处理逻辑，与 interface 层解耦
"""
import re
from datetime import date
from typing import List, Dict, Any
from core.business_adapter import BusinessLogicAdapter
from database import DatabaseManager
from business.commands import COMMANDS, get_help_text


class BusinessCommandHandler:
    """业务命令处理器
    
    处理所有业务相关的命令逻辑，不依赖具体的接口实现
    """
    
    def __init__(self, business_adapter: BusinessLogicAdapter, db_repo: DatabaseManager):
        self.business_adapter = business_adapter
        self.db = db_repo
    
    async def handle_command(self, command: str, args: List[str], context: Dict[str, Any]) -> str:
        """处理命令
        
        Args:
            command: 命令名称
            args: 命令参数
            context: 上下文信息（如 group_id）
            
        Returns:
            命令响应文本
        """
        # 获取命令配置
        cmd_config = COMMANDS.get(command)
        if not cmd_config:
            return "❓ 未识别的命令，回复 @机器人 帮助 查看可用指令"
        
        # 调用对应的处理方法
        handler_name = cmd_config.get('handler')
        if not hasattr(self, handler_name):
            return f"❓ 命令处理器 {handler_name} 未实现"
        
        handler = getattr(self, handler_name)
        return await handler(context.get('group_id', ''), args)
    
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
            records = self.business_adapter.get_records_by_date(target_date)
            
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
        return get_help_text()

