"""企业微信机器人高级功能示例

演示如何使用企业微信机器人的高级功能：
- 群聊管理
- 用户管理
- 批量操作
- 多种消息类型
"""
import asyncio
from loguru import logger

from config.settings import settings
from interface.wechat.wecom_client import WeChatWorkClient
from interface.wechat.manager import WeChatGroupManager, WeChatUserManager


def example_group_management():
    """群聊管理示例"""
    logger.info("=== 群聊管理示例 ===")
    
    # 创建客户端
    client = WeChatWorkClient(
        corp_id=settings.wechat_work_corp_id,
        secret=settings.wechat_work_secret,
        agent_id=settings.wechat_work_agent_id
    )
    
    # 创建群聊管理器
    group_mgr = WeChatGroupManager(client)
    
    # 1. 获取所有群聊
    groups = group_mgr.get_all_groups()
    logger.info(f"总共 {len(groups)} 个群聊")
    
    # 2. 搜索群聊
    keyword = "测试"
    matched_groups = group_mgr.search_groups(keyword)
    logger.info(f"找到 {len(matched_groups)} 个包含 '{keyword}' 的群聊")
    for group in matched_groups:
        logger.info(f"  - {group['name']} ({group['chatid']})")
    
    # 3. 获取群聊统计信息
    stats = group_mgr.get_group_statistics()
    logger.info(f"群聊统计: {stats}")
    
    # 4. 创建新群聊（需要实际的用户 ID）
    # new_chat_id = group_mgr.create_group(
    #     name="示例群聊",
    #     owner="your_userid",
    #     members=["user1", "user2", "user3"]
    # )
    # if new_chat_id:
    #     logger.info(f"创建成功: {new_chat_id}")
    
    # 5. 修改群聊
    # success = group_mgr.update_group(
    #     chat_id="chatid",
    #     name="新名称",
    #     add_members=["user4"]
    # )
    # logger.info(f"修改{'成功' if success else '失败'}")
    
    # 6. 批量发送消息
    # target_chats = ["chat1", "chat2", "chat3"]
    # results = group_mgr.batch_send_message(
    #     chat_ids=target_chats,
    #     content="📢 批量通知消息"
    # )
    # success_count = sum(1 for v in results.values() if v)
    # logger.info(f"批量发送: {success_count}/{len(target_chats)} 成功")


def example_user_management():
    """用户管理示例"""
    logger.info("=== 用户管理示例 ===")
    
    # 创建客户端
    client = WeChatWorkClient(
        corp_id=settings.wechat_work_corp_id,
        secret=settings.wechat_work_secret,
        agent_id=settings.wechat_work_agent_id
    )
    
    # 创建用户管理器
    user_mgr = WeChatUserManager(client)
    
    # 1. 获取单个用户信息
    # user_info = user_mgr.get_user_info("userid")
    # logger.info(f"用户信息: {user_info}")
    
    # 2. 批量获取用户信息
    # user_ids = ["user1", "user2", "user3"]
    # users_info = user_mgr.get_users_info(user_ids)
    # logger.info(f"获取到 {len(users_info)} 个用户信息")
    # for uid, info in users_info.items():
    #     logger.info(f"  - {info.get('name')} ({uid})")
    
    # 3. 获取部门成员
    department_id = 1  # 根部门
    users = user_mgr.get_department_users(department_id, fetch_child=True)
    logger.info(f"部门 {department_id} 有 {len(users)} 个成员")
    for user in users[:5]:
        logger.info(f"  - {user.get('name')} ({user.get('userid')})")
    
    # 4. 搜索用户
    # name = "张"
    # matched_users = user_mgr.search_users_by_name(name, department_id=1)
    # logger.info(f"找到 {len(matched_users)} 个名字包含 '{name}' 的用户")


def example_message_types():
    """不同消息类型示例"""
    logger.info("=== 消息类型示例 ===")
    
    # 创建客户端
    client = WeChatWorkClient(
        corp_id=settings.wechat_work_corp_id,
        secret=settings.wechat_work_secret,
        agent_id=settings.wechat_work_agent_id
    )
    
    # 替换为实际的 chat_id
    chat_id = "your_chat_id"
    
    # 1. 发送文本消息
    # client.send_group_message(chat_id, "📝 这是一条文本消息")
    # logger.info("文本消息已发送")
    
    # 2. 发送 Markdown 消息
    markdown_content = """
# 📊 数据报告
## 今日统计
- 新增用户：**100** 人
- 活跃用户：**500** 人
- 营业额：**¥10,000**

> 数据更新时间：2026-02-16 10:00
    """
    # client.send_markdown_message(chat_id, markdown_content)
    # logger.info("Markdown 消息已发送")
    
    # 3. 发送图片
    # media_id = client.upload_temp_media("/path/to/image.jpg", "image")
    # client.send_image_message(chat_id, media_id)
    # logger.info("图片已发送")
    
    # 4. 发送文件
    # media_id = client.upload_temp_media("/path/to/file.pdf", "file")
    # client.send_file_message(chat_id, media_id)
    # logger.info("文件已发送")


def example_callback_server():
    """回调服务器示例"""
    logger.info("=== 回调服务器示例 ===")
    
    from interface.wechat.callback_server import WeChatCallbackServer
    
    # 创建回调服务器
    server = WeChatCallbackServer(
        token=settings.wechat_work_token,
        encoding_aes_key=settings.wechat_work_encoding_aes_key,
        corp_id=settings.wechat_work_corp_id,
        host=settings.wechat_http_host,
        port=settings.wechat_http_port
    )
    
    # 定义消息处理器
    async def handle_message(msg_dict):
        """处理接收到的消息"""
        msg_type = msg_dict.get('MsgType', '')
        from_user = msg_dict.get('FromUserName', '')
        content = msg_dict.get('Content', '')
        
        logger.info(f"收到消息: type={msg_type}, from={from_user}, content={content}")
        
        # 可以在这里处理消息并返回回复
        # 返回 None 表示不回复
        return None
    
    # 定义事件处理器
    async def handle_event(event_dict):
        """处理事件"""
        event_type = event_dict.get('Event', '')
        from_user = event_dict.get('FromUserName', '')
        
        logger.info(f"收到事件: type={event_type}, from={from_user}")
        
        # 返回 None 表示不回复
        return None
    
    # 设置处理器
    server.set_message_handler(handle_message)
    server.set_event_handler(handle_event)
    
    # 启动服务器
    logger.info(f"启动回调服务器: http://{settings.wechat_http_host}:{settings.wechat_http_port}/callback")
    logger.info("请在企业微信后台配置此 URL")
    
    # server.start()  # 这会阻塞运行
    logger.info("提示：在生产环境中使用 server.start() 启动服务器")


def main():
    """主函数"""
    try:
        # 运行示例
        example_group_management()
        print()
        
        example_user_management()
        print()
        
        example_message_types()
        print()
        
        example_callback_server()
        
    except Exception as e:
        logger.error(f"错误: {e}")


if __name__ == "__main__":
    main()

