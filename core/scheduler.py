"""定时任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, datetime
from loguru import logger
from db.repository import DatabaseRepository
from config.settings import settings
from core.bot import WeChatBot
from core.business_adapter import BusinessLogicAdapter
import asyncio


class Scheduler:
    """定时任务调度器
    
    通过 BusinessLogicAdapter 解耦业务逻辑
    """
    
    def __init__(self, business_adapter: BusinessLogicAdapter, db_repo: DatabaseRepository, bot: WeChatBot = None):
        self.business_adapter = business_adapter
        self.db = db_repo
        self.bot = bot
        # 使用默认事件循环或创建新的事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        self.scheduler = AsyncIOScheduler(event_loop=loop)
    
    def start(self):
        """启动调度器"""
        # 解析每日汇总时间
        try:
            hour, minute = map(int, settings.daily_summary_time.split(':'))
        except:
            hour, minute = 21, 0
        
        # 添加每日汇总任务
        self.scheduler.add_job(
            self._daily_summary_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_summary',
            name='每日汇总',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started, daily summary at {hour:02d}:{minute:02d}")
    
    async def _daily_summary_job(self):
        """每日汇总任务"""
        try:
            logger.info("Running daily summary job")
            today = date.today()
            summary_text = self.business_adapter.generate_summary('daily', date=today)
            
            # 保存汇总到数据库
            summary_data = {
                'summary_text': summary_text,
                'confirmed': False
            }
            self.db.save_daily_summary(today, summary_data)
            
            # 发送到微信群（如果有bot实例）
            if self.bot and self.bot.target_group_ids:
                for group_id in self.bot.target_group_ids:
                    self.bot.send_message(group_id, summary_text)
                    logger.info(f"Daily summary sent to group {group_id}")
            else:
                logger.info("No bot or group configured, summary saved only")
                
        except Exception as e:
            logger.error(f"Daily summary job failed: {e}")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

