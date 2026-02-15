# 测试快速参考卡片

## 🚀 快速开始

```bash
# 1. 激活环境
conda activate wechat-business-manager

# 2. 运行所有测试
pytest tests/ -v
```

## 📋 逐步测试流程

### 步骤 1: 消息预处理器
```bash
./tests/run_module_tests.sh preprocessor
# 或
pytest tests/test_preprocessor.py -v
```
**检查**: 4个测试全部通过 ✅

### 步骤 2: LLM 解析器
```bash
./tests/run_module_tests.sh llm_parser
# 或
pytest tests/test_llm_parser.py -v
```
**检查**: 6个测试全部通过 ✅

### 步骤 3: 数据库访问层
```bash
./tests/run_module_tests.sh repository
# 或
pytest tests/test_repository.py -v
```
**检查**: 10个测试全部通过 ✅

### 步骤 4: 消息处理流水线
```bash
./tests/run_module_tests.sh pipeline
# 或
pytest tests/test_pipeline.py -v
```
**检查**: 8个测试全部通过 ✅

### 步骤 5: 汇总服务
```bash
./tests/run_module_tests.sh summary
# 或
pytest tests/test_summary_svc.py -v
```
**检查**: 6个测试全部通过 ✅

### 步骤 6: 命令处理器
```bash
./tests/run_module_tests.sh command
# 或
pytest tests/test_command_handler.py -v
```
**检查**: 10个测试全部通过 ✅

### 步骤 7: 集成测试
```bash
# 自动化集成测试
pytest tests/integration/ -v

# 手动集成测试
python tests/integration/manual_test.py
```
**检查**: 3个集成测试全部通过 ✅

## 📊 测试统计

| 模块 | 测试数 | 状态 |
|------|--------|------|
| 消息预处理器 | 4 | ✅ |
| LLM 解析器 | 6 | ✅ |
| 数据库访问层 | 10 | ✅ |
| 消息处理流水线 | 8 | ✅ |
| 汇总服务 | 6 | ✅ |
| 命令处理器 | 10 | ✅ |
| 集成测试 | 3 | ✅ |
| **总计** | **47** | **✅** |

## 🎯 常用命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_preprocessor.py -v

# 运行特定测试
pytest tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise -v

# 生成覆盖率报告
./tests/run_module_tests.sh coverage

# 查看测试帮助
./tests/run_module_tests.sh
```

## 📝 详细文档

- `TESTING_README.md` - 完整测试指南（推荐阅读）
- `FINAL_TEST_REPORT.md` - 最终测试报告
- `tests/MODULE_TEST_REPORT.md` - 各模块详细报告

