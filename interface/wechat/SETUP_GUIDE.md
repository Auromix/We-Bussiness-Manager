# 企业微信机器人配置指南

本指南将帮助你从零开始配置企业微信机器人。

## 前提条件

1. 拥有企业微信管理员权限
2. 服务器具有公网 IP 或已配置内网穿透
3. Python 3.8+ 环境
4. 已安装项目依赖

## 配置步骤

### 第一步：创建企业微信应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/)

2. 进入 **应用管理** -> **应用** -> **创建应用**

3. 填写应用信息：
   - 应用名称：例如 "业务助手"
   - 应用介绍：简单描述应用功能
   - 可见范围：选择需要使用机器人的部门或成员

4. 创建成功后，记录以下信息：
   - **AgentId**（应用 ID）
   - **Secret**（应用密钥）

5. 在企业信息页面获取：
   - **CorpId**（企业 ID）

### 第二步：配置应用权限

在应用详情页面，确保已开启以下权限：

#### 1. 接口权限

进入 **企业应用权限** -> **接口权限**，确保开启：

- ✅ 发送消息到群聊
- ✅ 获取成员基本信息
- ✅ 获取部门成员
- ✅ 管理群聊
- ✅ 发送应用消息

#### 2. 通讯录权限

进入 **企业应用权限** -> **通讯录权限**，至少需要：

- ✅ 成员信息读权限
- ✅ 部门信息读权限

### 第三步：配置消息接收

#### 1. 准备回调服务器

确保你的服务器满足以下要求：

- 可以从公网访问（或通过内网穿透）
- 已安装并启动回调服务
- 防火墙已开放相应端口（默认 8000）

**内网穿透工具推荐：**
- [ngrok](https://ngrok.com/)
- [frp](https://github.com/fatedier/frp)
- [natapp](https://natapp.cn/)

使用 ngrok 示例：
```bash
ngrok http 8000
```

记录生成的公网 URL，例如：`https://abc123.ngrok.io`

#### 2. 配置接收消息

在应用详情页面，进入 **接收消息** 设置：

1. **URL**：填写你的回调地址
   - 格式：`http://your-domain:8000/callback`
   - 或使用内网穿透：`https://abc123.ngrok.io/callback`

2. **Token**：随机字符串，建议 10-32 位
   - 可以使用这个命令生成：
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(16))"
     ```

3. **EncodingAESKey**：43 位随机字符串
   - 可以点击 "随机生成" 按钮
   - 或使用命令生成：
     ```bash
     python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode()[:43])"
     ```

4. 点击 **保存** 并等待验证
   - 企业微信会向你的回调 URL 发送验证请求
   - 如果验证失败，检查：
     - URL 是否可访问
     - Token 和 EncodingAESKey 是否正确
     - 回调服务是否正在运行

### 第四步：配置环境变量

在项目根目录创建 `.env` 文件（如果还没有）：

```bash
# 企业微信配置
WECHAT_WORK_CORP_ID=ww1234567890abcdef       # 第一步获取的企业 ID
WECHAT_WORK_SECRET=YOUR_SECRET_HERE          # 第一步获取的应用密钥
WECHAT_WORK_AGENT_ID=1000001                 # 第一步获取的应用 ID
WECHAT_WORK_TOKEN=YOUR_TOKEN_HERE            # 第三步配置的 Token
WECHAT_WORK_ENCODING_AES_KEY=YOUR_KEY_HERE   # 第三步配置的 EncodingAESKey

# HTTP 服务配置
WECHAT_HTTP_HOST=0.0.0.0                     # 监听地址
WECHAT_HTTP_PORT=8000                        # 监听端口

# 目标群聊（可选）
# 如果只想机器人响应特定群聊，可以在这里配置
# WECHAT_GROUP_IDS=chatid1,chatid2,chatid3

# LLM 配置（如果需要）
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
PRIMARY_LLM=openai

# 数据库配置
DATABASE_URL=sqlite:///data/store.db
```

**安全提示：**
- `.env` 文件包含敏感信息，不要提交到 Git
- 确保 `.gitignore` 中包含 `.env`
- 生产环境建议使用环境变量或密钥管理服务

### 第五步：启动服务

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 测试配置

运行测试脚本验证配置是否正确：

```python
# test_wechat_config.py
from config.settings import settings
from interface.wechat.wecom_client import WeChatWorkClient

# 测试连接
client = WeChatWorkClient(
    corp_id=settings.wechat_work_corp_id,
    secret=settings.wechat_work_secret,
    agent_id=settings.wechat_work_agent_id
)

# 测试获取 token
try:
    token = client._get_access_token()
    print(f"✅ Access token 获取成功: {token[:20]}...")
except Exception as e:
    print(f"❌ Access token 获取失败: {e}")

# 测试获取群聊列表
try:
    groups = client.get_all_app_chats()
    print(f"✅ 获取到 {len(groups)} 个群聊")
    for group in groups[:3]:
        print(f"  - {group.get('name')} ({group.get('chatid')})")
except Exception as e:
    print(f"❌ 获取群聊列表失败: {e}")
```

运行测试：
```bash
python test_wechat_config.py
```

#### 3. 启动机器人

```bash
python main.py
```

或者使用后台运行：
```bash
nohup python main.py > logs/bot.log 2>&1 &
```

使用 systemd（推荐生产环境）：

创建 `/etc/systemd/system/webot.service`：

```ini
[Unit]
Description=WeChat Business Manager Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/We-Bussiness-Manager
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable webot
sudo systemctl start webot
sudo systemctl status webot
```

### 第六步：创建群聊并测试

#### 1. 创建测试群聊

方法一：使用脚本创建

```python
# scripts/create_test_group.py
from interface.wechat.wecom_client import WeChatWorkClient
from config.settings import settings

client = WeChatWorkClient(
    corp_id=settings.wechat_work_corp_id,
    secret=settings.wechat_work_secret,
    agent_id=settings.wechat_work_agent_id
)

# 创建群聊
chat_id = client.create_app_chat(
    name="业务助手测试群",
    owner="your_userid",  # 替换为你的 userid
    userlist=["user1", "user2", "user3"]  # 替换为实际的 userid
)

print(f"✅ 群聊创建成功: {chat_id}")
```

方法二：手动在企业微信客户端创建群聊

#### 2. 获取群聊 ID

```python
# scripts/list_groups.py
from interface.wechat.wecom_client import WeChatWorkClient
from config.settings import settings

client = WeChatWorkClient(
    corp_id=settings.wechat_work_corp_id,
    secret=settings.wechat_work_secret,
    agent_id=settings.wechat_work_agent_id
)

groups = client.get_all_app_chats()
for group in groups:
    print(f"{group.get('name')}: {group.get('chatid')}")
```

#### 3. 发送测试消息

```python
# test_send_message.py
from interface.wechat.wecom_client import WeChatWorkClient
from config.settings import settings

client = WeChatWorkClient(
    corp_id=settings.wechat_work_corp_id,
    secret=settings.wechat_work_secret,
    agent_id=settings.wechat_work_agent_id
)

# 替换为实际的 chatid
chat_id = "wrXXXXXXXXXXXXXXXX"

client.send_group_message(chat_id, "🤖 机器人测试消息")
print("✅ 消息发送成功")
```

#### 4. 测试接收消息

在企业微信客户端的测试群中发送消息：

```
@机器人 帮助
```

如果一切正常，机器人应该会回复帮助信息。

查看日志确认消息处理：
```bash
tail -f logs/bot.log
```

## 常见问题

### Q1: 回调 URL 验证失败

**可能原因：**
- 回调服务未启动或无法访问
- Token 或 EncodingAESKey 配置错误
- 防火墙阻止了请求

**解决方法：**
1. 确认回调服务正在运行：
   ```bash
   curl http://localhost:8000/callback
   ```

2. 检查配置是否正确：
   ```bash
   python -c "from config.settings import settings; print(settings.wechat_work_token)"
   ```

3. 查看服务日志：
   ```bash
   tail -f logs/bot.log
   ```

### Q2: 获取 Access Token 失败

**可能原因：**
- CorpId 或 Secret 配置错误
- 网络问题
- 应用已被停用

**解决方法：**
1. 检查 CorpId 和 Secret 是否正确
2. 确认应用状态为 "已启用"
3. 尝试重新生成 Secret

### Q3: 发送消息失败

**错误码 40013**：Invalid CorpId
- 检查 CorpId 是否正确

**错误码 40014**：Invalid access token
- Access token 已过期或无效
- 检查 Secret 是否正确

**错误码 60020**：ChatId not found
- 群聊 ID 不存在或已解散
- 使用 `get_all_app_chats()` 确认群聊 ID

**错误码 60011**：No privilege
- 应用没有发送消息的权限
- 检查应用权限配置

### Q4: 收不到消息回调

**可能原因：**
- 回调 URL 配置错误
- 回调服务未运行
- 消息未 @ 机器人（如果配置了只响应 @）

**解决方法：**
1. 确认回调配置已保存并验证通过
2. 检查回调服务运行状态
3. 在群聊中 @ 机器人发送消息
4. 查看回调服务日志

### Q5: 内网穿透不稳定

**推荐方案：**
1. 使用专业的内网穿透服务（如 natapp 付费版）
2. 使用自建 frp 服务器
3. 部署到云服务器（最推荐）

## 性能优化

### 1. 启用缓存

使用 Redis 缓存用户信息和群聊信息：

```bash
# .env
REDIS_URL=redis://localhost:6379/0
```

### 2. 异步处理

对于耗时操作，使用后台任务：

```python
import asyncio

async def long_running_task():
    # 耗时操作
    pass

# 在消息处理中
asyncio.create_task(long_running_task())
```

### 3. 消息队列

使用消息队列处理高并发消息：

```bash
pip install celery redis
```

### 4. 负载均衡

部署多个回调服务实例，使用 Nginx 负载均衡：

```nginx
upstream wechat_callback {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    location /callback {
        proxy_pass http://wechat_callback;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 安全建议

1. **使用 HTTPS**
   - 生产环境必须使用 HTTPS
   - 使用 Let's Encrypt 免费证书

2. **密钥管理**
   - 不要在代码中硬编码密钥
   - 使用环境变量或密钥管理服务
   - 定期轮换密钥

3. **访问控制**
   - 限制回调 URL 的访问来源（企业微信服务器 IP）
   - 启用消息签名验证
   - 记录所有访问日志

4. **监控告警**
   - 监控服务可用性
   - 监控异常请求
   - 设置告警通知

## 下一步

配置完成后，你可以：

1. 阅读 [README.md](./README.md) 了解详细功能
2. 查看 [使用示例](../../examples/)
3. 自定义消息处理逻辑
4. 集成业务系统

## 技术支持

如果遇到问题：

1. 查看 [企业微信 API 文档](https://developer.work.weixin.qq.com/document/)
2. 查看项目 [issues](https://github.com/your-repo/issues)
3. 查看日志文件 `logs/bot.log`

## 附录

### A. 错误码对照表

| 错误码 | 说明 | 解决方法 |
|-------|------|---------|
| 0 | 成功 | - |
| 40001 | 不合法的 secret 参数 | 检查 Secret 配置 |
| 40013 | 不合法的 CorpId | 检查 CorpId 配置 |
| 40014 | 不合法的 access_token | Token 已过期，重新获取 |
| 42001 | access_token 超时 | 自动刷新 |
| 60011 | 无权限操作 | 检查应用权限 |
| 60020 | chatid 不存在 | 检查群聊 ID |

完整错误码列表：[企业微信全局返回码](https://developer.work.weixin.qq.com/document/path/90313)

### B. 有用的命令

```bash
# 查看服务状态
systemctl status webot

# 重启服务
systemctl restart webot

# 查看实时日志
tail -f logs/bot.log

# 测试网络连接
curl https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=YOUR_CORPID&corpsecret=YOUR_SECRET

# 查看端口占用
netstat -tlnp | grep 8000

# 测试回调服务
curl http://localhost:8000/callback
```

### C. 环境变量完整列表

参见 [config/settings.py](../../config/settings.py) 了解所有可用的配置项。

