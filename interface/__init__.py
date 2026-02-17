"""用户接口模块 - 完整版

提供企业微信接口，使用企业微信 API 实现完整功能。

架构设计：
- base.py: 定义统一的接口抽象基类 Interface
- manager.py: 接口管理器，统一管理多个接口
- wechat/: 企业微信接口实现（完整的机器人功能）
  - bot.py: 机器人主类
  - wecom_client.py: 企业微信 API 客户端
  - callback_server.py: 消息回调服务器
  - manager.py: 群聊和用户管理器
  - message_router.py: 消息路由器
- web/: Web接口（可选，提供 RESTful API 用于数据库管理）

功能特性：
- 消息收发（文本、图片、文件、Markdown）
- 群聊管理（创建、修改、查询）
- 用户管理（查询用户信息、部门成员）
- 消息回调（接收和处理企业微信消息）
- 批量操作和缓存管理

注意：所有业务相关的命令定义和处理逻辑都在 business/ 中
"""
from interface.base import Interface
from interface.manager import InterfaceManager

# 导入企业微信接口
from interface.wechat.bot import WeChatBot
from interface.wechat.wecom_client import WeChatWorkClient
from interface.wechat.callback_server import WeChatCallbackServer
from interface.wechat.manager import WeChatGroupManager, WeChatUserManager
from interface.wechat.message_router import WeChatMessageRouter

# Web接口（可选）
try:
    from interface.web.api import WebAPI
    _has_web = True
except ImportError:
    _has_web = False
    WebAPI = None

__all__ = [
    'Interface',
    'InterfaceManager',
    # 企业微信接口
    'WeChatBot',
    'WeChatWorkClient',
    'WeChatCallbackServer',
    'WeChatGroupManager',
    'WeChatUserManager',
    'WeChatMessageRouter',
]

# 如果有 Web 接口，添加到导出列表
if _has_web:
    __all__.append('WebAPI')
