"""主程序入口"""
import asyncio
import sys
import os
from loguru import logger
from config.settings import settings
from db.repository import DatabaseRepository
from parsing.preprocessor import MessagePreProcessor
from parsing.llm_parser import create_llm_parser
from parsing.pipeline import MessagePipeline
from core.message_router import MessageRouter
from core.command_handler import CommandHandler
from core.bot import WeChatBot, MockWeChatBot
from core.scheduler import Scheduler
from core.business_adapter import BusinessLogicAdapter
from business.therapy_store_adapter import TherapyStoreAdapter


def setup_logging():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="DEBUG"
    )


def main():
    """主函数"""
    setup_logging()
    logger.info("Starting WeChat Business Manager Bot...")
    
    # 检查环境变量
    if not settings.openai_api_key and not settings.anthropic_api_key:
        logger.error("至少需要设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 之一!")
        logger.error("请创建 .env 文件并配置 API Key")
        sys.exit(1)
    
    # 确保数据目录存在
    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 初始化数据库
    logger.info("Initializing database...")
    db_repo = DatabaseRepository()
    db_repo.create_tables()
    
    # 初始化消息预处理
    preprocessor = MessagePreProcessor()
    
    # 初始化 LLM 解析器
    logger.info("Initializing LLM parser...")
    llm_parser = create_llm_parser()
    
    # 初始化业务逻辑适配器（新项目可以替换这里）
    business_adapter: BusinessLogicAdapter = TherapyStoreAdapter(db_repo)
    
    # 初始化消息流水线（通过适配器解耦业务逻辑）
    pipeline = MessagePipeline(preprocessor, llm_parser, db_repo, business_adapter)
    
    # 初始化命令处理器（通过适配器解耦业务逻辑）
    command_handler = CommandHandler(db_repo, business_adapter)
    
    # 初始化消息路由
    router = MessageRouter(pipeline, command_handler, settings.bot_name)
    
    # 初始化微信机器人
    try:
        bot = WeChatBot(router)
        bot.start()
    except Exception as e:
        logger.warning(f"Failed to start WeChat bot: {e}, using mock mode")
        bot = MockWeChatBot(router)
        bot.start()
    
    # 初始化定时任务（通过适配器解耦业务逻辑）
    scheduler = Scheduler(business_adapter, db_repo, bot)
    scheduler.start()
    
    logger.info("Bot is running! Press Ctrl+C to stop.")
    
    # 保持运行
    try:
        # 如果是模拟模式，可以提供一个简单的消息接收接口
        if isinstance(bot, MockWeChatBot):
            logger.info("Mock mode: Use API to send messages")
            # 运行事件循环以支持 scheduler
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.run_forever()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_forever()
        else:
            # 真实模式，等待消息循环
            import time
            while bot.running:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()
        bot.stop()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    main()

