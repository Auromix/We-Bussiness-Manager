# 测试说明

## 测试结构

```
tests/
├── conftest.py              # Pytest 配置和共享 fixtures
├── test_preprocessor.py     # 消息预处理器测试
├── test_llm_parser.py       # LLM 解析器测试（使用 Mock）
├── test_pipeline.py         # 消息处理流水线测试
├── test_repository.py       # 数据库访问层测试
├── test_command_handler.py  # 命令处理器测试
├── test_summary_svc.py      # 汇总服务测试
├── run_all_tests.py         # 运行所有测试的脚本
└── fixtures/
    └── sample_messages.json # 示例消息数据
```

## 运行测试

### 运行所有测试

```bash
# 方式1：使用 pytest
pytest tests/ -v

# 方式2：使用脚本
python tests/run_all_tests.py

# 方式3：运行单个测试文件
pytest tests/test_preprocessor.py -v
```

### 运行特定测试

```bash
# 运行特定测试类
pytest tests/test_preprocessor.py::TestMessagePreProcessor -v

# 运行特定测试方法
pytest tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise -v

# 运行带标记的测试
pytest tests/ -m asyncio -v
```

## 测试覆盖

### 1. test_preprocessor.py
- ✅ 噪声过滤
- ✅ 日期提取（多种格式）
- ✅ 意图分类
- ✅ 金额提取

### 2. test_llm_parser.py
- ✅ OpenAI 解析器（Mock）
- ✅ Claude 解析器（Mock）
- ✅ 多条记录解析
- ✅ Fallback 机制

### 3. test_pipeline.py
- ✅ 噪声消息处理
- ✅ 服务消息处理
- ✅ 低置信度处理
- ✅ 多条记录处理
- ✅ LLM 失败处理
- ✅ 会员消息处理
- ✅ 商品销售处理

### 4. test_repository.py
- ✅ 原始消息保存和去重
- ✅ 顾客/员工/服务类型创建
- ✅ 服务记录保存（含提成）
- ✅ 按日期查询记录
- ✅ 商品销售保存
- ✅ 会员卡保存
- ✅ 解析状态更新

### 5. test_command_handler.py
- ✅ 每日汇总（空数据/有数据）
- ✅ 库存总结
- ✅ 会员总结
- ✅ 月度总结
- ✅ 查询记录
- ✅ 帮助命令
- ✅ 入库命令

### 6. test_summary_svc.py
- ✅ 空数据汇总
- ✅ 服务记录汇总
- ✅ 带提成汇总
- ✅ 商品销售汇总
- ✅ 待确认记录汇总
- ✅ 月度汇总

## 测试 Fixtures

### temp_db
创建临时数据库，每个测试使用独立的数据库文件，测试结束后自动清理。

### sample_message
提供标准的测试消息数据。

### sample_datetime
提供标准的测试日期时间。

## 注意事项

1. **数据库测试**：使用临时数据库，不会影响实际数据
2. **LLM 测试**：使用 Mock，不需要真实的 API Key
3. **异步测试**：使用 `pytest-asyncio` 运行异步测试
4. **依赖**：确保安装了所有测试依赖：
   ```bash
   pip install pytest pytest-asyncio
   ```

## 测试覆盖率

运行测试覆盖率报告：

```bash
pytest tests/ --cov=. --cov-report=html
```

## 持续集成

可以在 CI/CD 中运行：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-asyncio
    pytest tests/ -v
```

