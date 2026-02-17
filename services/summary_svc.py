"""汇总报表服务"""
from datetime import date, datetime, timedelta
from typing import Dict, List
from database import DatabaseManager


class SummaryService:
    """汇总服务"""
    
    def __init__(self, db_repo: DatabaseManager):
        self.db = db_repo
    
    def generate_daily_summary(self, target_date: date = None) -> str:
        """生成每日汇总报告"""
        if target_date is None:
            target_date = date.today()
        
        records = self.db.get_daily_records(target_date)
        
        service_records = [r for r in records if r['type'] == 'service']
        product_records = [r for r in records if r['type'] == 'product_sale']
        
        total_service = sum(r['net_amount'] for r in service_records)
        total_product = sum(r['total_amount'] for r in product_records)
        total_commission = sum(r.get('commission', 0) or 0 for r in service_records)
        unconfirmed = sum(1 for r in records if not r['confirmed'])
        
        summary = f"""📊 {target_date.strftime('%Y年%m月%d日')} 经营日报

💆 理疗服务: {len(service_records)}笔, 收入 ¥{total_service:.0f}
🛒 产品销售: {len(product_records)}笔, 收入 ¥{total_product:.0f}
💰 提成支出: ¥{total_commission:.0f}
━━━━━━━━━━━━━
📈 今日净收入: ¥{total_service + total_product - total_commission:.0f}

服务明细:
"""
        for r in service_records:
            confirm_mark = "✅" if r['confirmed'] else "⏳"
            summary += f"  {confirm_mark} {r['customer_name']} {r['service_type']} ¥{r['amount']:.0f}"
            if r.get('commission'):
                summary += f" (提成¥{r['commission']:.0f}→{r['commission_to']})"
            summary += "\n"
        
        if product_records:
            summary += "\n产品销售明细:\n"
            for r in product_records:
                confirm_mark = "✅" if r['confirmed'] else "⏳"
                summary += f"  {confirm_mark} {r['customer_name']} {r['product_name']} x{r['quantity']} ¥{r['total_amount']:.0f}\n"
        
        if unconfirmed > 0:
            summary += f"\n⚠️ {unconfirmed}条记录待确认，请回复 @机器人 确认"
        
        return summary
    
    def generate_monthly_summary(self, year: int, month: int) -> str:
        """生成月度汇总"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # 汇总所有日期
        total_service = 0
        total_product = 0
        total_commission = 0
        service_count = 0
        product_count = 0
        
        current_date = start_date
        while current_date <= end_date:
            records = self.db.get_daily_records(current_date)
            service_records = [r for r in records if r['type'] == 'service']
            product_records = [r for r in records if r['type'] == 'product_sale']
            
            total_service += sum(r['net_amount'] for r in service_records)
            total_product += sum(r['total_amount'] for r in product_records)
            total_commission += sum(r.get('commission', 0) or 0 for r in service_records)
            service_count += len(service_records)
            product_count += len(product_records)
            
            current_date += timedelta(days=1)
        
        summary = f"""📊 {year}年{month}月 经营月报

💆 理疗服务: {service_count}笔, 收入 ¥{total_service:.0f}
🛒 产品销售: {product_count}笔, 收入 ¥{total_product:.0f}
💰 提成支出: ¥{total_commission:.0f}
━━━━━━━━━━━━━
📈 本月净收入: ¥{total_service + total_product - total_commission:.0f}
"""
        return summary

