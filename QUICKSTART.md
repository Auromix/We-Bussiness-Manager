# 快速开始指南

## 1. 环境准备

### 系统要求
- Python 3.11+
- Windows 系统（用于 WeChatFerry，如果使用企业微信API则不需要）
- OpenAI API Key 或 Anthropic API Key

### 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...  # 可选

DATABASE_URL=sqlite:///data/store.db
BOT_NAME=小助手
TARGET_GROUP_NAME=门店经营群
PRIMARY_LLM=openai
DAILY_SUMMARY_TIME=21:00
```

## 3. 初始化数据库

```bash
python scripts/init_db.py
```

这将创建所有必要的数据库表并插入初始数据。

## 4. 运行机器人

### 方式一：直接运行（Windows + WeChatFerry）

```bash
python main.py
```

### 方式二：Docker 运行

```bash
docker-compose up -d
```

## 5. 使用说明

### 被动监听

机器人会自动监听群消息，解析业务相关的记录：

- `1.28段老师头疗30` → 自动解析为服务记录
- `理疗开卡1000姚老师` → 自动解析为会员充值
- `1.28姚老师理疗198-20李哥178` → 自动解析服务+提成

### 主动命令

在群中 @机器人 并发送命令：

- `@机器人 今日总结` - 查看今日经营汇总
- `@机器人 库存总结` - 查看库存情况
- `@机器人 会员总结` - 查看会员汇总
- `@机器人 查询 段老师` - 查询某位顾客的记录
- `@机器人 帮助` - 查看所有可用命令

## 6. 注意事项

1. **WeChatFerry 安装**：如果使用 WeChatFerry，需要单独安装：
   ```bash
   pip install wcferry
   ```
   注意：WeChatFerry 需要 Windows 环境和特定版本的微信客户端。

2. **API 成本**：系统使用 LLM 解析消息，建议：
   - 使用 gpt-4o-mini 降低成本
   - 配置置信度阈值，低置信度记录需要人工确认
   - 定期检查解析结果

3. **数据备份**：定期备份 `data/store.db` 文件。

## 7. 故障排查

### 问题：无法连接微信

- 检查是否在 Windows 环境运行
- 检查微信客户端版本是否兼容 WeChatFerry
- 尝试使用模拟模式测试其他功能

### 问题：LLM 解析失败

- 检查 API Key 是否正确
- 检查网络连接
- 查看日志文件 `logs/bot_*.log`

### 问题：数据库错误

- 确保 `data/` 目录有写权限
- 尝试重新初始化数据库：`python scripts/init_db.py`

## 8. 开发模式

运行测试：

```bash
pytest tests/
```

查看日志：

```bash
tail -f logs/bot_*.log
```

