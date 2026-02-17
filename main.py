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
from interface import InterfaceManager
from interface.wechat import WeChatBot, WeChatMessageRouter
from core.scheduler import Scheduler
from core.business_adapter import BusinessLogicAdapter
from business.therapy_store_adapter import TherapyStoreAdapter
from business.command_handler import BusinessCommandHandler
from business.scheduler_tasks import SchedulerTasks


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
    
    # 初始化 LLM 解析器（可选择启用函数调用）
    logger.info("Initializing LLM parser...")
    # 如果需要启用函数调用，传入 db_repo 和 enable_function_calling=True
    # 这样 Agent 就可以调用仓库函数进行查询等操作
    enable_function_calling = os.getenv("ENABLE_FUNCTION_CALLING", "false").lower() == "true"
    llm_parser = create_llm_parser(
        db_repo=db_repo if enable_function_calling else None,
        enable_function_calling=enable_function_calling
    )
    if enable_function_calling:
        logger.info("Function calling enabled - Agent can call repository functions")
    
    # 初始化业务逻辑适配器（新项目可以替换这里）
    business_adapter: BusinessLogicAdapter = TherapyStoreAdapter(db_repo)
    
    # 初始化消息流水线（通过适配器解耦业务逻辑）
    pipeline = MessagePipeline(preprocessor, llm_parser, db_repo, business_adapter)
    
    # 初始化业务命令处理器（业务逻辑层）
    business_command_handler = BusinessCommandHandler(business_adapter, db_repo)
    
    # 初始化微信消息路由
    router = WeChatMessageRouter(pipeline, business_command_handler)
    
    # 初始化接口管理器
    interface_manager = InterfaceManager()
    
    # 初始化企业微信机器人
    bot = WeChatBot(router)
    interface_manager.register(bot)
    
    # 初始化 Web API 接口（可选，用于数据库管理）
    enable_web_api = os.getenv("ENABLE_WEB_API", "false").lower() == "true"
    if enable_web_api:
        try:
            from interface.web import WebAPI
            logger.info("Initializing Web API interface...")
            web_api = WebAPI(
                db_repo=db_repo,
                host=os.getenv("WEB_API_HOST", "0.0.0.0"),
                port=int(os.getenv("WEB_API_PORT", "8080"))
            )
            interface_manager.register(web_api)
            logger.info("Web API interface registered (will start with other interfaces)")
        except ImportError:
            logger.warning("Web API not available (missing dependencies)")
    
    # 启动所有已注册的接口
    logger.info("Starting all interfaces...")
    interface_manager.start_all()
    
    # 初始化定时任务（业务逻辑层）
    def send_summary_message(target: str, content: str):
        """定时任务的消息发送回调"""
        # 通过接口管理器获取 wechat 接口并发送消息
        wechat_interface = interface_manager.get_interface("wechat")
        if wechat_interface:
            wechat_interface.send_message(target, content)
        else:
            logger.warning("WeChat interface not available for sending summary message")
    
    # 创建定时任务业务逻辑实例
    scheduler_tasks = SchedulerTasks(
        business_adapter=business_adapter,
        db_repo=db_repo,
        message_sender=send_summary_message if bot.running else None
    )
    
    # 初始化调度器（通用框架）
    scheduler = Scheduler()
    
    # 添加每日汇总任务
    try:
        hour, minute = map(int, settings.daily_summary_time.split(':'))
    except:
        hour, minute = 21, 0
    
    # 准备目标群组列表
    target_groups = None
    wechat_interface = interface_manager.get_interface("wechat")
    if wechat_interface and wechat_interface.is_running() and settings.wechat_group_ids:
        target_groups = [g.strip() for g in settings.wechat_group_ids.split(',')]
    
    # 创建任务函数
    async def daily_summary_job():
        await scheduler_tasks.daily_summary_task(target_groups)
    
    scheduler.add_daily_task(
        task_func=daily_summary_job,
        hour=hour,
        minute=minute,
        task_id='daily_summary',
        task_name='每日汇总'
    )
    
    scheduler.start()
    
    logger.info("All interfaces are running! Press Ctrl+C to stop.")
    logger.info(f"Active interfaces: {', '.join(interface_manager.get_running_interfaces())}")
    
    # 保持运行
    try:
        import time
        # 检查是否有接口在运行
        while any(interface.is_running() for interface in interface_manager.interfaces.values()):
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()
        interface_manager.stop_all()
        logger.info("All interfaces stopped.")


if __name__ == "__main__":
    main()

