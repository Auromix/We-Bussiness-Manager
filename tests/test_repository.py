"""测试数据库访问层"""
import pytest
from datetime import date, datetime
from db.repository import DatabaseRepository
from db.models import Employee, Customer, ServiceType, ServiceRecord, Product, ProductSale, Membership


class TestDatabaseRepository:
    """数据库访问层测试"""
    
    def test_save_raw_message(self, temp_db):
        """测试保存原始消息"""
        msg_data = {
            'wechat_msg_id': 'test_msg_001',
            'sender_nickname': '测试用户',
            'content': '1.28段老师头疗30',
            'timestamp': datetime(2024, 1, 28, 10, 0, 0),
            'is_at_bot': False
        }
        
        msg_id = temp_db.save_raw_message(msg_data)
        assert msg_id > 0
        
        # 测试去重
        msg_id2 = temp_db.save_raw_message(msg_data)
        assert msg_id == msg_id2
    
    def test_get_or_create_customer(self, temp_db):
        """测试获取或创建顾客"""
        customer = temp_db.get_or_create_customer("段老师")
        assert customer.id > 0
        assert customer.name == "段老师"
        
        # 再次获取应该返回同一个
        customer2 = temp_db.get_or_create_customer("段老师")
        assert customer.id == customer2.id
    
    def test_get_or_create_employee(self, temp_db):
        """测试获取或创建员工"""
        employee = temp_db.get_or_create_employee("叶维忠", "六亿（叶维忠）")
        assert employee.id > 0
        assert employee.name == "叶维忠"
        assert employee.wechat_nickname == "六亿（叶维忠）"
    
    def test_get_or_create_service_type(self, temp_db):
        """测试获取或创建服务类型"""
        service_type = temp_db.get_or_create_service_type("头疗", 30.0, "therapy")
        assert service_type.id > 0
        assert service_type.name == "头疗"
        assert float(service_type.default_price) == 30.0
    
    def test_save_service_record(self, temp_db):
        """测试保存服务记录"""
        # 先创建相关实体
        customer = temp_db.get_or_create_customer("段老师")
        service_type = temp_db.get_or_create_service_type("头疗", 30.0)
        
        record_data = {
            "customer_name": "段老师",
            "service_or_product": "头疗",
            "date": "2024-01-28",
            "amount": 30,
            "confidence": 0.95,
            "confirmed": True
        }
        
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_002',
            'sender_nickname': '测试用户',
            'content': '1.28段老师头疗30',
            'timestamp': datetime(2024, 1, 28, 10, 0, 0)
        })
        
        record_id = temp_db.save_service_record(record_data, msg_id)
        assert record_id > 0
        
        # 验证记录
        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter(ServiceRecord.id == record_id).first()
            assert record is not None
            assert record.customer_id == customer.id
            assert record.service_type_id == service_type.id
            assert float(record.amount) == 30
            assert record.service_date == date(2024, 1, 28)
    
    def test_save_service_record_with_commission(self, temp_db):
        """测试保存带提成的服务记录"""
        record_data = {
            "customer_name": "姚老师",
            "service_or_product": "理疗",
            "date": "2024-01-28",
            "amount": 198,
            "commission": 20,
            "commission_to": "李哥",
            "net_amount": 178,
            "confidence": 0.95
        }
        
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_003',
            'sender_nickname': '测试用户',
            'content': '1.28姚老师理疗198-20李哥178',
            'timestamp': datetime(2024, 1, 28, 10, 0, 0)
        })
        
        record_id = temp_db.save_service_record(record_data, msg_id)
        
        with temp_db.get_session() as session:
            record = session.query(ServiceRecord).filter(ServiceRecord.id == record_id).first()
            assert float(record.commission_amount) == 20
            assert record.commission_to == "李哥"
            assert float(record.net_amount) == 178
    
    def test_get_records_by_date(self, temp_db):
        """测试按日期获取记录"""
        # 创建几条记录
        for i, customer_name in enumerate(["段老师", "姚老师"]):
            record_data = {
                "customer_name": customer_name,
                "service_or_product": "头疗",
                "date": "2024-01-28",
                "amount": 30 + i * 10,
                "confidence": 0.95
            }
            msg_id = temp_db.save_raw_message({
                'wechat_msg_id': f'test_msg_{i+10}',
                'sender_nickname': '测试用户',
                'content': f'1.28{customer_name}头疗{30 + i * 10}',
                'timestamp': datetime(2024, 1, 28, 10, 0, 0)
            })
            temp_db.save_service_record(record_data, msg_id)
        
        # 查询记录
        records = temp_db.get_records_by_date(date(2024, 1, 28))
        assert len(records) == 2
        assert all(r["type"] == "service" for r in records)
        assert any(r["customer_name"] == "段老师" for r in records)
        assert any(r["customer_name"] == "姚老师" for r in records)
    
    def test_save_product_sale(self, temp_db):
        """测试保存商品销售记录"""
        sale_data = {
            "service_or_product": "泡脚液",
            "customer_name": "段老师",
            "date": "2024-01-28",
            "amount": 100,
            "quantity": 1,
            "confidence": 0.9
        }
        
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_004',
            'sender_nickname': '测试用户',
            'content': '泡脚液100段老师',
            'timestamp': datetime(2024, 1, 28, 10, 0, 0)
        })
        
        sale_id = temp_db.save_product_sale(sale_data, msg_id)
        assert sale_id > 0
    
    def test_save_membership(self, temp_db):
        """测试保存会员卡记录"""
        membership_data = {
            "customer_name": "姚老师",
            "card_type": "理疗卡",
            "date": "2024-01-28",
            "amount": 1000
        }
        
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_005',
            'sender_nickname': '测试用户',
            'content': '理疗开卡1000姚老师',
            'timestamp': datetime(2024, 1, 28, 10, 0, 0)
        })
        
        membership_id = temp_db.save_membership(membership_data, msg_id)
        assert membership_id > 0
        
        with temp_db.get_session() as session:
            membership = session.query(Membership).filter(Membership.id == membership_id).first()
            assert float(membership.total_amount) == 1000
            assert float(membership.balance) == 1000
            assert membership.card_type == "理疗卡"
    
    def test_update_parse_status(self, temp_db):
        """测试更新解析状态"""
        msg_id = temp_db.save_raw_message({
            'wechat_msg_id': 'test_msg_006',
            'sender_nickname': '测试用户',
            'content': '测试消息',
            'timestamp': datetime(2024, 1, 28, 10, 0, 0)
        })
        
        temp_db.update_parse_status(msg_id, 'parsed', result={"type": "service"})
        
        with temp_db.get_session() as session:
            from db.models import RawMessage
            msg = session.query(RawMessage).filter(RawMessage.id == msg_id).first()
            assert msg.parse_status == 'parsed'
            assert msg.parse_result == {"type": "service"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

