# 测试指南 - 逐步验证各模块功能

本文档将指导你如何逐步运行和验证每个模块的测试，确保所有功能正常工作，并最终完成集成测试。

## 📋 目录

1. [环境准备](#环境准备)
2. [测试执行顺序](#测试执行顺序)
3. [各模块详细测试](#各模块详细测试)
4. [人工验证检查点](#人工验证检查点)
5. [集成测试](#集成测试)
6. [问题排查](#问题排查)

---

## 🔧 环境准备

### 1. 激活 Conda 环境

```bash
# 方式1：使用脚本（推荐）
source activate_env.sh

# 方式2：手动激活
export PATH="$HOME/miniconda3/bin:$PATH"
eval "$(conda shell.bash hook)"
conda activate wechat-business-manager
```

### 2. 验证环境

```bash
# 检查 Python 版本（应该是 3.11.14）
python --version

# 检查 pytest（应该是 9.0.2）
pytest --version

# 检查关键依赖
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import pytest; print('Pytest OK')"
```

### 3. 进入项目目录

```bash
cd /home/yeshougan/project/We-Bussiness-Manager
```

---

## 📊 测试执行顺序

建议按照以下顺序逐步测试，从底层模块到上层模块：

```
1. 消息预处理器 (parsing/preprocessor.py)
   ↓
2. LLM 解析器 (parsing/llm_parser.py)
   ↓
3. 数据库访问层 (db/repository.py)
   ↓
4. 消息处理流水线 (parsing/pipeline.py)
   ↓
5. 汇总服务 (services/summary_svc.py)
   ↓
6. 命令处理器 (core/command_handler.py)
   ↓
7. 集成测试
```

---

## 🧪 各模块详细测试

### 步骤 1: 测试消息预处理器

**模块**: `parsing/preprocessor.py`  
**测试文件**: `tests/test_preprocessor.py`  
**功能**: 消息噪声过滤、日期提取、意图分类、金额提取

#### 运行测试

```bash
# 方式1：使用脚本
./tests/run_module_tests.sh preprocessor

# 方式2：直接使用 pytest
pytest tests/test_preprocessor.py -v
```

#### 预期结果

```
tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise PASSED
tests/test_preprocessor.py::TestMessagePreProcessor::test_extract_date PASSED
tests/test_preprocessor.py::TestMessagePreProcessor::test_classify_intent PASSED
tests/test_preprocessor.py::TestMessagePreProcessor::test_extract_amount PASSED

======================== 4 passed in X.XXs ========================
```

#### 人工验证检查点

✅ **检查点 1.1**: 噪声过滤
- [ ] 单字消息（"接"、"好"）被识别为噪声
- [ ] 简短回复（"好的"、"收到"）被识别为噪声
- [ ] 业务消息（"1.28段老师头疗30"）不被识别为噪声

✅ **检查点 1.2**: 日期提取
- [ ] 能提取 "1.28" 格式的日期
- [ ] 能提取 "1/28" 格式的日期
- [ ] 能提取 "1|28" 格式的日期（竖线分隔）
- [ ] 能提取 "1月28日" 格式的日期

✅ **检查点 1.3**: 意图分类
- [ ] "头疗30" 被分类为 service
- [ ] "开卡1000" 被分类为 membership
- [ ] "泡脚液100" 被分类为 product
- [ ] "26-27号错误" 被分类为 correction

✅ **检查点 1.4**: 金额提取
- [ ] 能从 "头疗30" 中提取 30
- [ ] 能从 "30头疗" 中提取 30
- [ ] 能从 "头疗30元" 中提取 30

**如果所有检查点通过，继续下一步。**

---

### 步骤 2: 测试 LLM 解析器

**模块**: `parsing/llm_parser.py`  
**测试文件**: `tests/test_llm_parser.py`  
**功能**: OpenAI/Claude 解析器、Fallback 机制

#### 运行测试

```bash
# 方式1：使用脚本
./tests/run_module_tests.sh llm_parser

# 方式2：直接使用 pytest
pytest tests/test_llm_parser.py -v -s
```

#### 预期结果

```
tests/test_llm_parser.py::TestOpenAIParser::test_parse_service_message PASSED
tests/test_llm_parser.py::TestOpenAIParser::test_parse_multiple_records PASSED
tests/test_llm_parser.py::TestOpenAIParser::test_parse_noise PASSED
tests/test_llm_parser.py::TestClaudeParser::test_parse_service_message PASSED
tests/test_llm_parser.py::TestLLMParserWithFallback::test_primary_success PASSED
tests/test_llm_parser.py::TestLLMParserWithFallback::test_primary_fail_fallback_success PASSED

======================== 6 passed in X.XXs ========================
```

#### 人工验证检查点

✅ **检查点 2.1**: OpenAI 解析器
- [ ] 能解析服务消息并返回正确格式
- [ ] 能解析多条记录（一条消息包含多笔交易）
- [ ] 能识别噪声消息

✅ **检查点 2.2**: Claude 解析器
- [ ] 能解析服务消息并返回正确格式

✅ **检查点 2.3**: Fallback 机制
- [ ] 主解析器成功时，不使用备用解析器
- [ ] 主解析器失败时，自动切换到备用解析器

**注意**: 这些测试使用 Mock，不需要真实的 API Key。

**如果所有检查点通过，继续下一步。**

---

### 步骤 3: 测试数据库访问层

**模块**: `db/repository.py`  
**测试文件**: `tests/test_repository.py`  
**功能**: 数据库 CRUD 操作、实体管理

#### 运行测试

```bash
# 方式1：使用脚本
./tests/run_module_tests.sh repository

# 方式2：直接使用 pytest
pytest tests/test_repository.py -v
```

#### 预期结果

```
tests/test_repository.py::TestDatabaseRepository::test_save_raw_message PASSED
tests/test_repository.py::TestDatabaseRepository::test_get_or_create_customer PASSED
tests/test_repository.py::TestDatabaseRepository::test_get_or_create_employee PASSED
tests/test_repository.py::TestDatabaseRepository::test_get_or_create_service_type PASSED
tests/test_repository.py::TestDatabaseRepository::test_save_service_record PASSED
tests/test_repository.py::TestDatabaseRepository::test_save_service_record_with_commission PASSED
tests/test_repository.py::TestDatabaseRepository::test_get_records_by_date PASSED
tests/test_repository.py::TestDatabaseRepository::test_save_product_sale PASSED
tests/test_repository.py::TestDatabaseRepository::test_save_membership PASSED
tests/test_repository.py::TestDatabaseRepository::test_update_parse_status PASSED

======================== 10 passed in X.XXs ========================
```

#### 人工验证检查点

✅ **检查点 3.1**: 原始消息保存
- [ ] 能保存原始消息
- [ ] 相同消息ID不会重复保存（去重）

✅ **检查点 3.2**: 实体创建
- [ ] 能创建顾客（如果不存在）
- [ ] 能创建员工（如果不存在）
- [ ] 能创建服务类型（如果不存在）
- [ ] 已存在的实体不会重复创建

✅ **检查点 3.3**: 服务记录保存
- [ ] 能保存基本服务记录
- [ ] 能保存带提成的服务记录
- [ ] 日期格式正确转换

✅ **检查点 3.4**: 数据查询
- [ ] 能按日期查询记录
- [ ] 查询结果格式正确

✅ **检查点 3.5**: 其他记录类型
- [ ] 能保存商品销售记录
- [ ] 能保存会员卡记录
- [ ] 能更新解析状态

**如果所有检查点通过，继续下一步。**

---

### 步骤 4: 测试消息处理流水线

**模块**: `parsing/pipeline.py`  
**测试文件**: `tests/test_pipeline.py`  
**功能**: 完整的消息处理流程

#### 运行测试

```bash
# 方式1：使用脚本
./tests/run_module_tests.sh pipeline

# 方式2：直接使用 pytest
pytest tests/test_pipeline.py -v -s
```

#### 预期结果

```
tests/test_pipeline.py::TestMessagePipeline::test_process_noise_message PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_service_message PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_low_confidence PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_multiple_records PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_llm_failure PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_membership_message PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_product_sale PASSED
tests/test_pipeline.py::TestMessagePipeline::test_process_invalid_record PASSED

======================== 8 passed in X.XXs ========================
```

#### 人工验证检查点

✅ **检查点 4.1**: 噪声消息处理
- [ ] 噪声消息被正确过滤，不进行 LLM 解析
- [ ] 状态标记为 'ignored'

✅ **检查点 4.2**: 服务消息处理
- [ ] 消息被正确解析
- [ ] 记录被保存到数据库
- [ ] 返回正确的处理结果

✅ **检查点 4.3**: 低置信度处理
- [ ] 低置信度记录被标记为需要确认
- [ ] `needs_confirmation` 为 True

✅ **检查点 4.4**: 多条记录处理
- [ ] 一条消息中的多条记录都被处理
- [ ] 每条记录都正确保存

✅ **检查点 4.5**: 错误处理
- [ ] LLM 失败时，错误被正确捕获
- [ ] 状态标记为 'failed'
- [ ] 错误信息被记录

✅ **检查点 4.6**: 其他消息类型
- [ ] 会员消息被正确处理
- [ ] 商品销售消息被正确处理
- [ ] 无效记录被过滤

**如果所有检查点通过，继续下一步。**

---

### 步骤 5: 测试汇总服务

**模块**: `services/summary_svc.py`  
**测试文件**: `tests/test_summary_svc.py`  
**功能**: 每日/月度汇总报表生成

#### 运行测试

```bash
# 方式1：使用脚本
./tests/run_module_tests.sh summary

# 方式2：直接使用 pytest
pytest tests/test_summary_svc.py -v
```

#### 预期结果

```
tests/test_summary_svc.py::TestSummaryService::test_generate_daily_summary_empty PASSED
tests/test_summary_svc.py::TestSummaryService::test_generate_daily_summary_with_service PASSED
tests/test_summary_svc.py::TestSummaryService::test_generate_daily_summary_with_commission PASSED
tests/test_summary_svc.py::TestSummaryService::test_generate_daily_summary_with_product PASSED
tests/test_summary_svc.py::TestSummaryService::test_generate_daily_summary_unconfirmed PASSED
tests/test_summary_svc.py::TestSummaryService::test_generate_monthly_summary PASSED

======================== 6 passed in X.XXs ========================
```

#### 人工验证检查点

✅ **检查点 5.1**: 空数据汇总
- [ ] 空数据时生成正确的汇总格式
- [ ] 显示 0 笔记录

✅ **检查点 5.2**: 服务记录汇总
- [ ] 正确统计服务记录数量
- [ ] 正确计算总收入
- [ ] 正确显示顾客和服务类型

✅ **检查点 5.3**: 带提成汇总
- [ ] 正确显示提成金额
- [ ] 正确显示提成对象
- [ ] 正确计算净收入

✅ **检查点 5.4**: 商品销售汇总
- [ ] 正确统计商品销售
- [ ] 正确显示商品名称和数量

✅ **检查点 5.5**: 待确认记录
- [ ] 正确显示待确认记录数量
- [ ] 提示信息清晰

✅ **检查点 5.6**: 月度汇总
- [ ] 正确统计月度数据
- [ ] 格式正确

**如果所有检查点通过，继续下一步。**

---

### 步骤 6: 测试命令处理器

**模块**: `core/command_handler.py`  
**测试文件**: `tests/test_command_handler.py`  
**功能**: @机器人 命令处理

#### 运行测试

```bash
# 方式1：使用脚本
./tests/run_module_tests.sh command

# 方式2：直接使用 pytest
pytest tests/test_command_handler.py -v
```

#### 预期结果

```
tests/test_command_handler.py::TestCommandHandler::test_daily_summary_empty PASSED
tests/test_command_handler.py::TestCommandHandler::test_daily_summary_with_data PASSED
tests/test_command_handler.py::TestCommandHandler::test_inventory_summary PASSED
tests/test_command_handler.py::TestCommandHandler::test_membership_summary PASSED
tests/test_command_handler.py::TestCommandHandler::test_monthly_summary PASSED
tests/test_command_handler.py::TestCommandHandler::test_query_records_by_date PASSED
tests/test_command_handler.py::TestCommandHandler::test_query_records_no_args PASSED
tests/test_command_handler.py::TestCommandHandler::test_show_help PASSED
tests/test_command_handler.py::TestCommandHandler::test_restock PASSED
tests/test_command_handler.py::TestCommandHandler::test_restock_invalid PASSED

======================== 10 passed in X.XXs ========================
```

#### 人工验证检查点

✅ **检查点 6.1**: 每日汇总命令
- [ ] 空数据时返回正确格式
- [ ] 有数据时正确汇总
- [ ] 包含所有必要信息

✅ **检查点 6.2**: 查询命令
- [ ] 按日期查询正确
- [ ] 无参数时提示正确
- [ ] 查询结果格式正确

✅ **检查点 6.3**: 其他命令
- [ ] 库存总结命令正常
- [ ] 会员总结命令正常
- [ ] 月度总结命令正常
- [ ] 帮助命令显示所有可用命令
- [ ] 入库命令参数验证正确

**如果所有检查点通过，继续下一步。**

---

## 🔗 集成测试

完成所有模块测试后，进行集成测试，验证整个系统的工作流程。

### 步骤 7: 运行所有单元测试

首先确保所有单元测试都通过：

```bash
# 运行所有测试
pytest tests/ -v

# 预期结果：44 passed
```

### 步骤 8: 端到端集成测试

创建集成测试脚本，验证完整的消息处理流程：

#### 8.1 创建集成测试文件

```bash
# 创建集成测试目录（如果不存在）
mkdir -p tests/integration
```

#### 8.2 运行集成测试脚本

我们创建一个简单的集成测试来验证完整流程：

```python
# tests/integration/test_end_to_end.py
"""
端到端集成测试
验证从消息接收到数据库保存的完整流程
"""
import pytest
from datetime import datetime
from parsing.preprocessor import MessagePreProcessor
from parsing.llm_parser import create_llm_parser
from parsing.pipeline import MessagePipeline
from db.repository import DatabaseRepository


class MockLLMParser:
    """Mock LLM 解析器用于集成测试"""
    def __init__(self):
        self.return_value = []
    
    async def parse_message(self, sender, timestamp, content):
        return self.return_value


@pytest.mark.asyncio
async def test_end_to_end_service_message(temp_db):
    """测试服务消息的完整处理流程"""
    # 1. 初始化组件
    preprocessor = MessagePreProcessor()
    llm_parser = MockLLMParser()
    pipeline = MessagePipeline(preprocessor, llm_parser, temp_db)
    
    # 2. 设置 LLM 返回结果
    llm_parser.return_value = [{
        "type": "service",
        "date": "2024-01-28",
        "customer_name": "段老师",
        "service_or_product": "头疗",
        "amount": 30,
        "confidence": 0.95
    }]
    
    # 3. 构造测试消息
    raw_msg = {
        'wechat_msg_id': 'integration_test_001',
        'sender_nickname': '测试用户',
        'content': '1.28段老师头疗30',
        'timestamp': datetime(2024, 1, 28, 10, 0, 0),
        'is_at_bot': False
    }
    
    # 4. 处理消息
    result = await pipeline.process(raw_msg)
    
    # 5. 验证结果
    assert result.status == 'parsed'
    assert len(result.records) == 1
    
    # 6. 验证数据库
    from datetime import date
    records = temp_db.get_records_by_date(date(2024, 1, 28))
    assert len(records) == 1
    assert records[0]['customer_name'] == '段老师'
    assert records[0]['service_type'] == '头疗'
```

#### 8.3 运行集成测试

```bash
# 运行集成测试
pytest tests/integration/ -v

# 或运行所有测试（包括集成测试）
pytest tests/ -v
```

### 步骤 9: 手动集成测试

除了自动化测试，还可以进行手动集成测试：

#### 9.1 测试完整消息处理流程

```python
# 创建测试脚本: tests/integration/manual_test.py
"""
手动集成测试脚本
运行: python tests/integration/manual_test.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from db.repository import DatabaseRepository
from parsing.preprocessor import MessagePreProcessor
from parsing.pipeline import MessagePipeline
import asyncio


class SimpleLLMParser:
    """简单的 LLM 解析器（用于手动测试）"""
    async def parse_message(self, sender, timestamp, content):
        # 简单的规则解析（用于测试）
        if "头疗" in content and "段老师" in content:
            return [{
                "type": "service",
                "date": "2024-01-28",
                "customer_name": "段老师",
                "service_or_product": "头疗",
                "amount": 30,
                "confidence": 0.9
            }]
        return [{"type": "noise"}]


async def main():
    print("=" * 50)
    print("手动集成测试")
    print("=" * 50)
    
    # 1. 初始化
    db = DatabaseRepository(database_url="sqlite:///test_integration.db")
    db.create_tables()
    
    preprocessor = MessagePreProcessor()
    llm_parser = SimpleLLMParser()
    pipeline = MessagePipeline(preprocessor, llm_parser, db)
    
    # 2. 测试消息1：服务消息
    print("\n[测试1] 处理服务消息...")
    msg1 = {
        'wechat_msg_id': 'manual_test_001',
        'sender_nickname': '测试用户',
        'content': '1.28段老师头疗30',
        'timestamp': datetime(2024, 1, 28, 10, 0, 0),
        'is_at_bot': False
    }
    result1 = await pipeline.process(msg1)
    print(f"  状态: {result1.status}")
    print(f"  记录数: {len(result1.records)}")
    
    # 3. 验证数据库
    print("\n[验证] 查询数据库...")
    records = db.get_records_by_date(date(2024, 1, 28))
    print(f"  找到 {len(records)} 条记录")
    for r in records:
        print(f"  - {r['customer_name']} {r.get('service_type', '')} ¥{r.get('amount', 0)}")
    
    # 4. 测试消息2：噪声消息
    print("\n[测试2] 处理噪声消息...")
    msg2 = {
        'wechat_msg_id': 'manual_test_002',
        'sender_nickname': '测试用户',
        'content': '接',
        'timestamp': datetime(2024, 1, 28, 10, 1, 0),
        'is_at_bot': False
    }
    result2 = await pipeline.process(msg2)
    print(f"  状态: {result2.status}")
    print(f"  记录数: {len(result2.records)}")
    
    print("\n" + "=" * 50)
    print("手动集成测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
```

运行手动测试：

```bash
python tests/integration/manual_test.py
```

#### 9.2 验证集成测试结果

✅ **集成测试检查点**:

- [ ] 消息能正确通过预处理
- [ ] LLM 解析器能正确解析消息
- [ ] 数据能正确保存到数据库
- [ ] 查询功能正常工作
- [ ] 噪声消息被正确过滤
- [ ] 错误情况被正确处理

---

## 📊 测试覆盖率报告

生成详细的测试覆盖率报告：

```bash
# 生成覆盖率报告
./tests/run_module_tests.sh coverage

# 或手动运行
pytest tests/ --cov=parsing --cov=db --cov=services --cov=core \
    --cov-report=term-missing --cov-report=html -v

# 查看 HTML 报告
open htmlcov/index.html
# 或
xdg-open htmlcov/index.html  # Linux
```

### 覆盖率目标

- ✅ 核心业务逻辑: >80%
- ✅ 消息预处理: >85%
- ✅ 数据库操作: >80%
- ✅ 汇总服务: >95%

---

## 🔍 问题排查

### 常见问题

#### 1. 测试失败：数据库连接错误

```bash
# 检查数据库文件权限
ls -la data/

# 确保目录存在
mkdir -p data logs
```

#### 2. 测试失败：导入错误

```bash
# 确保在项目根目录
cd /home/yeshougan/project/We-Bussiness-Manager

# 检查 Python 路径
python -c "import sys; print(sys.path)"
```

#### 3. 测试失败：异步测试问题

```bash
# 确保安装了 pytest-asyncio
pip install pytest-asyncio

# 检查 pytest 配置
pytest --collect-only tests/test_pipeline.py
```

#### 4. 测试超时

```bash
# 增加超时时间
pytest tests/ -v --timeout=30
```

### 调试技巧

#### 1. 运行单个测试

```bash
# 运行特定测试
pytest tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise -v -s

# -s 参数显示 print 输出
```

#### 2. 查看详细错误信息

```bash
# 显示完整错误堆栈
pytest tests/ -v --tb=long

# 显示简短错误信息
pytest tests/ -v --tb=short
```

#### 3. 进入调试器

```bash
# 失败时进入调试器
pytest tests/ --pdb
```

---

## ✅ 测试完成检查清单

完成所有测试后，检查以下项目：

### 单元测试

- [ ] 消息预处理器：4/4 通过
- [ ] LLM 解析器：6/6 通过
- [ ] 数据库访问层：10/10 通过
- [ ] 消息处理流水线：8/8 通过
- [ ] 汇总服务：6/6 通过
- [ ] 命令处理器：10/10 通过

### 集成测试

- [ ] 端到端消息处理流程正常
- [ ] 数据库操作正常
- [ ] 错误处理正常
- [ ] 边界情况处理正常

### 覆盖率

- [ ] 总体覆盖率 >65%
- [ ] 核心模块覆盖率 >80%
- [ ] 关键功能覆盖率 >90%

### 文档

- [ ] 测试结果已记录
- [ ] 问题已修复
- [ ] 测试报告已生成

---

## 📝 测试报告模板

完成测试后，记录测试结果：

```markdown
# 测试执行报告

**日期**: YYYY-MM-DD
**测试人员**: [你的名字]
**环境**: Conda (wechat-business-manager), Python 3.11.14

## 测试结果

| 模块 | 测试数 | 通过 | 失败 | 状态 |
|------|--------|------|------|------|
| 消息预处理器 | 4 | 4 | 0 | ✅ |
| LLM 解析器 | 6 | 6 | 0 | ✅ |
| 数据库访问层 | 10 | 10 | 0 | ✅ |
| 消息处理流水线 | 8 | 8 | 0 | ✅ |
| 汇总服务 | 6 | 6 | 0 | ✅ |
| 命令处理器 | 10 | 10 | 0 | ✅ |
| **总计** | **44** | **44** | **0** | **✅** |

## 覆盖率

- 总体覆盖率: XX%
- 核心模块覆盖率: XX%

## 问题记录

[记录任何发现的问题]

## 结论

[测试结论]
```

---

## 🚀 快速参考

### 运行所有测试

```bash
conda activate wechat-business-manager
pytest tests/ -v
```

### 运行单个模块

```bash
./tests/run_module_tests.sh <模块名>
```

### 生成覆盖率报告

```bash
./tests/run_module_tests.sh coverage
```

### 查看测试帮助

```bash
./tests/run_module_tests.sh
```

---

## 📚 相关文档

- `FINAL_TEST_REPORT.md` - 最终测试报告
- `tests/MODULE_TEST_REPORT.md` - 各模块详细报告
- `tests/TESTING_GUIDE.md` - 测试指南
- `tests/README.md` - 测试说明

---

**祝测试顺利！** 🎉

