#!/usr/bin/env bash
# FundAnalysis 项目一键初始化脚本 (Linux/macOS)
# 运行: bash scripts/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== FundAnalysis 项目初始化 ==="
echo ""

# 1. 检查 Python
echo "1/3 检查 Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
    PY_VERSION=$($PYTHON --version 2>&1)
    echo "  [OK] 找到 $PY_VERSION"
else
    echo "  [FAIL] 未找到 Python 3，请先安装"
    exit 1
fi

# 2. 创建虚拟环境
echo "2/3 创建虚拟环境..."
if [ -d ".venv" ]; then
    echo "  [WARN] .venv 已存在，跳过"
else
    $PYTHON -m venv .venv
    echo "  [OK] 虚拟环境已创建"
fi

# 3. 激活并安装依赖
echo "3/3 安装依赖..."
source .venv/bin/activate
pip install -r requirements.txt
echo "  [OK] 依赖安装完成"

# 验证安装
python -c "import streamlit, duckdb, pandas, plotly, jinja2, pytest; print('  [OK] 所有依赖可正常导入')"

echo ""
echo "=== 初始化完成 ==="
echo ""
echo "后续步骤:"
echo "  1. 编辑 .env 文件，填入同花顺 API 凭证"
echo "  2. 安装同花顺 API SDK（由用户手动完成）"
echo "  3. 运行 python scripts/verify_api.py 验证 API 连通性"
echo "  4. 运行 pytest 确认测试通过"
