# We-Business-Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 微信群托管机器人 — 健康理疗门店商业信息管理系统

## 📖 项目简介

We-Business-Manager 是一个基于 LLM（大语言模型）的智能微信群消息解析系统，专为健康理疗门店、健身房、美发店等服务业态设计。系统能够：

- 🤖 **智能消息解析**：被动监听群消息，自动解析业务相关的自然语言记录
- 💬 **交互式查询**：响应 @机器人 指令，执行查询、汇总等操作
- 📊 **数据结构化**：将非结构化的中文聊天消息转为结构化业务数据
- 📈 **自动汇总报告**：每日自动生成经营汇总报告
- 🔌 **可扩展架构**：支持多种业态的业务逻辑适配
- 🧠 **Agent 功能**：支持函数调用，让 AI Agent 直接操作数据库

## ✨ 主要特性

- **多 LLM 支持**：支持 OpenAI、Anthropic Claude、Minimax 等多种 LLM 提供商
- **灵活的数据模型**：支持服务记录、商品销售、会员管理等多种业务实体
- **插件化设计**：通过插件系统支持不同业态的扩展需求
- **企业微信集成**：支持企业微信回调接口，无需本地微信客户端
- **完善的测试**：包含完整的单元测试和集成测试
- **详细的文档**：提供快速开始指南、API 文档和示例代码

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

## 📁 项目结构

```
We-Bussiness-Manager/
├── agent/              # AI Agent 模块（函数调用、发现、执行）
├── business/           # 业务逻辑适配器
├── config/             # 配置文件
├── core/               # 核心模块（调度器、业务适配器）
├── database/           # 数据库模块（模型、仓库、CRUD）
├── examples/           # 示例代码
│   ├── agent/          # Agent 使用示例
│   ├── database/       # 数据库使用示例
│   └── wechat/         # 微信集成示例
├── interface/          # 接口层（微信、Web API）
├── parsing/            # 消息解析模块（LLM 解析器、流水线）
├── scripts/            # 工具脚本
├── tests/              # 测试文件
└── design/             # 设计文档
```

## ⚠️ 注意事项

1. **API 密钥安全**：
   - ⚠️ **重要**：永远不要将真实的 API Key 硬编码在代码中
   - 所有 API Key 必须通过环境变量或 `.env` 文件提供
   - 不要将包含真实密钥的 `.env` 文件提交到版本控制系统
   - 确保 `.gitignore` 中包含 `.env` 和 `config.ini`
   - 如果密钥已泄露，请立即在服务提供商处撤销并重新生成
2. **API 成本**：系统使用 LLM 解析消息，建议先配置成本控制策略
3. **数据安全**：群聊消息包含个人信息，请妥善保管数据库和 `.env` 文件
4. **企业微信**：推荐使用企业微信回调接口，无需本地微信客户端

## 📚 文档

- **[快速开始指南](examples/database/QUICKSTART.md)** - 数据库模块快速入门
- **[贡献指南](CONTRIBUTING.md)** - 如何为项目做贡献
- **[Agent 文档](agent/README.md)** - AI Agent 功能说明
- **[数据库文档](examples/database/README.md)** - 数据库模块详细文档
- **[企业微信集成指南](interface/wechat/SETUP_GUIDE.md)** - 企业微信配置说明

## 🤝 贡献

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目。

贡献方式：
- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

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

