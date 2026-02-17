"""企业微信机器人 - 完整版

使用企业微信 API 实现完整的机器人功能：
- 查询群聊列表和群聊信息
- 获取群聊和成员信息
- 发送各种类型的消息（文本、图片、文件、Markdown等）
- 接收和处理消息回调
- 群聊管理（创建、修改群聊）
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from config.settings import settings
from interface.base import Interface
from interface.wechat.callback_server import WeChatCallbackServer
from interface.wechat.message_router import WeChatMessageRouter
from interface.wechat.wecom_client import WeChatWorkClient


class WeChatBot(Interface):
    """企业微信机器人
    
    使用企业微信 API 实现消息收发和群聊管理
    """
    
    def __init__(self, router: WeChatMessageRouter, enable_callback: bool = True):
        """
        Args:
            router: 消息路由器，用于处理接收到的消息
            enable_callback: 是否启用回调服务器
        """
        super().__init__("wechat")
        self.router = router
        self.client: Optional[WeChatWorkClient] = None
        self.callback_server: Optional[WeChatCallbackServer] = None
        self.enable_callback = enable_callback
        self.bot_wxid: Optional[str] = None
        self.target_group_ids: Set[str] = set()
        self._callback_task: Optional[asyncio.Task] = None
        
        # 初始化目标群ID（如果配置了）
        if settings.wechat_group_ids:
            self.target_group_ids = set(settings.wechat_group_ids.split(','))
            logger.info(f"Target groups configured: {self.target_group_ids}")
    
    def start(self):
        """启动机器人"""
        try:
            # 初始化企业微信客户端
            self.client = WeChatWorkClient(
                corp_id=settings.wechat_work_corp_id,
                secret=settings.wechat_work_secret,
                agent_id=settings.wechat_work_agent_id
            )
            
            # 获取机器人ID
            self.bot_wxid = self.client.get_bot_id()
            
            # 启动回调服务器（如果启用）
            if self.enable_callback and settings.wechat_work_token and settings.wechat_work_encoding_aes_key:
                self.callback_server = WeChatCallbackServer(
                    token=settings.wechat_work_token,
                    encoding_aes_key=settings.wechat_work_encoding_aes_key,
                    corp_id=settings.wechat_work_corp_id,
                    host=settings.wechat_http_host,
                    port=settings.wechat_http_port
                )
                
                # 设置消息处理器
                self.callback_server.set_message_handler(self._handle_callback_message)
                self.callback_server.set_event_handler(self._handle_callback_event)
                
                # 在后台启动回调服务器
                logger.info("Starting callback server in background...")
                # Note: 实际应该在单独的线程或进程中启动
                logger.info(f"Callback URL: http://{settings.wechat_http_host}:{settings.wechat_http_port}/callback")
            else:
                logger.warning("Callback server not enabled or missing configuration")
            
            self.running = True
            logger.info(f"WeChat bot started successfully, bot_id: {self.bot_wxid}")
            
        except Exception as e:
            logger.error(f"Failed to start WeChat bot: {e}")
            raise
    
    async def _handle_callback_message(self, msg_dict: Dict[str, Any]) -> Optional[str]:
        """处理回调消息
        
        Args:
            msg_dict: 解析后的消息字典（来自企业微信）
            
        Returns:
            回复消息的 XML 字符串，如果不需要回复则返回 None
        """
        try:
            # 转换为标准消息格式
            raw_msg = self._convert_wecom_message(msg_dict)
            
            # 使用原有的消息处理逻辑
            response = await self.handle_message(raw_msg)
            
            # 如果需要回复，构建回复 XML
            if response:
                return self._build_text_reply_xml(msg_dict, response)
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling callback message: {e}")
            return None
    
    async def _handle_callback_event(self, event_dict: Dict[str, Any]) -> Optional[str]:
        """处理回调事件
        
        Args:
            event_dict: 解析后的事件字典
            
        Returns:
            回复消息的 XML 字符串，如果不需要回复则返回 None
        """
        event_type = event_dict.get('Event', '')
        logger.info(f"Received event: {event_type}")
        
        # 可以在这里处理各种事件，如：
        # - subscribe: 关注应用
        # - unsubscribe: 取消关注
        # - enter_agent: 进入应用
        # - click: 点击菜单
        # 等等
        
        return None
    
    def _convert_wecom_message(self, msg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """将企业微信消息格式转换为标准消息格式
        
        Args:
            msg_dict: 企业微信消息字典
            
        Returns:
            标准消息格式字典
        """
        return {
            'wechat_msg_id': msg_dict.get('MsgId', ''),
            'sender_wechat_id': msg_dict.get('FromUserName', ''),
            'sender_nickname': msg_dict.get('FromUserName', ''),  # 需要额外查询获取昵称
            'content': msg_dict.get('Content', ''),
            'msg_type': msg_dict.get('MsgType', 'text').lower(),
            'group_id': msg_dict.get('ChatId', ''),  # 群聊消息会有这个字段
            'timestamp': datetime.fromtimestamp(int(msg_dict.get('CreateTime', 0))),
            'is_at_bot': '@' in msg_dict.get('Content', ''),  # 简单判断，实际需要更复杂的逻辑
        }
    
    def _build_text_reply_xml(self, original_msg: Dict[str, Any], content: str) -> str:
        """构建文本回复消息的 XML
        
        Args:
            original_msg: 原始消息字典
            content: 回复内容
            
        Returns:
            XML 字符串
        """
        from_user = original_msg.get('ToUserName', '')
        to_user = original_msg.get('FromUserName', '')
        create_time = int(datetime.now().timestamp())
        
        xml_str = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
        return xml_str
    
    def get_all_groups(self) -> list:
        """获取所有群聊列表
        
        Returns:
            群聊列表，每个元素包含 chatid 和 name
        """
        if not self.client:
            logger.error("Client not initialized")
            return []
        
        try:
            return self.client.get_all_app_chats()
        except Exception as e:
            logger.error(f"Failed to get groups: {e}")
            return []
    
    def get_group_info(self, chat_id: str) -> Dict[str, Any]:
        """获取群聊详细信息
        
        Args:
            chat_id: 群聊 ID
            
        Returns:
            群聊信息字典，包含 name, owner, userlist 等
        """
        if not self.client:
            logger.error("Client not initialized")
            return {}
        
        try:
            return self.client.get_chat_info(chat_id)
        except Exception as e:
            logger.error(f"Failed to get group info: {e}")
            return {}
    
    def get_group_members(self, chat_id: str) -> list:
        """获取群聊成员列表
        
        Args:
            chat_id: 群聊 ID
            
        Returns:
            成员 userid 列表
        """
        if not self.client:
            logger.error("Client not initialized")
            return []
        
        try:
            return self.client.get_chat_members(chat_id)
        except Exception as e:
            logger.error(f"Failed to get group members: {e}")
            return []
    
    async def handle_message(self, raw_msg: Dict[str, Any]) -> Optional[str]:
        """处理接收到的消息
        
        Args:
            raw_msg: 消息字典，格式：
                {
                    'wechat_msg_id': str,
                    'sender_nickname': str,
                    'sender_wechat_id': str,
                    'content': str,
                    'msg_type': str,
                    'group_id': str,
                    'timestamp': datetime,
                    'is_at_bot': bool
                }
        
        Returns:
            如果需要回复，返回回复内容；否则返回 None
        """
        try:
            # 检查是否为目标群（如果配置了目标群）
            group_id = raw_msg.get('group_id', '')
            if self.target_group_ids and group_id not in self.target_group_ids:
                logger.debug(f"Message from non-target group: {group_id}")
                return None
            
            # 使用路由器处理消息
            response, should_send = await self.router.route(raw_msg)
            
            if should_send and response:
                return response
            return None
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return f"❌ 处理消息时出错: {str(e)}"
    
    def send_message(self, target: str, content: str):
        """发送消息到群聊
        
        Args:
            target: 目标群ID (chatid)
            content: 消息内容
        """
        if not self.client:
            logger.error("Client not initialized")
            return
        
        try:
            self.client.send_group_message(target, content)
            logger.info(f"Message sent to group {target}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    def send_user_message(self, user_id: str, content: str):
        """发送消息给用户
        
        Args:
            user_id: 用户 ID
            content: 消息内容
        """
        if not self.client:
            logger.error("Client not initialized")
            return
        
        try:
            self.client.send_text_message(user_id, content)
            logger.info(f"Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send user message: {e}")
            raise
    
    def send_markdown_message(self, chat_id: str, content: str):
        """发送 Markdown 消息到群聊
        
        Args:
            chat_id: 群聊 ID
            content: Markdown 内容
        """
        if not self.client:
            logger.error("Client not initialized")
            return
        
        try:
            self.client.send_markdown_message(chat_id, content)
            logger.info(f"Markdown message sent to group {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send markdown message: {e}")
            raise
    
    def send_image(self, chat_id: str, image_path: str):
        """发送图片到群聊
        
        Args:
            chat_id: 群聊 ID
            image_path: 图片文件路径
        """
        if not self.client:
            logger.error("Client not initialized")
            return
        
        try:
            # 上传图片获取 media_id
            media_id = self.client.upload_temp_media(image_path, "image")
            # 发送图片消息
            self.client.send_image_message(chat_id, media_id)
            logger.info(f"Image sent to group {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send image: {e}")
            raise
    
    def send_file(self, chat_id: str, file_path: str):
        """发送文件到群聊
        
        Args:
            chat_id: 群聊 ID
            file_path: 文件路径
        """
        if not self.client:
            logger.error("Client not initialized")
            return
        
        try:
            # 上传文件获取 media_id
            media_id = self.client.upload_temp_media(file_path, "file")
            # 发送文件消息
            self.client.send_file_message(chat_id, media_id)
            logger.info(f"File sent to group {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send file: {e}")
            raise
    
    def create_group(self, name: str, owner: str, members: List[str], 
                    chat_id: Optional[str] = None) -> str:
        """创建群聊
        
        Args:
            name: 群聊名称
            owner: 群主 userid
            members: 群成员 userid 列表
            chat_id: 指定的群聊 ID（可选）
            
        Returns:
            创建的群聊 ID
        """
        if not self.client:
            logger.error("Client not initialized")
            raise RuntimeError("Client not initialized")
        
        try:
            created_chat_id = self.client.create_app_chat(name, owner, members, chat_id)
            logger.info(f"Group created: {created_chat_id}")
            return created_chat_id
        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            raise
    
    def update_group(self, chat_id: str, name: Optional[str] = None,
                    owner: Optional[str] = None, add_members: Optional[List[str]] = None,
                    remove_members: Optional[List[str]] = None) -> bool:
        """修改群聊信息
        
        Args:
            chat_id: 群聊 ID
            name: 新的群聊名称（可选）
            owner: 新的群主 userid（可选）
            add_members: 要添加的成员列表（可选）
            remove_members: 要删除的成员列表（可选）
            
        Returns:
            是否修改成功
        """
        if not self.client:
            logger.error("Client not initialized")
            return False
        
        try:
            success = self.client.update_app_chat(
                chat_id, name, owner, add_members, remove_members
            )
            if success:
                logger.info(f"Group {chat_id} updated")
            return success
        except Exception as e:
            logger.error(f"Failed to update group: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户信息字典
        """
        if not self.client:
            logger.error("Client not initialized")
            return {}
        
        try:
            return self.client.get_user_info(user_id)
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {}
    
    def get_department_users(self, department_id: int, fetch_child: bool = False) -> List[Dict[str, Any]]:
        """获取部门成员列表
        
        Args:
            department_id: 部门 ID
            fetch_child: 是否递归获取子部门成员
            
        Returns:
            部门成员列表
        """
        if not self.client:
            logger.error("Client not initialized")
            return []
        
        try:
            return self.client.get_department_users(department_id, fetch_child)
        except Exception as e:
            logger.error(f"Failed to get department users: {e}")
            return []
    
    def stop(self):
        """停止机器人"""
        self.running = False
        if self.client:
            self.client.close()
        logger.info("WeChat bot stopped")
