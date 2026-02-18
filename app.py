#!/usr/bin/env python3
"""BizBot - AI-powered business management platform

Launch the web management platform with:
1. AI chat assistant (LLM agent with full database CRUD via natural language)
2. Database visualization dashboard

Usage:
    python app.py
    python app.py --port 8080
    python app.py --db sqlite:///data/store.db

Environment variables (configure in .env, run `python scripts/setup_env.py` to generate):
    MINIMAX_API_KEY   MiniMax API Key (required)
    MINIMAX_MODEL     MiniMax model name (default: MiniMax-M2.5)
    DATABASE_URL      Database connection URL
    WEB_PORT          Web port (default: 8080)
    WEB_USERNAME      Login username (default: admin)
    WEB_PASSWORD      Login password (default: admin123)
    WEB_SECRET_KEY    JWT secret key
"""
import argparse
import asyncio
import os
import signal
import sys

from loguru import logger


def init_default_data(db):
    """初始化默认业务数据（理疗馆基础数据）。

    根据 business_config 中的配置，自动创建默认的员工、服务类型、产品和渠道。
    使用 get_or_create 确保幂等性（重复运行不会创建重复数据）。
    """
    from config.business_config import business_config

    with db.get_session() as session:
        # 创建默认员工
        for staff in business_config.get_default_staff():
            emp = db.staff.get_or_create(staff["name"], session=session)
            emp.role = staff.get("role", "staff")
            emp.commission_rate = staff.get("commission_rate", 0)

        # 创建服务类型
        for st in business_config.get_service_types():
            db.service_types.get_or_create(
                st["name"], st.get("default_price"), st.get("category"),
                session=session,
            )

        # 创建产品
        for prod in business_config.get_products():
            db.products.get_or_create(
                prod["name"], prod.get("category"), prod.get("unit_price"),
                session=session,
            )

        # 创建引流渠道
        for ch in business_config.get_channels():
            db.channels.get_or_create(
                ch["name"], ch.get("type", "external"), None,
                ch.get("commission_rate"),
                session=session,
            )

        session.commit()

    logger.info("默认业务数据初始化完成")


async def create_agent(db):
    """创建智能管理 Agent 实例。

    Agent 注册了完整的数据库操作函数集，可以根据用户自然语言指令
    灵活调用增删改查操作。

    Args:
        db: DatabaseManager 实例，用于设置业务函数的数据库引用。

    Returns:
        配置好的 Agent 实例，或 None（如果 API Key 未配置）。
    """
    from config.settings import settings
    from agent import Agent, create_provider, FunctionRegistry
    from config.prompts import get_system_prompt
    from config.register_functions import register_all_functions
    from config import business_functions

    # 设置业务函数的数据库引用
    business_functions.set_db(db)

    # 检查 API Key
    if not settings.minimax_api_key:
        logger.warning("未配置 MINIMAX_API_KEY，Agent 将不可用")
        return None

    try:
        provider = create_provider(
            "minimax",
            api_key=settings.minimax_api_key,
            model=settings.minimax_model,
            base_url=settings.minimax_base_url,
        )
        logger.info(f"LLM Provider 创建成功: minimax ({settings.minimax_model})")
    except Exception as e:
        logger.warning(f"创建 LLM Provider 失败: {e}，将使用无 Agent 模式")
        return None

    # 创建函数注册表并注册所有业务函数
    registry = FunctionRegistry()
    register_all_functions(registry)

    func_count = len(registry.list_functions())
    logger.info(f"已注册 {func_count} 个业务函数到 Agent")

    # 获取系统提示词（由 business_config 动态生成）
    system_prompt = get_system_prompt()

    # 创建 Agent
    agent = Agent(provider, registry, system_prompt=system_prompt)
    return agent


async def _cleanup(web, db):
    """统一资源清理函数。

    确保 Web 服务器和数据库连接被正确关闭，释放端口和文件句柄。
    """
    logger.info("正在清理资源...")

    # 1. 停止 Web 服务器（释放端口）
    if web is not None:
        try:
            await web.shutdown()
        except Exception as e:
            logger.warning(f"停止 Web 服务器时出错: {e}")

    # 2. 关闭数据库连接（释放连接池）
    if db is not None:
        try:
            db.close()
        except Exception as e:
            logger.warning(f"关闭数据库连接时出错: {e}")

    logger.info("服务已停止")


async def main():
    parser = argparse.ArgumentParser(description="BizBot - AI-powered business management platform")
    parser.add_argument("--host", default=os.getenv("WEB_HOST", "0.0.0.0"),
                        help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.getenv("WEB_PORT", "8080")),
                        help="监听端口 (默认: 8080)")
    parser.add_argument("--db", default=os.getenv("DATABASE_URL", None),
                        help="数据库连接 URL")
    parser.add_argument("--username", default=os.getenv("WEB_USERNAME", "admin"),
                        help="登录用户名 (默认: admin)")
    parser.add_argument("--password", default=os.getenv("WEB_PASSWORD", "admin123"),
                        help="登录密码 (默认: admin123)")
    parser.add_argument("--no-agent", action="store_true",
                        help="不启动 Agent（仅数据库可视化）")
    parser.add_argument("--skip-init-data", action="store_true",
                        help="跳过默认业务数据初始化")
    args = parser.parse_args()

    # 用于 finally 清理的引用
    web = None
    db = None

    try:
        # 初始化数据库
        from database import DatabaseManager
        db = DatabaseManager(args.db)
        db.create_tables()
        logger.info(f"数据库已连接: {db.database_url}")

        # 初始化默认业务数据
        if not args.skip_init_data:
            try:
                init_default_data(db)
            except Exception as e:
                logger.warning(f"初始化默认数据时出错（不影响运行）: {e}")

        # 创建 Agent
        agent = None
        if not args.no_agent:
            try:
                agent = await create_agent(db)
                if agent:
                    logger.info("智能管理 Agent 已就绪")
            except Exception as e:
                logger.warning(f"Agent 初始化失败: {e}")

        # 消息处理回调
        from interface.base import Message, MessageType, Reply
        from config.business_config import business_config

        async def message_handler(message: Message):
            """处理用户消息

            Agent 会根据用户的自然语言指令，自动选择合适的工具函数执行。
            对于写操作，Agent 会在系统提示词中被指导先向用户确认。
            """
            if agent:
                try:
                    response = await agent.chat(message.content)
                    content = response.get("content", "抱歉，我无法处理你的请求。")

                    # 记录工具调用情况
                    if response.get("function_calls"):
                        tool_names = [fc['name'] for fc in response['function_calls']]
                        logger.info(f"Agent 调用了工具: {', '.join(tool_names)}")

                    return Reply(
                        type=MessageType.TEXT,
                        content=content,
                    )
                except Exception as e:
                    logger.error(f"Agent 处理出错: {e}")
                    return Reply(
                        type=MessageType.TEXT,
                        content=f"处理出错: {str(e)}",
                    )
            else:
                store_name = business_config.get_business_name()
                return Reply(
                    type=MessageType.TEXT,
                    content=(
                        f"Agent 未配置。请在 .env 中设置 MINIMAX_API_KEY 后重启。\n\n"
                        f"运行 python scripts/setup_env.py 可快速生成配置。\n\n"
                        f"当前仅支持数据库可视化功能，请在左侧导航栏查看数据。\n\n"
                        f"业态：{store_name}"
                    ),
                )

        # 创建 Web 通道
        from interface.web.channel import WebChannel
        from config.settings import settings

        web = WebChannel(
            message_handler=message_handler,
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            secret_key=settings.web_secret_key,
            db_manager=db,
        )

        # 启动
        await web.startup()

        store_name = business_config.get_business_name()
        func_count = len(agent.function_registry.list_functions()) if agent else 0

        print()
        print("=" * 60)
        print(f"  🤖 BizBot — {store_name} is running!")
        print(f"  URL:       http://localhost:{args.port}")
        print(f"  External:  http://YOUR_IP:{args.port}")
        print(f"  Username:  {args.username}")
        print(f"  Password:  {args.password}")
        print(f"  Database:  {db.database_url}")
        print(f"  Agent:     {'✅ enabled' if agent else '❌ disabled (set MINIMAX_API_KEY)'}")
        if agent:
            print(f"  Functions: {func_count} registered")
        print(f"  Config:    config/business_config.py")
        print("=" * 60)
        print("  Press Ctrl+C to stop")
        print()

        # 设置信号处理 —— 使用 asyncio 的信号处理确保事件循环能正确响应
        loop = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()
        _shutdown_requested = False

        def signal_handler(signum):
            """处理退出信号"""
            nonlocal _shutdown_requested
            if _shutdown_requested:
                # 第二次收到信号，强制退出
                logger.warning("再次收到退出信号，强制退出...")
                # 取消所有待处理的任务以快速退出
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                return
            _shutdown_requested = True
            logger.info(f"收到信号 {signum}，正在关闭服务...")
            shutdown_event.set()

        # 使用 loop.add_signal_handler（asyncio 原生方式，确保事件循环能正确唤醒）
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler, sig)

        # 保持运行，直到收到退出信号
        await shutdown_event.wait()

    except asyncio.CancelledError:
        logger.info("任务被取消，正在清理...")
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    finally:
        await _cleanup(web, db)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        print("\n已停止。")
