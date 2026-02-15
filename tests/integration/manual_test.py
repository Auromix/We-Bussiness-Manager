#!/usr/bin/env python3
"""
手动集成测试脚本
运行: python tests/integration/manual_test.py
"""
import sys
import os
import asyncio
from datetime import datetime, date

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.repository import DatabaseRepository
from parsing.preprocessor import MessagePreProcessor
from parsing.pipeline import MessagePipeline


class SimpleLLMParser:
    """简单的 LLM 解析器（用于手动测试）"""
    async def parse_message(self, sender, timestamp, content):
        # 简单的规则解析（用于测试）
        if "头疗" in content and "段老师" in content:
            return [{
                "type": "service",
                "date": "2024-01-28",
                "customer_name": "段老师",
                "service_or_product": "头疗",
                "amount": 30,
                "confidence": 0.9
            }]
        elif "理疗" in content and "姚老师" in content:
            return [{
                "type": "service",
                "date": "2024-01-28",
                "customer_name": "姚老师",
                "service_or_product": "理疗",
                "amount": 198,
                "commission": 20,
                "commission_to": "李哥",
                "net_amount": 178,
                "confidence": 0.95
            }]
        elif "开卡" in content:
            return [{
                "type": "membership",
                "date": "2024-01-28",
                "customer_name": "姚老师",
                "card_type": "理疗卡",
                "amount": 1000,
                "confidence": 0.95
            }]
        return [{"type": "noise"}]


async def main():
    print("=" * 60)
    print("手动集成测试 - 完整消息处理流程")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[初始化] 创建数据库和组件...")
    db = DatabaseRepository(database_url="sqlite:///test_integration_manual.db")
    db.create_tables()
    print("  ✅ 数据库初始化完成")
    
    preprocessor = MessagePreProcessor()
    llm_parser = SimpleLLMParser()
    from business.therapy_store_adapter import TherapyStoreAdapter
    business_adapter = TherapyStoreAdapter(db)
    pipeline = MessagePipeline(preprocessor, llm_parser, db, business_adapter)
    print("  ✅ 组件初始化完成")
    
    # 2. 测试消息1：服务消息
    print("\n" + "-" * 60)
    print("[测试1] 处理服务消息: '1.28段老师头疗30'")
    print("-" * 60)
    msg1 = {
        'wechat_msg_id': 'manual_test_001',
        'sender_nickname': '测试用户',
        'sender_wechat_id': 'test_user_001',
        'content': '1.28段老师头疗30',
        'msg_type': 'text',
        'group_id': 'test_group_001',
        'timestamp': datetime(2024, 1, 28, 10, 0, 0),
        'is_at_bot': False
    }
    result1 = await pipeline.process(msg1)
    print(f"  处理状态: {result1.status}")
    print(f"  记录数: {len(result1.records)}")
    if result1.records:
        for i, r in enumerate(result1.records, 1):
            print(f"  记录 {i}:")
            print(f"    - 类型: {r['type']}")
            print(f"    - 置信度: {r['confidence']}")
            print(f"    - 需要确认: {r['needs_confirmation']}")
    
    # 3. 测试消息2：带提成的服务消息
    print("\n" + "-" * 60)
    print("[测试2] 处理带提成的服务消息: '1.28姚老师理疗198-20李哥178'")
    print("-" * 60)
    msg2 = {
        'wechat_msg_id': 'manual_test_002',
        'sender_nickname': '测试用户',
        'content': '1.28姚老师理疗198-20李哥178',
        'timestamp': datetime(2024, 1, 28, 10, 1, 0),
        'is_at_bot': False
    }
    result2 = await pipeline.process(msg2)
    print(f"  处理状态: {result2.status}")
    print(f"  记录数: {len(result2.records)}")
    
    # 4. 测试消息3：会员开卡
    print("\n" + "-" * 60)
    print("[测试3] 处理会员开卡消息: '理疗开卡1000姚老师'")
    print("-" * 60)
    msg3 = {
        'wechat_msg_id': 'manual_test_003',
        'sender_nickname': '测试用户',
        'content': '理疗开卡1000姚老师',
        'timestamp': datetime(2024, 1, 28, 10, 2, 0),
        'is_at_bot': False
    }
    result3 = await pipeline.process(msg3)
    print(f"  处理状态: {result3.status}")
    print(f"  记录数: {len(result3.records)}")
    
    # 5. 测试消息4：噪声消息
    print("\n" + "-" * 60)
    print("[测试4] 处理噪声消息: '接'")
    print("-" * 60)
    msg4 = {
        'wechat_msg_id': 'manual_test_004',
        'sender_nickname': '测试用户',
        'content': '接',
        'timestamp': datetime(2024, 1, 28, 10, 3, 0),
        'is_at_bot': False
    }
    result4 = await pipeline.process(msg4)
    print(f"  处理状态: {result4.status}")
    print(f"  记录数: {len(result4.records)}")
    
    # 6. 验证数据库
    print("\n" + "-" * 60)
    print("[验证] 查询数据库记录")
    print("-" * 60)
    records = db.get_records_by_date(date(2024, 1, 28))
    print(f"  找到 {len(records)} 条记录:")
    for i, r in enumerate(records, 1):
        print(f"  记录 {i}:")
        if r['type'] == 'service':
            print(f"    - 类型: 服务")
            print(f"    - 顾客: {r['customer_name']}")
            print(f"    - 服务: {r['service_type']}")
            print(f"    - 金额: ¥{r['amount']:.0f}")
            if r.get('commission'):
                print(f"    - 提成: ¥{r['commission']:.0f} → {r['commission_to']}")
            print(f"    - 净收入: ¥{r['net_amount']:.0f}")
            print(f"    - 已确认: {'是' if r['confirmed'] else '否'}")
    
    # 7. 测试汇总
    print("\n" + "-" * 60)
    print("[测试5] 生成每日汇总")
    print("-" * 60)
    from services.summary_svc import SummaryService
    summary_svc = SummaryService(db)
    summary = summary_svc.generate_daily_summary(date(2024, 1, 28))
    print(summary)
    
    print("\n" + "=" * 60)
    print("✅ 手动集成测试完成！")
    print("=" * 60)
    print("\n提示: 测试数据库文件: test_integration_manual.db")
    print("可以删除此文件以清理测试数据")


if __name__ == "__main__":
    asyncio.run(main())

