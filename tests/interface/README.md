# Interface 模块测试

本目录包含 `interface/` 模块的完整测试套件。

## 测试覆盖

### 基础模块
- ✅ `test_base.py` - 接口抽象基类测试
- ✅ `test_manager.py` - 接口管理器测试

### 微信模块
- ✅ `wechat/test_bot.py` - 微信机器人测试
- ✅ `wechat/test_work_client.py` - 企业微信 API 客户端测试
- ✅ `wechat/test_message_router.py` - 消息路由测试
- ✅ `wechat/test_http_server.py` - HTTP API 服务器测试

## 运行测试

### 使用 conda 环境

```bash
# 激活环境
eval "$(conda shell.bash hook)"
conda activate wechat-business-manager

# 运行所有 interface 测试
pytest tests/interface/ -v

# 运行特定测试文件
pytest tests/interface/test_base.py -v
pytest tests/interface/wechat/test_bot.py -v
```

## 测试统计

- **总测试数**: 66
- **通过率**: 100%
- **覆盖模块**: 
  - `interface.base`
  - `interface.manager`
  - `interface.wechat.bot`
  - `interface.wechat.work_client`
  - `interface.wechat.message_router`
  - `interface.wechat.http_server`

## 代码规范审查

所有代码已按照 Google Python 代码规范进行审查和修复：

1. ✅ **导入顺序**: 标准库 -> 第三方库 -> 本地库
2. ✅ **类型注解**: 使用 `typing` 模块的类型注解
3. ✅ **文档字符串**: 使用 Google 风格的文档字符串
4. ✅ **命名规范**: 遵循 PEP 8 命名规范

## 环境变量配置

### 企业微信配置（可选）

如果使用企业微信 API 模式，需要配置以下环境变量：

```bash
# 企业微信配置
WECHAT_WORK_CORP_ID=your_corp_id          # 企业 ID
WECHAT_WORK_SECRET=your_secret            # 应用密钥
WECHAT_WORK_AGENT_ID=your_agent_id        # 应用 ID
```

### HTTP API 模式配置（可选）

如果使用 HTTP API 模式，可以配置：

```bash
# HTTP API 配置
WECHAT_HTTP_HOST=0.0.0.0                  # 监听地址（默认：0.0.0.0）
WECHAT_HTTP_PORT=8000                    # 监听端口（默认：8000）
```

### 群组配置（可选）

```bash
# 目标群组 ID（逗号分隔）
WECHAT_GROUP_IDS=group1,group2,group3
```

## 配置说明

### 企业微信 API 模式

📖 **详细配置指南**：请查看 [企业微信后台配置指南](../../docs/WECHAT_WORK_SETUP.md)

快速步骤：

1. **获取企业 ID (corp_id)**
   - 登录[企业微信管理后台](https://work.weixin.qq.com/)
   - 进入"我的企业" -> "企业信息"
   - 复制"企业 ID"

2. **创建应用并获取 Secret**
   - 进入"应用管理" -> "自建"
   - 创建新应用或选择现有应用
   - 在应用详情页获取"Secret"（⚠️ 只显示一次，请立即保存）

3. **获取应用 ID (agent_id)**
   - 在应用详情页获取"AgentId"

4. **配置应用权限**
   - 开启"发送消息到群聊"权限
   - 开启"发送消息到会话"权限
   - 设置应用的可见范围

5. **配置回调 URL**（可选，用于接收消息）
   - 在应用详情页配置"接收消息服务器"
   - URL 格式：`https://your-domain.com/wechat/callback`
   - Token 和 EncodingAESKey 需要保存用于验证

### HTTP API 模式

HTTP API 模式不需要企业微信配置，适用于通过外部服务转发消息的场景。

1. **启动 HTTP 服务器**
   ```python
   from interface.wechat.http_server import WeChatHTTPServer
   from interface.wechat.bot import WeChatBot
   
   # 创建 bot 和 server
   server = WeChatHTTPServer(bot, host="0.0.0.0", port=8000)
   server.start()
   ```

2. **发送消息到服务器**
   ```bash
   curl -X POST http://localhost:8000/wechat/message \
     -H "Content-Type: application/json" \
     -d '{
       "content": "测试消息",
       "group_id": "group_123",
       "sender_nickname": "测试用户",
       "sender_wechat_id": "user_123",
       "is_at_bot": false
     }'
   ```

## 测试依赖

确保已安装以下依赖：

```bash
pip install pytest pytest-asyncio fastapi uvicorn requests httpx
```

## 注意事项

1. **测试使用 Mock**: 所有测试都使用 Mock 对象，不需要真实的企业微信环境
2. **异步测试**: 部分测试使用 `@pytest.mark.asyncio` 装饰器
3. **环境隔离**: 测试不会影响实际运行环境

