"""微信机器人主类"""
import asyncio
import threading
from datetime import datetime
from typing import Set, Optional
from loguru import logger
from core.message_router import MessageRouter
from config.settings import settings

# 注意：WeChatFerry 需要 Windows 环境，这里提供一个抽象接口
# 实际使用时需要安装 wcferry 包


class WeChatBot:
    """微信机器人"""
    
    def __init__(self, router: MessageRouter):
        self.router = router
        self.bot_wxid: Optional[str] = None
        self.target_group_ids: Set[str] = set()
        self.wcf = None  # WeChatFerry 实例
        self.running = False
        
        # 初始化目标群ID
        if settings.wechat_group_ids:
            self.target_group_ids = set(settings.wechat_group_ids.split(','))
    
    def start(self):
        """启动机器人"""
        try:
            # 尝试导入 WeChatFerry
            try:
                from wcferry import Wcf, WxMsg
                self.Wcf = Wcf
                self.WxMsg = WxMsg
            except ImportError:
                logger.warning("WeChatFerry not installed, using mock mode")
                self._start_mock_mode()
                return
            
            # 初始化 WeChatFerry
            self.wcf = self.Wcf()
            self.bot_wxid = self.wcf.get_self_wxid()
            logger.info(f"Bot started, wxid: {self.bot_wxid}")
            
            # 注册消息回调
            self.wcf.enable_receiving_msg()
            self.running = True
            
            # 启动消息循环
            threading.Thread(target=self._message_loop, daemon=True).start()
            logger.info("Message loop started")
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            logger.info("Falling back to mock mode")
            self._start_mock_mode()
    
    def _start_mock_mode(self):
        """启动模拟模式（用于测试）"""
        logger.info("Running in mock mode - no actual WeChat connection")
        self.running = True
        # 在模拟模式下，可以通过其他方式接收消息（如HTTP API）
    
    def _message_loop(self):
        """消息循环（在单独线程中运行）"""
        # 在新线程中创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running and self.wcf and self.wcf.is_receiving_msg():
            try:
                msg = self.wcf.get_msg()
                if msg and msg.from_group():
                    # 检查是否为目标群
                    if not self.target_group_ids or msg.roomid in self.target_group_ids:
                        # 在事件循环中处理消息
                        loop.run_until_complete(self._handle_group_message(msg))
            except Exception as e:
                logger.error(f"Message loop error: {e}")
                import time
                time.sleep(1)
    
    async def _handle_group_message(self, msg):
        """处理群消息"""
        try:
            # 构造统一消息格式
            raw_msg = {
                'wechat_msg_id': str(msg.id),
                'sender_nickname': self.wcf.get_alias_in_chatroom(msg.roomid, msg.sender) or msg.sender,
                'sender_wechat_id': msg.sender,
                'content': msg.content,
                'msg_type': 'text' if msg.type == 1 else 'other',
                'group_id': msg.roomid,
                'timestamp': datetime.fromtimestamp(msg.ts),
                'is_at_bot': self.bot_wxid in msg.content or f'@{settings.bot_name}' in msg.content,
            }
            
            # 路由消息
            response, should_send = await self.router.route(raw_msg)
            
            # 如果需要回复
            if should_send and response:
                self.wcf.send_text(response, msg.roomid)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def send_message(self, group_id: str, content: str):
        """发送消息到群"""
        if self.wcf:
            self.wcf.send_text(content, group_id)
        else:
            logger.warning(f"Mock mode: would send to {group_id}: {content}")
    
    def stop(self):
        """停止机器人"""
        self.running = False
        if self.wcf:
            self.wcf.disable_receiving_msg()
        logger.info("Bot stopped")


class MockWeChatBot:
    """模拟微信机器人（用于测试或非Windows环境）"""
    
    def __init__(self, router: MessageRouter):
        self.router = router
        self.running = False
    
    def start(self):
        """启动模拟机器人"""
        logger.info("Mock bot started - waiting for messages via API")
        self.running = True
    
    async def handle_message(self, raw_msg: dict) -> Optional[str]:
        """处理消息（通过API调用）"""
        response, should_send = await self.router.route(raw_msg)
        return response if should_send else None
    
    def stop(self):
        """停止机器人"""
        self.running = False

