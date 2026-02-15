# 项目结构说明

## 目录结构

```
We-Bussiness-Manager/
├── config/                 # 配置文件
│   ├── __init__.py
│   ├── settings.py        # 全局配置（环境变量、API Key等）
│   ├── known_entities.py  # 已知实体定义（服务类型、商品类型等）
│   └── prompts.py         # LLM Prompt 定义
│
├── db/                    # 数据库层
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy ORM 模型
│   └── repository.py      # 数据访问层（CRUD操作）
│
├── parsing/               # 消息解析模块
│   ├── __init__.py
│   ├── preprocessor.py   # 消息预处理器（规则引擎）
│   ├── llm_parser.py     # LLM 解析引擎（OpenAI/Claude）
│   ├── pipeline.py       # 消息处理流水线
│   └── entity_resolver.py # 实体消歧（名称→ID映射）
│
├── services/             # 业务逻辑层
│   ├── __init__.py
│   ├── summary_svc.py    # 汇总报表服务
│   ├── inventory_svc.py  # 库存管理服务
│   └── membership_svc.py # 会员管理服务
│
├── core/                 # 核心模块
│   ├── __init__.py
│   ├── bot.py           # 微信机器人主类
│   ├── message_router.py # 消息路由（区分@指令和被动监听）
│   ├── command_handler.py # 命令处理器
│   └── scheduler.py     # 定时任务调度器
│
├── scripts/              # 工具脚本
│   ├── __init__.py
│   └── init_db.py       # 数据库初始化脚本
│
├── tests/               # 测试文件
│   ├── __init__.py
│   ├── test_preprocessor.py
│   └── fixtures/
│       └── sample_messages.json
│
├── data/                # 数据目录（数据库文件、日志等）
├── logs/                # 日志目录
│
├── main.py              # 主程序入口
├── requirements.txt     # Python 依赖
├── docker-compose.yml   # Docker 部署配置
├── Dockerfile          # Docker 镜像定义
├── README.md          # 项目说明
├── QUICKSTART.md       # 快速开始指南
└── design.md          # 设计文档
```

## 核心模块说明

### 1. config/ - 配置管理
- `settings.py`: 使用 pydantic-settings 管理环境变量配置
- `known_entities.py`: 定义已知的服务类型、商品类型等
- `prompts.py`: 定义 LLM 的系统提示词和用户提示词模板

### 2. db/ - 数据层
- `models.py`: SQLAlchemy ORM 模型，对应数据库表结构
- `repository.py`: 数据访问层，封装所有数据库操作

### 3. parsing/ - 消息解析
- `preprocessor.py`: 规则引擎，过滤噪声、提取日期、粗分类
- `llm_parser.py`: LLM 解析器，支持 OpenAI 和 Claude
- `pipeline.py`: 完整的消息处理流水线
- `entity_resolver.py`: 实体名称到数据库ID的映射

### 4. services/ - 业务逻辑
- `summary_svc.py`: 生成每日/月度汇总报表
- `inventory_svc.py`: 库存管理相关业务逻辑
- `membership_svc.py`: 会员管理相关业务逻辑

### 5. core/ - 核心功能
- `bot.py`: 微信机器人主类，处理微信消息接收和发送
- `message_router.py`: 消息路由器，区分@指令和被动监听
- `command_handler.py`: 命令处理器，实现各种@机器人指令
- `scheduler.py`: 定时任务调度器，如每日汇总

## 数据流

```
微信群消息
    ↓
WeChatBot (bot.py)
    ↓
MessageRouter (message_router.py)
    ├─→ @机器人 → CommandHandler → 返回结果
    └─→ 普通消息 → MessagePipeline
                    ↓
                PreProcessor (规则过滤)
                    ↓
                LLMParser (LLM解析)
                    ↓
                DatabaseRepository (入库)
```

## 关键设计决策

1. **两阶段解析**：先用规则引擎过滤噪声，再用 LLM 解析，降低成本
2. **置信度机制**：低置信度记录标记为待确认，需要人工审核
3. **实体自动创建**：遇到新顾客/员工时自动创建记录
4. **消息去重**：基于微信消息ID防止重复处理
5. **Mock模式**：支持在没有微信环境时测试其他功能

## 扩展点

1. **新增服务类型**：在 `config/known_entities.py` 中添加
2. **新增命令**：在 `core/command_handler.py` 的 `COMMANDS` 字典中添加
3. **新增业务逻辑**：在 `services/` 目录下创建新的服务类
4. **数据库迁移**：使用 Alembic 进行数据库版本管理（待实现）

