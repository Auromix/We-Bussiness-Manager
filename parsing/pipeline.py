"""消息处理流水线"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from parsing.preprocessor import MessagePreProcessor
from parsing.llm_parser import LLMParser
from database import DatabaseManager
from core.business_adapter import BusinessLogicAdapter


class ProcessResult:
    """处理结果"""
    def __init__(self, status: str, records: Optional[List[Dict]] = None, error: Optional[str] = None):
        self.status = status  # ignored / parsed / failed
        self.records = records or []
        self.error = error


class MessagePipeline:
    """
    完整的消息处理流水线:
    原始消息 → 噪声过滤 → 预处理 → LLM解析 → 置信度检查 → 入库 → (可选)确认请求
    
    通过 BusinessLogicAdapter 解耦业务逻辑，支持不同项目的业务逻辑替换
    """
    
    def __init__(self, preprocessor: MessagePreProcessor, llm_parser: LLMParser, 
                 db_repo: DatabaseManager, business_adapter: BusinessLogicAdapter):
        self.preprocessor = preprocessor
        self.llm_parser = llm_parser
        self.db = db_repo
        self.business_adapter = business_adapter  # 业务逻辑适配器
        self.CONFIDENCE_THRESHOLD = 0.7  # 低于此值需人工确认
    
    async def process(self, raw_msg: Dict[str, Any]) -> ProcessResult:
        """处理原始消息"""
        try:
            # 1. 存储原始消息
            msg_id = self.db.save_raw_message(raw_msg)
            
            # 2. 噪声过滤
            if self.preprocessor.is_noise(raw_msg['content']):
                self.db.update_parse_status(msg_id, 'ignored')
                return ProcessResult(status='ignored')
            
            # 3. 粗分类（可选，用于日志）
            intent = self.preprocessor.classify_intent(raw_msg['content'])
            logger.debug(f"Message intent: {intent}, content: {raw_msg['content'][:50]}")
            
            # 4. LLM 结构化提取
            try:
                records = await self.llm_parser.parse_message(
                    sender=raw_msg['sender_nickname'],
                    timestamp=raw_msg['timestamp'].isoformat() if isinstance(raw_msg['timestamp'], datetime) else str(raw_msg['timestamp']),
                    content=raw_msg['content']
                )
            except Exception as e:
                logger.error(f"LLM parsing failed: {e}")
                self.db.update_parse_status(msg_id, 'failed', error=str(e))
                return ProcessResult(status='failed', error=str(e))
            
            # 5. 处理每条解析结果
            results = []
            for record in records:
                # 验证记录格式
                if not isinstance(record, dict):
                    logger.warning(f"Invalid record format: {record}")
                    continue
                
                record_type = record.get('type')
                if not record_type:
                    logger.warning(f"Record missing 'type' field: {record}")
                    continue
                
                if record_type == 'noise':
                    self.db.update_parse_status(msg_id, 'ignored')
                    continue
                
                # 6. 置信度检查
                confidence = record.get('confidence', 0.5)
                needs_confirmation = confidence < self.CONFIDENCE_THRESHOLD
                
                # 7. 添加记录人信息
                record['recorder_nickname'] = raw_msg.get('sender_nickname')
                
                # 8. 入库（通过业务逻辑适配器）
                try:
                    db_record_id = self.business_adapter.save_business_record(
                        record_type=record_type,
                        data=record,
                        raw_message_id=msg_id,
                        confirmed=not needs_confirmation
                    )
                    
                    results.append({
                        'record_id': db_record_id,
                        'type': record['type'],
                        'needs_confirmation': needs_confirmation,
                        'confidence': confidence,
                        'data': record
                    })
                except Exception as e:
                    logger.error(f"Failed to save record: {e}, record: {record}")
                    continue
            
            # 9. 更新消息解析状态
            if results:
                self.db.update_parse_status(msg_id, 'parsed', result=records)
            else:
                self.db.update_parse_status(msg_id, 'ignored')
            
            return ProcessResult(status='parsed', records=results)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return ProcessResult(status='failed', error=str(e))
    

