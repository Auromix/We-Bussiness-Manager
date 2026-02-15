# 微信群托管机器人 — 健康理疗门店商业信息管理系统

## 技术架构设计文档 (AI Coding Reference)

---

## 1. 项目概述

### 1.1 业务场景

一家健康疗养理疗店，员工在微信群中以自然语言记录日常经营数据（理疗服务、保健品销售、药品库存、会员管理）。系统需要：

1. **被动监听**：持续监听群消息，解析业务相关的自然语言记录
2. **主动响应**：当被 @机器人 时，执行特定指令（如"库存总结"、"会员总结"）
3. **智能解析**：将非结构化的中文聊天消息转为结构化业务数据
4. **每日审查**：在每日结束时生成汇总报告，发送到群中供确认

### 1.2 核心挑战

根据实际群聊记录分析，消息具有以下特征：

- **日期格式不统一**：`1/24`、`1.28`、`1月26日`、`2|1`（竖线分隔）混合使用
- **金额位置不固定**：`头疗30`、`30头疗`、`理疗体验100`、`100体验理疗`
- **包含修正消息**：如 `26-27号错误，改25-26`
- **包含无关消息**：闲聊、表情包、停车提醒等噪声
- **多个记录员**：不同人记录风格不同（如"六亿（叶维忠）"vs"不在依赖（郑传华）"）
- **包含复合消息**：如 `2.3段老师490\n姚老师490理疗合计980` 一条消息多笔记录
- **提成/折扣逻辑**：如 `理疗198-20李哥178`（扣除提成）
- **开卡/充值**：如 `理疗开卡1000姚老师`

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        微信群 (WeChat Group)                      │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ 消息推送                          │ 回复消息
               ▼                                  ▲
┌──────────────────────────────────────────────────────────────────┐
│                    WeChat Bridge Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │  WeChatFerry  │  │  itchat/hook │  │  企业微信 API       │     │
│  │  (推荐方案)   │  │  (备选)      │  │  (如果可用)         │     │
│  └──────┬───────┘  └──────────────┘  └────────────────────┘     │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Core Application (Python/Node.js)              │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Message Router   │  │ Command Handler  │  │ Passive Parser │  │
│  │ (消息路由)       │  │ (@机器人 指令)   │  │ (被动解析)     │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                    │                     │           │
│           ▼                    ▼                     ▼           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              LLM Parsing Engine (NLU 层)                    │ │
│  │  ┌─────────────────┐    ┌─────────────────┐                │ │
│  │  │  OpenAI API      │    │  Claude API      │                │ │
│  │  │  (gpt-4o-mini)   │    │  (claude-sonnet)  │                │ │
│  │  └─────────────────┘    └─────────────────┘                │ │
│  │  - 消息意图识别                                              │ │
│  │  - 实体提取 (日期/人名/服务/金额)                            │ │
│  │  - 修正指令理解                                              │ │
│  │  - 噪声过滤                                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Business Logic Layer                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ 理疗服务 │ │ 保健品   │ │ 药品库存 │ │ 会员管理     │  │ │
│  │  │ Service  │ │ Product  │ │ Inventory│ │ Membership   │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Scheduler (定时任务)                             │ │
│  │  - 每日汇总报告生成 (21:00)                                  │ │
│  │  - 未确认记录提醒                                             │ │
│  │  - 月度/周度统计                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Data Layer                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  SQLite/PostgreSQL│ │  Redis (缓存)    │  │  消息日志       │  │
│  │  (主数据库)       │ │  (会话上下文)    │  │  (原始消息存档) │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 推荐技术栈

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| 语言 | **Python 3.11+** | 生态成熟，LLM SDK 最佳支持，中文NLP库丰富 |
| 微信桥接 | **WeChatFerry (wcferry)** | 开源、稳定、支持个人微信，Hook方式最可靠 |
| LLM | **OpenAI gpt-4o-mini (主) + Claude claude-sonnet-4-20250514 (备)** | gpt-4o-mini 成本低、中文好；Claude 作为 fallback |
| 数据库 | **SQLite (初期) → PostgreSQL (扩展)** | 轻量启动，后期可迁移 |
| 缓存 | **Redis** | 存储会话上下文、LLM解析缓存、防重复 |
| 定时任务 | **APScheduler** | Python原生，轻量 |
| ORM | **SQLAlchemy 2.0** | 类型安全，支持异步 |
| 消息队列 | **内存队列 (初期) → Redis Queue (扩展)** | 消息量不大，初期无需Kafka |
| 部署 | **Docker Compose** | 微信Hook需要Windows环境，Docker便于管理 |

---

## 3. 数据库设计

### 3.1 ER 关系

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   customers   │──┐  │  service_records  │     │    employees     │
│──────────────│  │  │──────────────────│     │──────────────────│
│ id (PK)      │  ├─>│ customer_id (FK) │  ┌─>│ id (PK)         │
│ name         │  │  │ employee_id (FK) │──┘  │ name            │
│ phone        │  │  │ service_type     │     │ wechat_nickname  │
│ created_at   │  │  │ amount           │     │ role             │
└──────────────┘  │  │ commission       │     └──────────────────┘
                  │  │ service_date     │
┌──────────────┐  │  │ raw_message      │     ┌──────────────────┐
│  memberships  │  │  │ parsed_by_llm    │     │  product_sales   │
│──────────────│  │  │ confirmed        │     │──────────────────│
│ id (PK)      │  │  └──────────────────┘     │ id (PK)         │
│ customer_id  │──┘                            │ product_id (FK) │
│ card_type    │     ┌──────────────────┐     │ customer_id     │
│ total_amount │     │    products      │     │ quantity         │
│ balance      │     │──────────────────│     │ amount           │
│ remaining    │     │ id (PK)         │     │ sale_date        │
│   _sessions  │     │ name            │     │ raw_message      │
│ created_at   │     │ category        │     └──────────────────┘
└──────────────┘     │ stock_quantity  │
                     │ unit_price      │     ┌──────────────────┐
                     └──────────────────┘     │  raw_messages    │
                                              │──────────────────│
                                              │ id (PK)         │
                                              │ sender_nickname  │
                                              │ content          │
                                              │ timestamp        │
                                              │ is_business      │
                                              │ parse_result     │
                                              │ parse_status     │
                                              └──────────────────┘
```

### 3.2 DDL (SQLite/PostgreSQL 兼容)

```sql
-- 员工表（记录员/理疗师）
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,              -- 真实姓名
    wechat_nickname VARCHAR(100),           -- 微信昵称（如"六亿（叶维忠）"）
    wechat_alias VARCHAR(100),              -- 微信备注名
    role VARCHAR(20) DEFAULT 'staff',       -- staff / manager / bot
    commission_rate DECIMAL(5,2) DEFAULT 0, -- 提成比例
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 顾客/会员表
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,              -- 顾客称呼（如"段老师"、"姚老师"）
    phone VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会员卡表
CREATE TABLE memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    card_type VARCHAR(50),                  -- 卡类型（如"理疗卡"）
    total_amount DECIMAL(10,2) NOT NULL,    -- 充值总额
    balance DECIMAL(10,2) NOT NULL,         -- 剩余余额
    remaining_sessions INTEGER,             -- 剩余次数（如有）
    opened_at DATE NOT NULL,               -- 开卡日期
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 服务类型字典表
CREATE TABLE service_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,       -- 如"头疗"、"理疗"、"泡脚"
    default_price DECIMAL(10,2),
    category VARCHAR(50)                    -- therapy / foot_bath / etc
);

-- 服务记录表（核心表）
CREATE TABLE service_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES customers(id),
    employee_id INTEGER REFERENCES employees(id),    -- 服务员工
    recorder_id INTEGER REFERENCES employees(id),    -- 记录人
    service_type_id INTEGER REFERENCES service_types(id),
    service_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,           -- 实际收费
    commission_amount DECIMAL(10,2) DEFAULT 0, -- 提成金额
    commission_to VARCHAR(50),               -- 提成给谁（如"李哥"）
    net_amount DECIMAL(10,2),                -- 净收入 = amount - commission
    membership_id INTEGER REFERENCES memberships(id), -- 如果从会员卡扣费
    notes TEXT,
    raw_message_id INTEGER REFERENCES raw_messages(id),
    parse_confidence DECIMAL(3,2),           -- LLM解析置信度 0-1
    confirmed BOOLEAN DEFAULT FALSE,         -- 是否人工确认
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,             -- 如"泡脚液"
    category VARCHAR(50),                    -- supplement / medicine / accessory
    unit_price DECIMAL(10,2),
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品销售记录
CREATE TABLE product_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    customer_id INTEGER REFERENCES customers(id),
    recorder_id INTEGER REFERENCES employees(id),
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(10,2) NOT NULL,
    sale_date DATE NOT NULL,
    notes TEXT,
    raw_message_id INTEGER REFERENCES raw_messages(id),
    parse_confidence DECIMAL(3,2),
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存变动记录
CREATE TABLE inventory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    change_type VARCHAR(20) NOT NULL,        -- sale / restock / adjustment
    quantity_change INTEGER NOT NULL,         -- 正数入库，负数出库
    quantity_after INTEGER NOT NULL,
    reference_id INTEGER,                    -- 关联 product_sales.id 或其他
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 原始消息存档（所有消息都保存）
CREATE TABLE raw_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wechat_msg_id VARCHAR(100) UNIQUE,      -- 微信消息ID（去重）
    sender_nickname VARCHAR(100) NOT NULL,
    sender_wechat_id VARCHAR(100),
    content TEXT NOT NULL,
    msg_type VARCHAR(20) DEFAULT 'text',     -- text / image / voice / ...
    group_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    is_at_bot BOOLEAN DEFAULT FALSE,         -- 是否@了机器人
    is_business BOOLEAN,                     -- 是否为业务消息（LLM判断）
    parse_status VARCHAR(20) DEFAULT 'pending', -- pending / parsed / failed / ignored
    parse_result JSON,                       -- LLM解析的JSON结果
    parse_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 修正记录（追踪修改历史）
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_record_type VARCHAR(50),        -- service_records / product_sales
    original_record_id INTEGER,
    correction_type VARCHAR(20),             -- date_change / amount_change / delete
    old_value JSON,
    new_value JSON,
    reason TEXT,
    raw_message_id INTEGER REFERENCES raw_messages(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日汇总快照
CREATE TABLE daily_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_date DATE NOT NULL UNIQUE,
    total_service_revenue DECIMAL(10,2),
    total_product_revenue DECIMAL(10,2),
    total_commissions DECIMAL(10,2),
    net_revenue DECIMAL(10,2),
    service_count INTEGER,
    product_sale_count INTEGER,
    new_members INTEGER,
    membership_revenue DECIMAL(10,2),
    summary_text TEXT,                       -- 发送到群里的文本
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. LLM 消息解析引擎（最核心模块）

### 4.1 解析策略

采用 **两阶段解析**：

**阶段一：规则预处理（无需LLM，降低成本）**

```python
import re
from datetime import datetime, date

class MessagePreProcessor:
    """规则引擎：处理明确模式，降低 LLM 调用量"""

    # 噪声过滤规则
    NOISE_PATTERNS = [
        r'^接$', r'^好$', r'^运$',           # 单字闲聊
        r'^\[.*表情\]',                       # 表情包
        r'^(好的|收到|谢谢|嗯|哦)',            # 简短回复
        r'停在|掉头|车子',                     # 停车相关
        r'@\S+\s*(好的|收到)',                 # @某人+简短确认
    ]

    # 日期提取（支持多种格式）
    DATE_PATTERNS = [
        # "1月26日" / "1月26号"
        (r'(\d{1,2})月(\d{1,2})[日号]', lambda m: f"{m.group(1)}/{m.group(2)}"),
        # "1.28" / "1.27"
        (r'(\d{1,2})\.(\d{1,2})', lambda m: f"{m.group(1)}/{m.group(2)}"),
        # "1/28" / "1|28" / "2|1"
        (r'(\d{1,2})[/|](\d{1,2})', lambda m: f"{m.group(1)}/{m.group(2)}"),
    ]

    # 已知服务类型
    SERVICE_KEYWORDS = ['头疗', '理疗', '泡脚', '按摩', '推拿', '刮痧', '拔罐']
    PRODUCT_KEYWORDS = ['泡脚液', '保健品', '药品', '膏药']
    MEMBERSHIP_KEYWORDS = ['开卡', '充值', '会员']

    def is_noise(self, content: str) -> bool:
        """判断是否为噪声消息"""
        content = content.strip()
        if len(content) <= 2 and not any(c.isdigit() for c in content):
            return True
        return any(re.search(p, content) for p in self.NOISE_PATTERNS)

    def extract_date(self, content: str, msg_timestamp: datetime) -> date | None:
        """从消息内容提取业务日期"""
        for pattern, formatter in self.DATE_PATTERNS:
            match = re.search(pattern, content)
            if match:
                date_str = formatter(match)
                month, day = map(int, date_str.split('/'))
                year = msg_timestamp.year
                return date(year, month, day)
        return None

    def classify_intent(self, content: str) -> str:
        """粗分类: service / product / membership / correction / unknown"""
        if any(kw in content for kw in self.MEMBERSHIP_KEYWORDS):
            return 'membership'
        if any(kw in content for kw in self.PRODUCT_KEYWORDS):
            return 'product'
        if '错误' in content or '改' in content or '更正' in content:
            return 'correction'
        if any(kw in content for kw in self.SERVICE_KEYWORDS):
            return 'service'
        if re.search(r'\d+元?', content) and re.search(r'.老师', content):
            return 'service'  # 有金额+老师 -> 大概率是服务记录
        return 'unknown'
```

**阶段二：LLM 结构化提取**

```python
# LLM Prompt 设计 — 这是系统的核心

SYSTEM_PROMPT = """你是一个健康理疗门店的数据录入助手。你的任务是从微信群聊消息中提取结构化业务数据。

## 门店业务类型
1. 理疗服务：员工为顾客做按摩/头疗/泡脚等，收取费用
2. 保健品销售：泡脚液等产品售卖
3. 会员卡：开卡充值
4. 修正指令：更正之前的错误记录

## 已知人员
- 顾客常以"X老师"称呼：段老师、姚老师、周老师、郑老师等
- 员工/记录员：通过微信昵称识别
- 提成人员：如"李哥"

## 消息格式特征
- 日期格式多样：1.28、1/28、1|28、1月28日 均表示1月28日
- 金额可能在服务前或后：头疗30 = 30头疗 = 头疗30元
- 可能一条消息包含多笔记录，用换行分隔
- "开卡1000" = 会员充值1000元
- "198-20李哥178" = 总价198，李哥提成20，实收178

## 输出要求
对每条消息，返回 JSON 数组（可能包含多笔记录）。每笔记录格式：

```json
{
  "type": "service" | "product_sale" | "membership" | "correction" | "noise",
  "date": "YYYY-MM-DD",
  "customer_name": "段老师",
  "service_or_product": "头疗",
  "amount": 30,
  "commission": null,
  "commission_to": null,
  "net_amount": 30,
  "notes": "",
  "confidence": 0.95,
  "correction_detail": null
}
```

如果是修正指令，`correction_detail` 格式为：
```json
{
  "action": "change_date" | "change_amount" | "delete",
  "original_date": "原日期",
  "new_date": "新日期",
  "description": "26-27号错误，改25-26"
}
```

如果无法识别或是闲聊/噪声，返回 `[{"type": "noise"}]`。

## 关键规则
1. 宁可返回 confidence 低值，也不要编造数据
2. 如果金额不确定，标注 confidence < 0.7
3. 一条消息可能包含多笔交易，全部提取
4. "体验" 通常意味着折扣价/试做价
"""

USER_PROMPT_TEMPLATE = """
消息发送者: {sender_nickname}
消息时间: {timestamp}
消息内容:
{content}

请提取结构化数据。
"""
```

### 4.2 LLM 调用封装（支持 OpenAI + Claude 切换）

```python
from abc import ABC, abstractmethod
from openai import OpenAI
from anthropic import Anthropic
import json

class LLMParser(ABC):
    @abstractmethod
    async def parse_message(self, sender: str, timestamp: str, content: str) -> list[dict]:
        pass

class OpenAIParser(LLMParser):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def parse_message(self, sender, timestamp, content) -> list[dict]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    sender_nickname=sender, timestamp=timestamp, content=content
                )}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # 低温度保证一致性
        )
        return json.loads(response.choices[0].message.content)

class ClaudeParser(LLMParser):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def parse_message(self, sender, timestamp, content) -> list[dict]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    sender_nickname=sender, timestamp=timestamp, content=content
                )}
            ],
        )
        # Claude 返回的文本可能包含 markdown code block
        text = response.content[0].text
        text = text.strip('`').removeprefix('json').strip()
        return json.loads(text)

class LLMParserWithFallback:
    """带有 fallback 的解析器"""
    def __init__(self, primary: LLMParser, fallback: LLMParser):
        self.primary = primary
        self.fallback = fallback

    async def parse_message(self, sender, timestamp, content) -> list[dict]:
        try:
            return await self.primary.parse_message(sender, timestamp, content)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}, falling back")
            return await self.fallback.parse_message(sender, timestamp, content)
```

### 4.3 解析流水线

```python
class MessagePipeline:
    """
    完整的消息处理流水线:
    原始消息 → 噪声过滤 → 预处理 → LLM解析 → 置信度检查 → 入库 → (可选)确认请求
    """

    def __init__(self, preprocessor, llm_parser, db_service):
        self.preprocessor = preprocessor
        self.llm_parser = llm_parser
        self.db = db_service
        self.CONFIDENCE_THRESHOLD = 0.7  # 低于此值需人工确认

    async def process(self, raw_msg: dict) -> ProcessResult:
        # 1. 存储原始消息
        msg_id = await self.db.save_raw_message(raw_msg)

        # 2. 噪声过滤
        if self.preprocessor.is_noise(raw_msg['content']):
            await self.db.update_parse_status(msg_id, 'ignored')
            return ProcessResult(status='ignored')

        # 3. 粗分类
        intent = self.preprocessor.classify_intent(raw_msg['content'])
        if intent == 'unknown':
            # 仍然发给 LLM，但记录为 uncertain
            pass

        # 4. LLM 结构化提取
        try:
            records = await self.llm_parser.parse_message(
                sender=raw_msg['sender_nickname'],
                timestamp=raw_msg['timestamp'],
                content=raw_msg['content']
            )
        except Exception as e:
            await self.db.update_parse_status(msg_id, 'failed', error=str(e))
            return ProcessResult(status='failed', error=str(e))

        # 5. 处理每条解析结果
        results = []
        for record in records:
            if record.get('type') == 'noise':
                await self.db.update_parse_status(msg_id, 'ignored')
                continue

            # 6. 置信度检查
            confidence = record.get('confidence', 0.5)
            needs_confirmation = confidence < self.CONFIDENCE_THRESHOLD

            # 7. 入库
            db_record_id = await self.db.save_business_record(
                record_type=record['type'],
                data=record,
                raw_message_id=msg_id,
                confirmed=not needs_confirmation
            )

            results.append({
                'record_id': db_record_id,
                'type': record['type'],
                'needs_confirmation': needs_confirmation,
                'confidence': confidence,
                'data': record
            })

        await self.db.update_parse_status(msg_id, 'parsed', result=records)
        return ProcessResult(status='parsed', records=results)
```

---

## 5. 命令系统（@机器人 交互）

### 5.1 命令定义

```python
# 命令注册表
COMMANDS = {
    # ---- 查询类 ----
    "今日总结":     {"handler": "daily_summary",      "args": 0, "desc": "生成今日经营数据汇总"},
    "库存总结":     {"handler": "inventory_summary",   "args": 0, "desc": "显示当前库存情况"},
    "会员总结":     {"handler": "membership_summary",  "args": 0, "desc": "显示会员充值/余额汇总"},
    "本月总结":     {"handler": "monthly_summary",     "args": 0, "desc": "生成本月经营报表"},
    "查询":        {"handler": "query_records",       "args": "*", "desc": "查询XX老师/查询1月28日"},

    # ---- 操作类 ----
    "确认":        {"handler": "confirm_records",     "args": 0, "desc": "确认今日所有待确认记录"},
    "撤销":        {"handler": "undo_last",           "args": "?", "desc": "撤销上一条/撤销指定记录"},
    "修改":        {"handler": "modify_record",       "args": "*", "desc": "修改 #记录ID 金额为XX"},

    # ---- 库存管理 ----
    "入库":        {"handler": "restock",             "args": "*", "desc": "入库 泡脚液 100瓶"},
    "库存调整":     {"handler": "adjust_inventory",    "args": "*", "desc": "手动调整库存"},

    # ---- 帮助 ----
    "帮助":        {"handler": "show_help",           "args": 0, "desc": "显示所有可用命令"},
}
```

### 5.2 命令处理示例

```python
class CommandHandler:
    async def daily_summary(self, group_id: str, args: list) -> str:
        """生成今日汇总"""
        today = date.today()
        records = await self.db.get_records_by_date(today)

        service_records = [r for r in records if r['type'] == 'service']
        product_records = [r for r in records if r['type'] == 'product_sale']
        membership_records = [r for r in records if r['type'] == 'membership']

        total_service = sum(r['net_amount'] or r['amount'] for r in service_records)
        total_product = sum(r['total_amount'] for r in product_records)
        total_membership = sum(r['total_amount'] for r in membership_records)
        total_commission = sum(r.get('commission', 0) or 0 for r in service_records)
        unconfirmed = sum(1 for r in records if not r['confirmed'])

        summary = f"""📊 {today.strftime('%Y年%m月%d日')} 经营日报

💆 理疗服务: {len(service_records)}笔, 收入 ¥{total_service:.0f}
🛒 产品销售: {len(product_records)}笔, 收入 ¥{total_product:.0f}
💳 会员充值: {len(membership_records)}笔, 金额 ¥{total_membership:.0f}
💰 提成支出: ¥{total_commission:.0f}
━━━━━━━━━━━━━
📈 今日净收入: ¥{total_service + total_product - total_commission:.0f}

服务明细:
"""
        for r in service_records:
            confirm_mark = "✅" if r['confirmed'] else "⏳"
            summary += f"  {confirm_mark} {r['customer_name']} {r['service_type']} ¥{r['amount']:.0f}"
            if r.get('commission'):
                summary += f" (提成¥{r['commission']:.0f}→{r['commission_to']})"
            summary += "\n"

        if unconfirmed > 0:
            summary += f"\n⚠️ {unconfirmed}条记录待确认，请回复 @机器人 确认"

        return summary
```

---

## 6. 微信桥接层

### 6.1 WeChatFerry 集成方案

```python
"""
WeChatFerry 是目前最稳定的个人微信 Hook 方案。
注意事项:
1. 需要 Windows 环境运行（微信PC客户端）
2. 需要特定版本的微信客户端（WeChatFerry 文档指定版本）
3. 建议用虚拟机/VPS 运行，保持微信在线
"""

from wcferry import Wcf, WxMsg
import threading

class WeChatBot:
    def __init__(self, pipeline: MessagePipeline, command_handler: CommandHandler):
        self.wcf = Wcf()
        self.pipeline = pipeline
        self.command_handler = command_handler
        self.bot_wxid = None
        self.target_group_ids = set()  # 监听的群ID

    def start(self):
        self.bot_wxid = self.wcf.get_self_wxid()
        # 注册消息回调
        self.wcf.enable_receiving_msg()
        threading.Thread(target=self._message_loop, daemon=True).start()

    def _message_loop(self):
        while self.wcf.is_receiving_msg():
            try:
                msg: WxMsg = self.wcf.get_msg()
                if msg.from_group() and msg.roomid in self.target_group_ids:
                    asyncio.run(self._handle_group_message(msg))
            except Exception as e:
                logger.error(f"Message loop error: {e}")

    async def _handle_group_message(self, msg: WxMsg):
        # 构造统一消息格式
        raw_msg = {
            'wechat_msg_id': msg.id,
            'sender_nickname': self.wcf.get_alias_in_chatroom(msg.roomid, msg.sender) or msg.sender,
            'sender_wechat_id': msg.sender,
            'content': msg.content,
            'msg_type': 'text' if msg.type == 1 else 'other',
            'group_id': msg.roomid,
            'timestamp': datetime.fromtimestamp(msg.ts),
            'is_at_bot': self.bot_wxid in msg.content or f'@{self.bot_name}' in msg.content,
        }

        if raw_msg['is_at_bot']:
            # @机器人 -> 处理命令
            response = await self._handle_command(raw_msg)
            if response:
                self.wcf.send_text(response, msg.roomid)
        else:
            # 被动监听 -> 解析业务消息
            await self.pipeline.process(raw_msg)

    async def _handle_command(self, raw_msg: dict) -> str:
        """解析 @机器人 后面的命令"""
        content = raw_msg['content']
        # 去掉 @机器人 部分
        content = re.sub(r'@\S+\s*', '', content).strip()

        for keyword, cmd_config in COMMANDS.items():
            if content.startswith(keyword):
                args = content[len(keyword):].strip().split()
                handler = getattr(self.command_handler, cmd_config['handler'])
                return await handler(raw_msg['group_id'], args)

        return "❓ 未识别的命令，回复 @机器人 帮助 查看可用指令"
```

### 6.2 备选方案对比

| 方案 | 优势 | 劣势 | 推荐度 |
|------|------|------|--------|
| **WeChatFerry** | 开源、功能全、社区活跃 | 需 Windows + 特定微信版本 | ⭐⭐⭐⭐⭐ |
| **itchat (UOS)** | Python原生、简单 | 2024年后频繁掉线，封号风险高 | ⭐⭐ |
| **企业微信 API** | 官方支持、稳定、不封号 | 需企业认证，群管理方式不同 | ⭐⭐⭐⭐（如果可获得） |
| **ComWeChatRobot** | 功能全面 | 维护不活跃 | ⭐⭐⭐ |
| **OpenIMServer** | 自建IM，完全可控 | 需迁移用户到新平台，不现实 | ⭐ |

**强烈建议**：如果门店有营业执照，优先申请**企业微信**，使用官方 API 是最稳定可靠的方案。

---

## 7. 关键注意事项

### 7.1 消息解析的边界案例处理

```python
"""
根据实际群聊记录分析出的边界案例，LLM Prompt 和代码必须处理：
"""

EDGE_CASES = {
    # 1. 日期修正
    "26-27号错误，改25-26": {
        "action": "change_date",
        "description": "将原来标记为26-27的记录改为25-26日期"
    },

    # 2. 提成扣除
    "1.28姚老师理疗198-20李哥178": {
        "amount": 198,
        "commission": 20,
        "commission_to": "李哥",
        "net_amount": 178
    },

    # 3. 复合消息 (一条多笔)
    "2.3段老师490\n姚老师490理疗合计980": {
        "records": [
            {"customer": "段老师", "amount": 490},
            {"customer": "姚老师", "amount": 490},
        ],
        "note": "合计980是校验用"
    },

    # 4. 日期和金额位置互换
    "26段老师头疗30":     {"date_prefix": True, "amount_suffix": True},
    "26段老师30头疗":     {"date_prefix": True, "amount_before_service": True},

    # 5. 开卡/充值
    "1.28理疗开卡1000姚老师": {
        "type": "membership",
        "card_type": "理疗卡",
        "amount": 1000,
        "customer": "姚老师"
    },

    # 6. 打包服务
    "26段老师泡脚一个月100送一提泡脚液": {
        "records": [
            {"type": "service", "service": "泡脚", "amount": 100, "duration": "一个月"},
            {"type": "product_sale", "product": "泡脚液", "amount": 0, "note": "赠送"},
        ]
    },

    # 7. 重复消息 (发送者发了两遍)
    "1.28段老师30头疗\n1.28段老师30头疗": {
        "note": "可能是重复发送，需要去重。但也可能是两次消费，LLM需根据上下文判断"
    },

    # 8. 后续补充 (追加提成说明)
    "減去20李哥提成178": {
        "note": "这是对前一条记录的补充说明，需要回溯更新"
    },
}
```

### 7.2 成本控制策略

```python
"""
LLM API 成本优化方案：
"""

COST_OPTIMIZATION = {
    "1_noise_filter_first": {
        "desc": "先用规则过滤噪声，只有疑似业务消息才调用 LLM",
        "saving": "~60% 消息无需 LLM"
    },

    "2_use_mini_model": {
        "desc": "日常解析用 gpt-4o-mini ($0.15/1M input)，复杂/低置信度用 gpt-4o ($2.5/1M)",
        "estimate": "门店日均~30条业务消息，每条~200 tokens → 日成本约 $0.01"
    },

    "3_batch_processing": {
        "desc": "将5分钟内的消息打包为一个请求，减少请求数",
        "saving": "减少 API 调用次数 ~50%"
    },

    "4_cache_similar_patterns": {
        "desc": "缓存已解析的相似模式，如'X老师头疗30'可直接模板匹配",
        "saving": "重复模式无需 LLM"
    },

    "5_monthly_estimate": {
        "desc": "按每天30条业务消息，每条200 tokens 计算",
        "gpt4o_mini": "$0.01/天 ≈ $0.30/月",
        "gpt4o": "$0.15/天 ≈ $4.50/月",
        "claude_sonnet": "约 $0.10/天 ≈ $3.00/月"
    }
}
```

### 7.3 数据一致性保障

```python
"""
关键的数据一致性机制：
"""

DATA_INTEGRITY = {
    "1_idempotency": {
        "desc": "微信消息ID去重，防止同一消息重复处理",
        "impl": "raw_messages.wechat_msg_id UNIQUE 约束"
    },

    "2_confirmation_workflow": {
        "desc": "LLM 解析结果默认为'待确认'，人工确认后才标记为'已确认'",
        "impl": "service_records.confirmed + confirmed_at"
    },

    "3_audit_trail": {
        "desc": "所有修改都有原始消息关联，可追溯",
        "impl": "raw_message_id FK + corrections 表"
    },

    "4_daily_reconciliation": {
        "desc": "每日汇总时对比 LLM 解析金额 vs 手工核算",
        "impl": "daily_summaries 快照 + 人工确认"
    },

    "5_soft_delete": {
        "desc": "记录只做逻辑删除，不物理删除",
        "impl": "is_active / deleted_at 字段"
    }
}
```

### 7.4 安全与合规

```python
SECURITY_CONSIDERATIONS = {
    "1_api_key_management": {
        "desc": "OpenAI/Claude API Key 通过环境变量或 Vault 管理",
        "impl": "python-dotenv / docker secrets"
    },

    "2_wechat_account_risk": {
        "desc": "Hook方式有封号风险，建议使用专用微信号",
        "mitigation": [
            "使用微信小号作为机器人",
            "控制发送频率，不要频繁群发",
            "企业微信方案零封号风险"
        ]
    },

    "3_data_privacy": {
        "desc": "群聊消息包含个人信息（姓名、消费记录）",
        "mitigation": [
            "数据库加密存储敏感字段",
            "LLM 调用时可匿名化处理（但本场景名字是关键信息）",
            "确保只有授权人可访问后台数据"
        ]
    },

    "4_llm_hallucination": {
        "desc": "LLM 可能产生幻觉，编造不存在的记录",
        "mitigation": [
            "低温度 (temperature=0.1)",
            "要求返回 confidence 分数",
            "低于阈值的记录标记为待确认",
            "每日汇总时人工复核"
        ]
    }
}
```

---

## 8. 项目文件结构

```
wechat-store-bot/
├── README.md
├── docker-compose.yml              # Docker 部署配置
├── Dockerfile
├── .env.example                    # 环境变量模板
├── requirements.txt
│
├── config/
│   ├── settings.py                 # 全局配置
│   ├── known_entities.py           # 已知顾客、员工、服务类型
│   └── prompts.py                  # LLM Prompt 定义
│
├── core/
│   ├── __init__.py
│   ├── bot.py                      # WeChatBot 主类
│   ├── message_router.py           # 消息路由（@指令 vs 被动监听）
│   ├── command_handler.py          # 命令处理器
│   └── scheduler.py                # 定时任务（每日汇总）
│
├── parsing/
│   ├── __init__.py
│   ├── preprocessor.py             # 规则预处理器
│   ├── llm_parser.py               # LLM 解析引擎（OpenAI/Claude）
│   ├── pipeline.py                 # 完整解析流水线
│   └── entity_resolver.py          # 实体消歧（"段老师"→ customer_id）
│
├── services/
│   ├── __init__.py
│   ├── service_record_svc.py       # 理疗服务业务逻辑
│   ├── product_sale_svc.py         # 产品销售业务逻辑
│   ├── inventory_svc.py            # 库存管理
│   ├── membership_svc.py           # 会员管理
│   └── summary_svc.py             # 汇总报表
│
├── db/
│   ├── __init__.py
│   ├── models.py                   # SQLAlchemy ORM 模型
│   ├── migrations/                 # Alembic 迁移
│   └── repository.py              # 数据访问层
│
├── tests/
│   ├── test_preprocessor.py
│   ├── test_llm_parser.py          # Mock LLM 的单元测试
│   ├── test_pipeline.py
│   ├── test_commands.py
│   └── fixtures/
│       └── sample_messages.json    # 真实消息样本（脱敏）
│
└── scripts/
    ├── init_db.py                  # 初始化数据库 + 种子数据
    ├── import_history.py           # 导入历史消息（如上面的聊天记录）
    └── backfill_parse.py           # 对历史消息批量解析
```

---

## 9. 部署方案

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 注意：微信 Hook 需要 Windows 环境
  # 方案A：Windows 主机运行微信 + WeChatFerry，通过 RPC 连接到 Linux 容器中的 Bot
  # 方案B：全部在 Windows 上运行（推荐初期方案）

  bot:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=sqlite:///data/store.db  # 初期用 SQLite
      - REDIS_URL=redis://redis:6379/0
      - BOT_NAME=小助手
      - TARGET_GROUP_NAME=门店经营群
      - PRIMARY_LLM=openai  # openai / anthropic
      - DAILY_SUMMARY_TIME=21:00
      - CONFIDENCE_THRESHOLD=0.7
    volumes:
      - ./data:/app/data  # 数据持久化
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

## 10. 开发优先级路线图

| 阶段 | 内容 | 时间估算 |
|------|------|---------|
| **P0 - MVP** | 消息监听 + LLM解析 + 服务记录入库 + 今日总结命令 | 1-2 周 |
| **P1 - 核心功能** | 全部命令系统 + 会员管理 + 产品销售 + 每日自动汇总 | 1-2 周 |
| **P2 - 稳健性** | 修正指令处理 + 去重 + 置信度过滤 + 人工确认流程 | 1 周 |
| **P3 - 运营工具** | 月度报表 + 库存预警 + 会员到期提醒 + 导出 Excel | 1 周 |
| **P4 - 可选增强** | Web 管理后台 + 数据可视化 + 迁移到 PostgreSQL | 按需 |

---

## 11. 给 AI 编码的关键提示

> **编写代码时务必注意以下要点：**

1. **中文 NLP 的坑**：日期中的 `|`（竖线）是用户输入习惯，不是正则特殊字符但需要 escape；中文数字和阿拉伯数字混用
2. **消息顺序**：微信消息时间戳可能因网络延迟乱序，用消息内容中的日期而非发送时间
3. **"老师"是称呼**：群内 "段老师"、"姚老师"不是真正的老师，是顾客的尊称
4. **LLM 返回格式**：务必做 JSON parse 的异常处理，LLM 有时会返回非法 JSON
5. **微信消息编码**：微信表情包是 `[xx]` 格式，需要过滤；@消息格式各版本不同
6. **竖线日期分隔符**：`2|1` `2|3` 是 `2/1` `2/3` 的输入法问题，必须支持
7. **重复消息检测**：同一发送者短时间内发送相同内容，大概率是重复操作而非两笔交易
8. **"体验"价**：包含"体验"的消息通常是折扣价/首次体验价
9. **会员卡抵扣**：开卡后的消费可能从卡内余额扣除，需要更新 membership.balance
10. **提成是从门店收入中扣**：`198-20李哥178` 意思是门店收了198，给李哥提成20，门店净收入178