#!/bin/bash
# Miniconda 安装和环境设置脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Miniconda 安装和环境设置"
echo "=========================================="

# 检查是否已安装 conda
if command -v conda &> /dev/null; then
    echo "✅ Conda 已安装: $(conda --version)"
    CONDA_INSTALLED=true
else
    echo "❌ Conda 未安装，开始安装 Miniconda..."
    CONDA_INSTALLED=false
fi

# 如果没有安装，下载并安装 Miniconda
if [ "$CONDA_INSTALLED" = false ]; then
    echo ""
    echo "📥 下载 Miniconda..."
    
    # 检测系统架构
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    elif [ "$ARCH" = "aarch64" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
    else
        echo "❌ 不支持的架构: $ARCH"
        exit 1
    fi
    
    MINICONDA_INSTALLER="/tmp/miniconda.sh"
    
    # 下载 Miniconda
    wget -q "$MINICONDA_URL" -O "$MINICONDA_INSTALLER" || {
        echo "❌ 下载失败，请检查网络连接"
        exit 1
    }
    
    echo "📦 安装 Miniconda..."
    bash "$MINICONDA_INSTALLER" -b -p "$HOME/miniconda3"
    
    # 初始化 conda
    echo "🔧 初始化 Conda..."
    "$HOME/miniconda3/bin/conda" init bash
    
    # 添加到 PATH
    export PATH="$HOME/miniconda3/bin:$PATH"
    
    # 清理安装文件
    rm "$MINICONDA_INSTALLER"
    
    echo "✅ Miniconda 安装完成！"
    echo "⚠️  请运行: source ~/.bashrc 或重新打开终端"
fi

# 确保 conda 在 PATH 中
if [ -f "$HOME/miniconda3/bin/conda" ]; then
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

# 接受服务条款
echo ""
echo "📝 接受 Conda 服务条款..."
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

# 更新 conda
echo ""
echo "🔄 更新 Conda..."
conda update -y conda 2>/dev/null || echo "⚠️  更新 conda 失败，继续..."

# 创建新的 conda 环境
ENV_NAME="wechat-business-manager"
PYTHON_VERSION="3.11"

echo ""
echo "🐍 创建 Conda 环境: $ENV_NAME (Python $PYTHON_VERSION)..."

# 检查环境是否已存在
if conda env list | grep -q "^$ENV_NAME "; then
    echo "⚠️  环境 $ENV_NAME 已存在，是否删除并重新创建？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  删除现有环境..."
        conda env remove -n "$ENV_NAME" -y
        conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
    else
        echo "✅ 使用现有环境"
    fi
else
    conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
fi

# 激活环境
echo ""
echo "🔌 激活环境..."
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

# 安装项目依赖
echo ""
echo "📦 安装项目依赖..."
cd "$(dirname "$0")"

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装测试依赖
echo ""
echo "🧪 安装测试依赖..."
pip install pytest pytest-asyncio pytest-cov

echo ""
echo "=========================================="
echo "✅ 环境设置完成！"
echo "=========================================="
echo ""
echo "使用以下命令激活环境："
echo "  conda activate $ENV_NAME"
echo ""
echo "运行测试："
echo "  pytest tests/ -v"
echo "  或"
echo "  python tests/run_all_tests.py"
echo ""

