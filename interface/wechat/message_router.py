"""微信消息路由 - 区分 @机器人 指令和被动监听"""
import re
from typing import Any, Dict, Tuple

from business.command_handler import BusinessCommandHandler
from business.commands import COMMANDS
from parsing.pipeline import MessagePipeline


class WeChatMessageRouter:
    """微信消息路由器 - 区分 @机器人 指令和被动监听"""
    
    def __init__(self, pipeline: MessagePipeline, command_handler: BusinessCommandHandler):
        """
        Args:
            pipeline: 消息处理流水线，用于解析业务消息
            command_handler: 业务命令处理器，用于处理 @机器人 命令
        """
        self.pipeline = pipeline
        self.command_handler = command_handler
    
    async def route(self, raw_msg: Dict[str, Any]) -> Tuple[str, bool]:
        """
        路由消息
        
        Args:
            raw_msg: 原始消息字典
            
        Returns:
            (response_text, should_send): 回复内容和是否需要发送
        """
        if raw_msg.get('is_at_bot', False):
            # @机器人 -> 处理命令
            response = await self._handle_command(raw_msg)
            return (response, True)
        else:
            # 被动监听 -> 解析业务消息
            result = await self.pipeline.process(raw_msg)
            # 被动监听通常不回复，除非有错误需要提示
            if result.status == 'failed':
                return (f"❌ 解析失败: {result.error}", False)
            return ("", False)
    
    async def _handle_command(self, raw_msg: Dict[str, Any]) -> str:
        """解析 @机器人 后面的命令"""
        content = raw_msg['content']
        # 去掉 @机器人 部分
        content = re.sub(r'@\S+\s*', '', content).strip()
        
        # 查找匹配的命令（从业务层获取命令定义）
        for keyword, cmd_config in COMMANDS.items():
            if content.startswith(keyword):
                args = content[len(keyword):].strip().split()
                context = {
                    'group_id': raw_msg.get('group_id', ''),
                    'sender_id': raw_msg.get('sender_wechat_id', ''),
                    'sender_name': raw_msg.get('sender_nickname', ''),
                }
                return await self.command_handler.handle_command(keyword, args, context)
        
        return "❓ 未识别的命令，回复 @机器人 帮助 查看可用指令"

