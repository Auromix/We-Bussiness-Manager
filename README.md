# 微信群托管机器人 — 健康理疗门店商业信息管理系统

## 项目简介

这是一个基于 LLM 的微信群消息解析系统，用于健康理疗门店的日常经营数据管理。系统能够：

- 被动监听群消息，自动解析业务相关的自然语言记录
- 响应 @机器人 指令，执行查询、汇总等操作
- 将非结构化的中文聊天消息转为结构化业务数据
- 每日自动生成汇总报告

## 技术栈

- Python 3.11+
- WeChatFerry (微信桥接)
- OpenAI gpt-4o-mini / Claude (LLM解析)
- SQLite / PostgreSQL (数据库)
- Redis (缓存)
- APScheduler (定时任务)
- SQLAlchemy 2.0 (ORM)

## 快速开始

### 1. 设置 Conda 环境（推荐）

```bash
# 使用自动安装脚本
./setup_conda_env.sh

# 或手动设置（见 conda_setup_guide.md）
conda create -n wechat-business-manager python=3.11 -y
conda activate wechat-business-manager
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key 等配置
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 运行测试（推荐先测试）

```bash
# 运行所有测试
pytest tests/ -v

# 或逐步测试各模块（见 TESTING_README.md）
./tests/run_module_tests.sh all
```

### 5. 运行机器人

```bash
python main.py
```

## 项目结构

```
wechat-store-bot/
├── config/          # 配置文件
├── core/            # 核心模块（bot, router, scheduler）
├── parsing/         # 消息解析模块
├── services/        # 业务逻辑层
├── db/              # 数据库模型和访问层
├── scripts/         # 工具脚本
└── tests/           # 测试文件
```

## 注意事项

1. **微信环境**：WeChatFerry 需要 Windows 环境运行，建议使用虚拟机或专用服务器
2. **API 成本**：系统使用 LLM 解析消息，建议先配置成本控制策略
3. **数据安全**：群聊消息包含个人信息，请妥善保管数据库

## 测试

### 快速测试

```bash
# 激活环境
conda activate wechat-business-manager

# 运行所有测试
pytest tests/ -v
```

### 详细测试指南

- **`TESTING_README.md`** - 完整的测试指南，包含逐步测试流程和人工验证检查点
- **`TEST_QUICK_REFERENCE.md`** - 快速参考卡片
- **`FINAL_TEST_REPORT.md`** - 测试结果报告

### 测试统计

- **总测试数**: 47（44个单元测试 + 3个集成测试）
- **通过率**: 100%
- **覆盖率**: 67%（核心模块 >80%）

## 详细文档

- **`design.md`** - 完整的设计文档
- **`TESTING_README.md`** - 测试指南（推荐阅读）
- **`QUICKSTART.md`** - 快速开始指南
- **`PROJECT_STRUCTURE.md`** - 项目结构说明

