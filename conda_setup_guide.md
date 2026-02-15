# Conda 环境设置指南

## 快速开始

### 方式一：使用自动安装脚本（推荐）

```bash
# 运行安装脚本
./setup_conda_env.sh
```

脚本会自动：
1. 检查并安装 Miniconda（如果未安装）
2. 创建名为 `wechat-business-manager` 的 conda 环境
3. 安装所有项目依赖
4. 安装测试依赖

### 方式二：手动安装

#### 1. 安装 Miniconda

```bash
# 下载 Miniconda（Linux x86_64）
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh

# 按照提示完成安装，然后初始化
source ~/.bashrc
# 或重新打开终端
```

#### 2. 创建 Conda 环境

```bash
# 创建新环境（Python 3.11）
conda create -n wechat-business-manager python=3.11 -y

# 激活环境
conda activate wechat-business-manager
```

#### 3. 安装依赖

```bash
# 进入项目目录
cd /home/yeshougan/project/We-Bussiness-Manager

# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov
```

## 使用环境

### 激活环境

```bash
conda activate wechat-business-manager
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单个模块测试
pytest tests/test_preprocessor.py -v

# 使用测试脚本
python tests/run_all_tests.py
```

### 退出环境

```bash
conda deactivate
```

## 环境管理

### 查看所有环境

```bash
conda env list
```

### 删除环境

```bash
conda env remove -n wechat-business-manager
```

### 导出环境配置

```bash
conda env export > environment.yml
```

### 从配置文件创建环境

```bash
conda env create -f environment.yml
```

## 常见问题

### 1. Conda 命令未找到

如果安装后找不到 conda 命令：

```bash
# 初始化 conda
source ~/miniconda3/bin/activate
conda init bash

# 重新加载 shell 配置
source ~/.bashrc
```

### 2. 环境激活失败

```bash
# 手动初始化 conda
eval "$(conda shell.bash hook)"
conda activate wechat-business-manager
```

### 3. 依赖安装失败

```bash
# 更新 conda
conda update conda

# 清理缓存
conda clean --all

# 重新安装
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 4. 测试运行失败

确保已激活环境并安装了所有依赖：

```bash
# 检查 Python 版本
python --version  # 应该是 3.11.x

# 检查已安装的包
pip list | grep pytest

# 重新安装测试依赖
pip install pytest pytest-asyncio pytest-cov
```

## 环境信息

- **环境名称**: `wechat-business-manager`
- **Python 版本**: 3.11
- **包管理器**: pip (通过 conda 环境)

## 验证安装

运行以下命令验证环境设置是否正确：

```bash
# 激活环境
conda activate wechat-business-manager

# 检查 Python 版本
python --version

# 检查关键依赖
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
python -c "import pytest; print('Pytest:', pytest.__version__)"

# 运行一个简单测试
pytest tests/test_preprocessor.py::TestMessagePreProcessor::test_is_noise -v
```

## 下一步

环境设置完成后：

1. ✅ 运行所有测试：`pytest tests/ -v`
2. ✅ 查看测试覆盖率：`pytest tests/ --cov=. --cov-report=html`
3. ✅ 开始开发或调试

