# 测试指南

## 快速开始

### 1. 安装测试依赖

```bash
pip install pytest pytest-asyncio
```

或者安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 运行测试

#### 运行所有测试

```bash
# 方式1：使用 pytest
pytest tests/ -v

# 方式2：使用脚本
python tests/run_all_tests.py

# 方式3：使用 shell 脚本
./tests/run_module_test.sh all
```

#### 运行单个模块测试

```bash
# 使用 pytest 直接运行
pytest tests/test_preprocessor.py -v

# 使用 shell 脚本
./tests/run_module_test.sh preprocessor
```

## 各模块测试说明

### 1. 消息预处理器 (test_preprocessor.py)

测试消息预处理器的核心功能：

```bash
pytest tests/test_preprocessor.py -v
```

**测试内容**：
- ✅ 噪声消息过滤
- ✅ 日期提取（支持多种格式：1.28, 1/28, 1|28, 1月28日）
- ✅ 意图分类（service/product/membership/correction）
- ✅ 金额提取

**示例**：
```python
def test_is_noise():
    preprocessor = MessagePreProcessor()
    assert preprocessor.is_noise("接") == True
    assert preprocessor.is_noise("1.28段老师头疗30") == False
```

### 2. LLM 解析器 (test_llm_parser.py)

测试 LLM 解析器（使用 Mock，不需要真实 API）：

```bash
pytest tests/test_llm_parser.py -v -s
```

**测试内容**：
- ✅ OpenAI 解析器 Mock 测试
- ✅ Claude 解析器 Mock 测试
- ✅ 多条记录解析
- ✅ Fallback 机制

**注意**：这些测试使用 Mock，不需要真实的 API Key。

### 3. 消息处理流水线 (test_pipeline.py)

测试完整的消息处理流程：

```bash
pytest tests/test_pipeline.py -v -s
```

**测试内容**：
- ✅ 噪声消息处理
- ✅ 服务消息处理
- ✅ 低置信度处理（需要确认）
- ✅ 多条记录处理
- ✅ LLM 失败处理
- ✅ 会员消息处理
- ✅ 商品销售处理

### 4. 数据库访问层 (test_repository.py)

测试数据库操作：

```bash
pytest tests/test_repository.py -v
```

**测试内容**：
- ✅ 原始消息保存和去重
- ✅ 顾客/员工/服务类型创建
- ✅ 服务记录保存（含提成）
- ✅ 按日期查询记录
- ✅ 商品销售保存
- ✅ 会员卡保存

**注意**：使用临时数据库，不会影响实际数据。

### 5. 命令处理器 (test_command_handler.py)

测试命令处理功能：

```bash
pytest tests/test_command_handler.py -v
```

**测试内容**：
- ✅ 每日汇总
- ✅ 库存总结
- ✅ 会员总结
- ✅ 查询记录
- ✅ 帮助命令

### 6. 汇总服务 (test_summary_svc.py)

测试汇总报表生成：

```bash
pytest tests/test_summary_svc.py -v
```

**测试内容**：
- ✅ 空数据汇总
- ✅ 服务记录汇总
- ✅ 带提成汇总
- ✅ 商品销售汇总
- ✅ 待确认记录汇总
- ✅ 月度汇总

## 测试 Fixtures

### temp_db
创建临时数据库，每个测试使用独立的数据库文件。

```python
def test_something(temp_db):
    # temp_db 是一个 DatabaseRepository 实例
    # 使用临时数据库，测试结束后自动清理
    pass
```

### sample_message
提供标准的测试消息数据。

```python
def test_message_processing(sample_message):
    # sample_message 包含完整的消息数据
    pass
```

## 测试覆盖率

生成测试覆盖率报告：

```bash
# 安装覆盖率工具
pip install pytest-cov

# 生成报告
pytest tests/ --cov=. --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 调试测试

### 运行单个测试

```bash
pytest tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise -v
```

### 显示 print 输出

```bash
pytest tests/test_preprocessor.py -v -s
```

### 在失败时进入调试器

```bash
pytest tests/test_preprocessor.py --pdb
```

## 常见问题

### 1. 导入错误

如果遇到导入错误，确保项目根目录在 Python 路径中：

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### 2. 数据库错误

测试使用临时数据库，如果遇到数据库错误：
- 检查 SQLite 是否可用
- 确保有写权限

### 3. 异步测试失败

确保安装了 `pytest-asyncio`：

```bash
pip install pytest-asyncio
```

## 持续集成

在 CI/CD 中运行测试：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      - name: Run tests
        run: pytest tests/ -v
```

## 测试最佳实践

1. **独立性**：每个测试应该独立运行，不依赖其他测试
2. **可重复性**：测试结果应该一致，不依赖外部状态
3. **快速**：测试应该快速运行
4. **清晰**：测试名称应该清晰描述测试内容
5. **覆盖**：尽可能覆盖各种边界情况

## 添加新测试

添加新测试时：

1. 在对应的测试文件中添加测试方法
2. 使用描述性的测试名称
3. 添加必要的注释
4. 确保测试可以独立运行
5. 更新本文档

示例：

```python
def test_new_feature(self, temp_db):
    """测试新功能"""
    # Arrange
    data = {...}
    
    # Act
    result = function_under_test(data)
    
    # Assert
    assert result == expected
```

