# 企业微信机器人接口

基于企业微信 API 实现的功能完整的机器人系统，作为 Agent 的用户层接口。

## 功能特性

### 核心功能

1. **消息收发**
   - 文本消息
   - Markdown 消息
   - 图片消息
   - 文件消息
   - 支持群聊和私聊

2. **群聊管理**
   - 查询所有参与的群聊
   - 获取群聊详细信息和成员列表
   - 创建新群聊
   - 修改群聊信息（名称、群主、成员）
   - 批量发送消息
   - 群聊搜索和统计

3. **用户管理**
   - 查询用户信息
   - 获取部门成员列表
   - 用户搜索
   - 批量获取用户信息

4. **消息回调**
   - 接收企业微信消息回调
   - 消息签名验证
   - 消息加密/解密
   - 事件处理

## 架构设计

```
interface/wechat/
├── __init__.py           # 模块初始化
├── bot.py                # 机器人主类（Interface 实现）
├── wecom_client.py       # 企业微信 API 客户端
├── callback_server.py    # 消息回调服务器
├── manager.py            # 群聊和用户管理器
├── message_router.py     # 消息路由器
└── README.md            # 本文档
```

### 组件说明

1. **WeChatWorkClient** (`wecom_client.py`)
   - 企业微信 API 的底层封装
   - 处理认证、token 管理
   - 提供所有 API 调用方法

2. **WeChatBot** (`bot.py`)
   - 实现 `Interface` 抽象基类
   - 整合客户端和回调服务器
   - 提供统一的机器人接口

3. **WeChatCallbackServer** (`callback_server.py`)
   - FastAPI 服务器
   - 处理消息回调
   - 消息加密/解密
   - 签名验证

4. **WeChatGroupManager & WeChatUserManager** (`manager.py`)
   - 高级管理功能
   - 缓存管理
   - 批量操作
   - 搜索和统计

5. **WeChatMessageRouter** (`message_router.py`)
   - 消息路由和分发
   - 区分命令消息和业务消息
   - 与业务层对接

## 快速开始

### 1. 配置环境变量

在 `.env` 文件中配置以下参数：

```bash
# 企业微信配置
WECHAT_WORK_CORP_ID=your_corp_id           # 企业 ID
WECHAT_WORK_SECRET=your_secret             # 应用密钥
WECHAT_WORK_AGENT_ID=your_agent_id         # 应用 ID
WECHAT_WORK_TOKEN=your_token               # 回调 Token
WECHAT_WORK_ENCODING_AES_KEY=your_key      # 回调加密密钥

# HTTP 服务配置
WECHAT_HTTP_HOST=0.0.0.0                   # 监听地址
WECHAT_HTTP_PORT=8000                      # 监听端口

# 目标群聊（可选，逗号分隔）
WECHAT_GROUP_IDS=chatid1,chatid2
```

### 2. 初始化机器人

```python
from interface.wechat.bot import WeChatBot
from interface.wechat.message_router import WeChatMessageRouter
from parsing.pipeline import MessagePipeline
from business.command_handler import BusinessCommandHandler

# 创建消息处理组件
pipeline = MessagePipeline(...)
command_handler = BusinessCommandHandler(...)
router = WeChatMessageRouter(pipeline, command_handler)

# 创建并启动机器人
bot = WeChatBot(router, enable_callback=True)
bot.start()
```

### 3. 配置企业微信回调

在企业微信管理后台：

1. 进入 **应用管理** -> 选择你的应用
2. 进入 **接收消息** 设置
3. 配置回调 URL：`http://your-domain:8000/callback`
4. 填写 Token 和 EncodingAESKey（与 `.env` 中一致）
5. 保存并验证 URL

## 使用示例

### 发送消息

```python
# 发送文本消息到群聊
bot.send_message("chatid", "Hello, World!")

# 发送 Markdown 消息
bot.send_markdown_message("chatid", """
# 标题
这是一个 **Markdown** 消息
""")

# 发送图片
bot.send_image("chatid", "/path/to/image.jpg")

# 发送文件
bot.send_file("chatid", "/path/to/file.pdf")

# 发送私聊消息
bot.send_user_message("userid", "Hello!")
```

### 群聊管理

```python
# 获取所有群聊
groups = bot.get_all_groups()

# 获取群聊详细信息
info = bot.get_group_info("chatid")

# 获取群成员
members = bot.get_group_members("chatid")

# 创建群聊
chat_id = bot.create_group(
    name="新群聊",
    owner="owner_userid",
    members=["user1", "user2", "user3"]
)

# 修改群聊
bot.update_group(
    chat_id="chatid",
    name="新名称",
    add_members=["user4"],
    remove_members=["user1"]
)
```

### 用户管理

```python
# 获取用户信息
user_info = bot.get_user_info("userid")

# 获取部门成员
users = bot.get_department_users(department_id=1, fetch_child=True)
```

### 使用管理器（高级功能）

```python
from interface.wechat.manager import WeChatGroupManager, WeChatUserManager

# 群聊管理器
group_mgr = WeChatGroupManager(bot.client)

# 搜索群聊
groups = group_mgr.search_groups("关键词")

# 获取统计信息
stats = group_mgr.get_group_statistics()

# 批量发送消息
results = group_mgr.batch_send_message(
    chat_ids=["chat1", "chat2"],
    content="批量消息"
)

# 用户管理器
user_mgr = WeChatUserManager(bot.client)

# 搜索用户
users = user_mgr.search_users_by_name("张三")

# 批量获取用户信息
user_infos = user_mgr.get_users_info(["user1", "user2", "user3"])
```

## 消息处理流程

```
企业微信消息 
    ↓
回调服务器接收
    ↓
签名验证 & 消息解密
    ↓
消息路由器分发
    ↓
┌────────────┬────────────┐
│ @机器人消息 │  普通消息   │
│  (命令处理) │ (业务解析)  │
└────────────┴────────────┘
    ↓              ↓
命令处理器      消息处理流水线
    ↓              ↓
返回结果        存储到数据库
```

## API 文档

### WeChatBot 类

#### 初始化

```python
def __init__(self, router: WeChatMessageRouter, enable_callback: bool = True)
```

#### 生命周期方法

- `start()`: 启动机器人
- `stop()`: 停止机器人
- `is_running()`: 检查运行状态

#### 消息发送

- `send_message(target: str, content: str)`: 发送文本消息到群聊
- `send_user_message(user_id: str, content: str)`: 发送私聊消息
- `send_markdown_message(chat_id: str, content: str)`: 发送 Markdown 消息
- `send_image(chat_id: str, image_path: str)`: 发送图片
- `send_file(chat_id: str, file_path: str)`: 发送文件

#### 群聊管理

- `get_all_groups() -> List[Dict]`: 获取所有群聊
- `get_group_info(chat_id: str) -> Dict`: 获取群聊信息
- `get_group_members(chat_id: str) -> List[str]`: 获取群成员
- `create_group(name, owner, members, chat_id=None) -> str`: 创建群聊
- `update_group(chat_id, name=None, owner=None, add_members=None, remove_members=None) -> bool`: 修改群聊

#### 用户管理

- `get_user_info(user_id: str) -> Dict`: 获取用户信息
- `get_department_users(department_id: int, fetch_child: bool) -> List[Dict]`: 获取部门成员

#### 消息处理

- `async handle_message(raw_msg: Dict) -> Optional[str]`: 处理接收到的消息

### WeChatWorkClient 类

底层 API 客户端，提供所有企业微信 API 的调用方法。

详细 API 列表参见 `wecom_client.py` 源码。

## 注意事项

### 权限配置

确保你的企业微信应用具有以下权限：

1. **消息发送权限**
   - 发送消息到群聊
   - 发送消息给用户

2. **通讯录权限**
   - 获取成员信息
   - 获取部门成员列表

3. **应用管理权限**
   - 创建群聊
   - 修改群聊信息

### 回调服务器

1. **网络配置**
   - 确保回调 URL 可以从外网访问
   - 如果在内网，需要配置内网穿透或反向代理

2. **安全性**
   - Token 和 EncodingAESKey 要保密
   - 建议使用 HTTPS
   - 回调服务器会自动验证消息签名

3. **性能优化**
   - 回调处理应该尽快返回
   - 耗时操作放到后台任务中执行

### 消息限制

企业微信 API 有以下限制：

1. **消息频率**
   - 应用发送消息频率限制：20000次/分钟
   - 单个用户接收消息限制：20条/分钟

2. **群聊限制**
   - 群聊成员数：2-2000 人
   - 单个应用最多创建 1000 个群聊

3. **文件大小**
   - 图片：最大 2MB
   - 文件：最大 20MB

## 故障排查

### 回调验证失败

1. 检查 Token 和 EncodingAESKey 是否正确
2. 检查回调 URL 是否可访问
3. 查看服务器日志获取详细错误信息

### 消息发送失败

1. 检查 access_token 是否有效
2. 检查群聊 ID 是否正确
3. 检查应用是否有发送权限
4. 查看错误码和错误信息

### 无法接收消息

1. 确认回调服务器正在运行
2. 确认回调 URL 配置正确
3. 检查企业微信后台的回调配置
4. 查看回调服务器日志

## 扩展开发

### 添加自定义消息处理器

```python
# 在 bot.py 中修改 _handle_callback_message 方法
async def _handle_callback_message(self, msg_dict: Dict[str, Any]) -> Optional[str]:
    msg_type = msg_dict.get('MsgType', '')
    
    if msg_type == 'image':
        # 处理图片消息
        return await self._handle_image_message(msg_dict)
    elif msg_type == 'file':
        # 处理文件消息
        return await self._handle_file_message(msg_dict)
    else:
        # 默认处理
        raw_msg = self._convert_wecom_message(msg_dict)
        response = await self.handle_message(raw_msg)
        if response:
            return self._build_text_reply_xml(msg_dict, response)
    
    return None
```

### 添加自定义事件处理器

```python
# 在 bot.py 中修改 _handle_callback_event 方法
async def _handle_callback_event(self, event_dict: Dict[str, Any]) -> Optional[str]:
    event_type = event_dict.get('Event', '')
    
    if event_type == 'subscribe':
        # 处理关注事件
        return self._build_text_reply_xml(event_dict, "欢迎关注！")
    elif event_type == 'enter_agent':
        # 处理进入应用事件
        return self._build_text_reply_xml(event_dict, "欢迎使用！")
    
    return None
```

## 参考资料

- [企业微信 API 文档](https://developer.work.weixin.qq.com/document/)
- [企业微信群聊机器人](https://developer.work.weixin.qq.com/document/path/90664)
- [消息接收与发送](https://developer.work.weixin.qq.com/document/path/90239)

## 更新日志

### v2.0.0 (2026-02-16)

- 重构整个 interface 模块
- 使用企业微信 API 实现完整的机器人功能
- 添加消息回调服务器
- 添加群聊和用户管理器
- 支持多种消息类型（文本、Markdown、图片、文件）
- 支持群聊管理（创建、修改、查询）
- 添加缓存机制和批量操作
- 完善文档和示例代码

