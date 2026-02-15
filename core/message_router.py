"""消息路由"""
import re
from typing import Dict, Any
from parsing.pipeline import MessagePipeline
from core.command_handler import CommandHandler, COMMANDS


class MessageRouter:
    """消息路由器 - 区分 @机器人 指令和被动监听"""
    
    def __init__(self, pipeline: MessagePipeline, command_handler: CommandHandler, bot_name: str):
        self.pipeline = pipeline
        self.command_handler = command_handler
        self.bot_name = bot_name
    
    async def route(self, raw_msg: Dict[str, Any]) -> tuple[str, bool]:
        """
        路由消息
        返回: (response_text, should_send)
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
        
        # 查找匹配的命令
        for keyword, cmd_config in COMMANDS.items():
            if content.startswith(keyword):
                args = content[len(keyword):].strip().split()
                handler = getattr(self.command_handler, cmd_config['handler'])
                return await handler(raw_msg.get('group_id', ''), args)
        
        return "❓ 未识别的命令，回复 @机器人 帮助 查看可用指令"

