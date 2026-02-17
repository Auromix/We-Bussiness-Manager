"""企业微信接口模块 - 完整版

使用企业微信 API 实现完整的机器人功能：
- 群聊管理（创建、修改、查询、批量操作）
- 消息收发（文本、图片、文件、Markdown）
- 成员管理（查询用户信息、部门成员）
- 消息回调（接收和处理企业微信消息）
- 高级管理功能（缓存、搜索、统计）

核心组件：
- WeChatBot: 机器人主类（Interface 实现）
- WeChatWorkClient: 企业微信 API 客户端
- WeChatCallbackServer: 消息回调服务器
- WeChatGroupManager: 群聊管理器
- WeChatUserManager: 用户管理器
- WeChatMessageRouter: 消息路由器
"""
from interface.wechat.bot import WeChatBot
from interface.wechat.callback_server import WeChatCallbackServer
from interface.wechat.manager import WeChatGroupManager, WeChatUserManager
from interface.wechat.message_router import WeChatMessageRouter
from interface.wechat.wecom_client import WeChatWorkClient

__all__ = [
    'WeChatBot',
    'WeChatWorkClient',
    'WeChatCallbackServer',
    'WeChatGroupManager',
    'WeChatUserManager',
    'WeChatMessageRouter',
]
