# FundAnalysis 项目一键初始化脚本 (Windows)
# 运行: powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectDir

Write-Host "=== FundAnalysis 项目初始化 ===" -ForegroundColor Green
Write-Host ""

# 1. 检查 Python
Write-Host "1/3 检查 Python..."
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    Write-Host "  [FAIL] 未找到 Python，请先安装" -ForegroundColor Red
    exit 1
}
$PyVersion = & python --version
Write-Host "  [OK] 找到 $PyVersion"

# 2. 创建虚拟环境
Write-Host "2/3 创建虚拟环境..."
if (Test-Path ".venv") {
    Write-Host "  [WARN] .venv 已存在，跳过" -ForegroundColor Yellow
} else {
    & python -m venv .venv
    Write-Host "  [OK] 虚拟环境已创建"
}

# 3. 激活并安装依赖
Write-Host "3/3 安装依赖..."
& .\.venv\Scripts\Activate.ps1
& pip install -q -r requirements.txt
Write-Host "  [OK] 依赖安装完成"

# 验证安装
Write-Host "验证安装..."
& python -c "import streamlit, duckdb, pandas, plotly, jinja2, pytest; print('  [OK] 所有依赖可正常导入')"

Write-Host ""
Write-Host "=== 初始化完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "后续步骤:"
Write-Host "  1. 编辑 .env 文件，填入同花顺 API 凭证"
Write-Host "  2. 安装同花顺 API SDK（由用户手动完成）"
Write-Host "  3. 运行 python scripts\verify_api.py 验证 API 连通性"
Write-Host "  4. 运行 pytest 确认测试通过"
