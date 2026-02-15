"""测试汇总服务"""
import pytest
from datetime import date, timedelta
from services.summary_svc import SummaryService
from db.repository import DatabaseRepository


class TestSummaryService:
    """汇总服务测试"""
    
    @pytest.fixture
    def summary_svc(self, temp_db):
        """创建汇总服务实例"""
        return SummaryService(temp_db)
    
    def test_generate_daily_summary_empty(self, summary_svc):
        """测试空数据的每日汇总"""
        result = summary_svc.generate_daily_summary(date.today())
        
        assert "经营日报" in result
        assert "理疗服务" in result
        assert "产品销售" in result
        assert "0笔" in result or "0" in result
    
    def test_generate_daily_summary_with_service(self, summary_svc, temp_db):
        """测试有服务记录的每日汇总"""
        today = date.today()
        
        # 创建服务记录
        for i, customer_name in enumerate(["段老师", "姚老师"]):
            record_data = {
                "customer_name": customer_name,
                "service_or_product": "头疗",
                "date": today.isoformat(),
                "amount": 30 + i * 10,
                "confidence": 0.95,
                "confirmed": True
            }
            msg_id = temp_db.save_raw_message({
                'wechat_msg_id': f'test_msg_{i+40}',
                'sender_nickname': '测试用户',
                'content': f'{customer_name}头疗{30 + i * 10}',
                'timestamp': today
            })
            temp_db.save_service_record(record_data, msg_id)
        
        result = summary_svc.generate_daily_summary(today)
        
        assert "经营日报" in result
        assert "2笔" in result or "2" in result
        assert "段老师" in result
        assert "姚老师" in result
        assert "头疗" in result
    
    def test_generate_daily_summary_with_commission(self, summary_svc, temp_db):
        """测试带提成的每日汇总"""
        today = date.today()
        
        record_data = {
            "customer_name": "姚老师",
            "service_or_product": "理疗",
            "date": today.isoformat(),
            "amount": 198,
            "commission": 20,
            "commission_to": "李哥",
            "net_amount": 178,
            "confidence": 0.95
        }
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_050',
            'sender_nickname': '测试用户',
            'content': '理疗198-20李哥178',
            'timestamp': today
        })
        temp_db.save_service_record(record_data, msg_id)
        
        result = summary_svc.generate_daily_summary(today)
        
        assert "提成" in result
        assert "李哥" in result
    
    def test_generate_daily_summary_with_product(self, summary_svc, temp_db):
        """测试有商品销售的每日汇总"""
        today = date.today()
        
        sale_data = {
            "service_or_product": "泡脚液",
            "customer_name": "段老师",
            "date": today.isoformat(),
            "amount": 100,
            "quantity": 1,
            "confidence": 0.9
        }
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_060',
            'sender_nickname': '测试用户',
            'content': '泡脚液100段老师',
            'timestamp': today
        })
        temp_db.save_product_sale(sale_data, msg_id)
        
        result = summary_svc.generate_daily_summary(today)
        
        assert "产品销售" in result
        assert "泡脚液" in result
    
    def test_generate_daily_summary_unconfirmed(self, summary_svc, temp_db):
        """测试有待确认记录的每日汇总"""
        today = date.today()
        
        record_data = {
            "customer_name": "段老师",
            "service_or_product": "头疗",
            "date": today.isoformat(),
            "amount": 30,
            "confidence": 0.5,  # 低置信度
            "confirmed": False
        }
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_070',
            'sender_nickname': '测试用户',
            'content': '段老师头疗30',
            'timestamp': today
        })
        temp_db.save_service_record(record_data, msg_id)
        
        result = summary_svc.generate_daily_summary(today)
        
        assert "待确认" in result or "⏳" in result
    
    def test_generate_monthly_summary(self, summary_svc):
        """测试月度汇总"""
        today = date.today()
        result = summary_svc.generate_monthly_summary(today.year, today.month)
        
        assert "月报" in result or "月" in result
        assert str(today.year) in result
        assert str(today.month) in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

