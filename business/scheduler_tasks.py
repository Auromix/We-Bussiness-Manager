"""定时任务业务逻辑 - 项目特定的定时任务实现

所有定时任务的具体业务逻辑都在这里，与 core/scheduler 解耦
"""
from datetime import date
from typing import Callable, Optional
from loguru import logger
from db.repository import DatabaseRepository
from core.business_adapter import BusinessLogicAdapter


class SchedulerTasks:
    """定时任务业务逻辑
    
    包含所有定时任务的具体业务实现，不依赖具体的接口实现
    """
    
    def __init__(
        self,
        business_adapter: BusinessLogicAdapter,
        db_repo: DatabaseRepository,
        message_sender: Optional[Callable[[str, str], None]] = None
    ):
        """
        Args:
            business_adapter: 业务逻辑适配器
            db_repo: 数据库仓库
            message_sender: 消息发送回调函数，签名: (target: str, content: str) -> None
        """
        self.business_adapter = business_adapter
        self.db = db_repo
        self.message_sender = message_sender
    
    async def daily_summary_task(self, target_groups: Optional[list] = None):
        """每日汇总任务
        
        Args:
            target_groups: 目标群组列表，如果为 None 则不发送消息
        """
        try:
            logger.info("Running daily summary task")
            today = date.today()
            summary_text = self.business_adapter.generate_summary('daily', date=today)
            
            # 保存汇总到数据库
            summary_data = {
                'summary_text': summary_text,
                'confirmed': False
            }
            self.db.save_daily_summary(today, summary_data)
            
            # 发送消息（如果提供了消息发送器和目标群组）
            if self.message_sender and target_groups:
                try:
                    for group_id in target_groups:
                        self.message_sender(group_id.strip(), summary_text)
                        logger.info(f"Daily summary sent to group {group_id}")
                except Exception as e:
                    logger.error(f"Failed to send daily summary: {e}")
            else:
                logger.info("No message sender or target groups configured, summary saved only")
                
        except Exception as e:
            logger.error(f"Daily summary task failed: {e}")
            raise

