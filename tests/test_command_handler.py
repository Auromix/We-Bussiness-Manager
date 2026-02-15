"""测试命令处理器"""
import pytest
from datetime import date
from core.command_handler import CommandHandler
from db.repository import DatabaseRepository


class TestCommandHandler:
    """命令处理器测试"""
    
    @pytest.fixture
    def handler(self, temp_db, mock_business_adapter):
        """创建命令处理器实例"""
        return CommandHandler(temp_db, mock_business_adapter)
    
    @pytest.mark.asyncio
    async def test_daily_summary_empty(self, handler):
        """测试空数据的每日汇总"""
        result = await handler.daily_summary("test_group", [])
        
        assert "经营日报" in result
        assert "理疗服务" in result
        assert "产品销售" in result
    
    @pytest.mark.asyncio
    async def test_daily_summary_with_data(self, handler, temp_db):
        """测试有数据的每日汇总"""
        # 创建一些测试数据
        for i, customer_name in enumerate(["段老师", "姚老师"]):
            record_data = {
                "customer_name": customer_name,
                "service_or_product": "头疗",
                "date": date.today().isoformat(),
                "amount": 30 + i * 10,
                "confidence": 0.95,
                "confirmed": True
            }
            msg_id = temp_db.save_raw_message({
                'wechat_msg_id': f'test_msg_{i+20}',
                'sender_nickname': '测试用户',
                'content': f'{customer_name}头疗{30 + i * 10}',
                'timestamp': date.today()
            })
            temp_db.save_service_record(record_data, msg_id)
        
        result = await handler.daily_summary("test_group", [])
        
        assert "经营日报" in result
        assert "段老师" in result
        assert "姚老师" in result
        assert "头疗" in result
    
    @pytest.mark.asyncio
    async def test_inventory_summary(self, handler):
        """测试库存总结"""
        result = await handler.inventory_summary("test_group", [])
        assert "库存" in result
    
    @pytest.mark.asyncio
    async def test_membership_summary(self, handler):
        """测试会员总结"""
        result = await handler.membership_summary("test_group", [])
        assert "会员" in result
    
    @pytest.mark.asyncio
    async def test_monthly_summary(self, handler):
        """测试月度总结"""
        result = await handler.monthly_summary("test_group", [])
        assert "月报" in result or "月" in result
    
    @pytest.mark.asyncio
    async def test_query_records_by_date(self, handler, temp_db):
        """测试按日期查询记录"""
        from datetime import datetime
        # 创建测试数据 - 使用今天日期以确保查询能找到
        today = date.today()
        record_data = {
            "customer_name": "段老师",
            "service_or_product": "头疗",
            "date": today.isoformat(),
            "amount": 30,
            "confidence": 0.95
        }
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_030',
            'sender_nickname': '测试用户',
            'content': f'{today.month}.{today.day}段老师头疗30',
            'timestamp': datetime.combine(today, datetime.min.time())
        })
        temp_db.save_service_record(record_data, msg_id)
        
        # 使用今天的日期查询
        month_day = f"{today.month}月{today.day}日"
        result = await handler.query_records("test_group", [month_day])
        
        assert "段老师" in result
        assert "头疗" in result or "30" in result
    
    @pytest.mark.asyncio
    async def test_query_records_no_args(self, handler):
        """测试查询无参数"""
        result = await handler.query_records("test_group", [])
        assert "请指定查询条件" in result
    
    @pytest.mark.asyncio
    async def test_show_help(self, handler):
        """测试显示帮助"""
        result = await handler.show_help("test_group", [])
        assert "可用命令" in result
        assert "今日总结" in result
        assert "帮助" in result
    
    @pytest.mark.asyncio
    async def test_restock(self, handler):
        """测试入库命令"""
        result = await handler.restock("test_group", ["泡脚液", "100"])
        assert "入库" in result or "已入库" in result
    
    @pytest.mark.asyncio
    async def test_restock_invalid(self, handler):
        """测试入库命令无效参数"""
        result = await handler.restock("test_group", ["泡脚液"])
        assert "格式" in result or "❓" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

