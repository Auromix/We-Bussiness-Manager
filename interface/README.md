# Interface 模块 - 简化版说明

## 概述

Interface 模块已经简化，去掉了 web 和 HTTP server，只保留企业微信 API 的核心功能。

## 目录结构

```
interface/
├── __init__.py           # 模块初始化，导出核心类
├── base.py              # 接口基类定义
├── manager.py           # 接口管理器
├── wechat/              # 企业微信接口（核心）
│   ├── __init__.py
│   ├── bot.py           # 企业微信机器人
│   ├── wecom_client.py  # 企业微信API客户端
│   └── message_router.py # 消息路由器
└── web/                 # Web接口（可选，用于数据库管理）
    ├── __init__.py
    └── api.py
```

## 核心组件

### 1. WeChatWorkClient (wecom_client.py)

企业微信 API 客户端，提供底层 API 调用。

**核心功能：**
- ✅ 获取所有群聊列表（自动分页）
- ✅ 获取群聊详细信息
- ✅ 获取群聊成员列表
- ✅ 发送群消息
- ✅ 发送用户消息
- ✅ 自动管理 access_token

**示例：**
```python
from interface.wechat import WeChatWorkClient

client = WeChatWorkClient(
    corp_id="your_corp_id",
    secret="your_secret",
    agent_id="your_agent_id"
)

# 获取所有群聊
chats = client.get_all_app_chats()

# 获取群聊信息
chat_info = client.get_chat_info(chat_id)

# 发送消息
client.send_group_message(chat_id, "Hello!")
```

### 2. WeChatBot (bot.py)

企业微信机器人，提供高级功能和消息处理。

**核心功能：**
- ✅ 启动/停止机器人
- ✅ 获取群聊列表和信息
- ✅ 处理接收到的消息
- ✅ 发送消息到群聊或用户
- ✅ 消息路由和业务处理

**示例：**
```python
from interface.wechat import WeChatBot, WeChatMessageRouter

# 创建机器人
router = WeChatMessageRouter(pipeline, command_handler)
bot = WeChatBot(router)
bot.start()

# 获取群聊
groups = bot.get_all_groups()

# 处理消息
response = await bot.handle_message(message_dict)

# 发送消息
bot.send_message(chat_id, "Hello!")
```

### 3. WeChatMessageRouter (message_router.py)

消息路由器，区分 @机器人 指令和被动监听。

**功能：**
- ✅ 区分主动命令（@机器人）和被动监听
- ✅ 路由到对应的处理器
- ✅ 返回是否需要回复

## 简化内容

### 已删除：
- ❌ `http_server.py` - HTTP API 服务器
- ❌ HTTP 回调接口相关代码
- ❌ 多模式切换逻辑（work/http）

### 保留：
- ✅ 企业微信 API 客户端
- ✅ 机器人核心功能
- ✅ 消息路由器
- ✅ Web API（可选，用于数据库管理）

## 配置要求

在 `config/settings.py` 或环境变量中配置：

```bash
# 企业微信配置（必需）
export WECHAT_WORK_CORP_ID="your_corp_id"
export WECHAT_WORK_SECRET="your_app_secret"
export WECHAT_WORK_AGENT_ID="your_agent_id"

# 目标群ID（可选，多个用逗号分隔）
export WECHAT_GROUP_IDS="chatid1,chatid2"
```

## 使用示例

查看 `examples/wechat/` 目录：
- `basic_usage.py` - 基本使用示例
- `README.md` - 详细使用说明

运行示例：
```bash
python examples/wechat/basic_usage.py
```

## 消息接收

企业微信使用**回调模式**接收消息：

1. 在企业微信管理后台配置回调URL
2. 企业微信会主动推送消息到你的服务器
3. 服务器接收后调用 `bot.handle_message()` 处理

**注意：** 企业微信不支持轮询模式，必须配置回调URL。

## API 参考

### WeChatWorkClient

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_all_app_chats()` | 获取所有应用会话 | `List[Dict]` |
| `get_chat_info(chat_id)` | 获取群聊信息 | `Dict` |
| `get_chat_members(chat_id)` | 获取群成员列表 | `List[str]` |
| `send_group_message(chat_id, content)` | 发送群消息 | `None` |
| `send_text_message(user_id, content)` | 发送用户消息 | `None` |
| `close()` | 关闭客户端 | `None` |

### WeChatBot

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `start()` | 启动机器人 | `None` |
| `stop()` | 停止机器人 | `None` |
| `get_all_groups()` | 获取所有群聊 | `List[Dict]` |
| `get_group_info(chat_id)` | 获取群聊信息 | `Dict` |
| `get_group_members(chat_id)` | 获取群成员 | `List[str]` |
| `handle_message(raw_msg)` | 处理消息 | `Optional[str]` |
| `send_message(target, content)` | 发送消息 | `None` |
| `send_user_message(user_id, content)` | 发送用户消息 | `None` |

## 常见问题

### Q: 如何接收消息？

A: 企业微信使用回调模式，需要在企业微信管理后台配置回调URL。当有消息时，企业微信会主动推送到你的服务器。

### Q: 如何获取群聊ID？

A: 使用 `get_all_groups()` 或 `get_all_app_chats()` 方法获取所有群聊列表，每个群聊包含 `chatid` 字段。

### Q: 可以发送图片、文件吗？

A: 可以。需要先调用企业微信的媒体上传API上传文件，然后发送对应的消息类型。当前版本只实现了文本消息，可以根据需要扩展。

### Q: access_token 如何管理？

A: 客户端会自动管理 access_token，包括获取和刷新。token 有效期为2小时，会提前5分钟刷新。

## 相关文档

- [企业微信API文档](https://developer.work.weixin.qq.com/document/)
- [应用回调配置](https://developer.work.weixin.qq.com/document/path/90930)
- [消息推送](https://developer.work.weixin.qq.com/document/path/90236)

## 注意事项

1. **Token管理**: access_token 会自动刷新，有效期为2小时
2. **频率限制**: 企业微信API有频率限制，请注意调用频率
3. **回调验证**: 首次配置回调URL时需要验证
4. **消息加解密**: 回调消息需要解密处理
5. **群聊权限**: 应用只能操作自己创建或加入的群聊

