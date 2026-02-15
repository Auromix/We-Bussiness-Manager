# Conda 环境设置完成 ✅

## 环境信息

- **Conda 版本**: 25.11.1
- **环境名称**: `wechat-business-manager`
- **Python 版本**: 3.11.14
- **安装位置**: `~/miniconda3/envs/wechat-business-manager`

## 快速使用

### 激活环境

```bash
# 方式1：使用脚本（推荐）
source activate_env.sh

# 方式2：手动激活
export PATH="$HOME/miniconda3/bin:$PATH"
eval "$(conda shell.bash hook)"
conda activate wechat-business-manager
```

### 运行测试

```bash
# 激活环境后
pytest tests/ -v

# 或使用测试脚本
python tests/run_all_tests.py

# 运行单个模块
pytest tests/test_preprocessor.py -v
```

### 退出环境

```bash
conda deactivate
```

## 已安装的包

### 核心依赖
- SQLAlchemy 2.0+
- Pydantic 2.0+
- Loguru
- APScheduler
- Python-dateutil

### 测试依赖
- pytest 9.0.2
- pytest-asyncio 1.3.0
- pytest-cov 7.0.0

### LLM API（可选，测试时使用 Mock）
- openai
- anthropic

## 测试结果

运行 `pytest tests/ -v` 查看完整测试结果。

## 环境管理命令

```bash
# 查看所有环境
conda env list

# 查看当前环境信息
conda info

# 查看已安装的包
conda list
# 或
pip list

# 更新包
pip install --upgrade <package_name>

# 删除环境（如果需要）
conda env remove -n wechat-business-manager
```

## 常见问题

### 1. 环境激活失败

如果遇到 "command not found: conda"：

```bash
# 初始化 conda
source ~/miniconda3/bin/activate
conda init bash
source ~/.bashrc
```

### 2. 测试失败

确保已激活环境：

```bash
# 检查 Python 版本
python --version  # 应该是 3.11.14

# 检查 pytest
pytest --version

# 重新安装测试依赖
pip install pytest pytest-asyncio pytest-cov
```

### 3. 依赖冲突

如果遇到依赖冲突：

```bash
# 清理并重新安装
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

## 下一步

1. ✅ 环境已设置完成
2. ✅ 依赖已安装
3. ✅ 测试可以运行
4. 📝 开始开发或运行完整测试套件

## 验证安装

运行以下命令验证环境：

```bash
# 激活环境
conda activate wechat-business-manager

# 检查关键组件
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import pytest; print('Pytest OK')"
python -c "from parsing.preprocessor import MessagePreProcessor; print('Preprocessor OK')"

# 运行一个测试
pytest tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise -v
```

