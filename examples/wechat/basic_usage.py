"""企业微信机器人基础使用示例

演示如何使用企业微信机器人的基本功能
"""
import asyncio
from loguru import logger

from config.settings import settings
from interface.wechat.bot import WeChatBot
from interface.wechat.message_router import WeChatMessageRouter
from business.command_handler import BusinessCommandHandler
from parsing.pipeline import MessagePipeline
from database import DatabaseManager


async def main():
    """主函数"""
    
    # 1. 初始化依赖
    logger.info("初始化组件...")
    
    # 初始化数据库
    repo = DatabaseManager(settings.database_url)
    
    # 初始化消息处理流水线
    pipeline = MessagePipeline(repo)
    
    # 初始化命令处理器
    command_handler = BusinessCommandHandler(repo)
    
    # 初始化消息路由器
    router = WeChatMessageRouter(pipeline, command_handler)
    
    # 2. 创建并启动机器人
    logger.info("创建机器人...")
    bot = WeChatBot(router, enable_callback=True)
    
    try:
        logger.info("启动机器人...")
        bot.start()
        
        # 3. 测试基本功能
        logger.info("测试基本功能...")
        
        # 获取所有群聊
        groups = bot.get_all_groups()
        logger.info(f"找到 {len(groups)} 个群聊")
        for group in groups[:5]:
            logger.info(f"  - {group.get('name')} ({group.get('chatid')})")
        
        # 如果有群聊，获取第一个群的详细信息
        if groups:
            first_group = groups[0]
            chat_id = first_group['chatid']
            
            # 获取群聊详细信息
            info = bot.get_group_info(chat_id)
            logger.info(f"群聊信息: {info.get('name')}")
            logger.info(f"群主: {info.get('owner')}")
            logger.info(f"成员数: {len(info.get('userlist', []))}")
            
            # 获取群成员
            members = bot.get_group_members(chat_id)
            logger.info(f"群成员: {members}")
            
            # 发送测试消息
            # bot.send_message(chat_id, "🤖 机器人已启动！")
            # logger.info("测试消息已发送")
        
        # 4. 保持运行
        logger.info("机器人运行中，按 Ctrl+C 停止...")
        
        # 在实际使用中，这里应该保持服务运行
        # 如果启用了回调服务器，需要等待回调处理
        # await asyncio.Event().wait()  # 永久等待
        
        # 这里为了演示，我们只等待 5 秒
        await asyncio.sleep(5)
        
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"错误: {e}")
    finally:
        # 5. 停止机器人
        logger.info("停止机器人...")
        bot.stop()
        logger.info("机器人已停止")


if __name__ == "__main__":
    asyncio.run(main())

