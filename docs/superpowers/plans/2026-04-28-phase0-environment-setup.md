# Phase 0: 前置环境准备 执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立完整的开发基础设施，消除所有后续开发的阻塞点。

**Architecture:** 从零搭建项目脚手架，包括目录结构、虚拟环境、依赖安装、配置管理、测试基础设施。所有模块采用极简实现，不引入多余抽象。同花顺 API 的 SDK 安装与连通性验证由用户手动完成，不纳入初始化脚本。

**Tech Stack:** Python 3.14, DuckDB 1.5, Streamlit 1.56, pytest 9.0, Playwright 1.58

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `.env.example` | Create | API凭证和配置占位符 |
| `.gitignore` | Modify | 补充Python/DuckDB/Streamlit忽略规则 |
| `data/__init__.py` | Create | Package marker |
| `data/config.py` | Create | 配置管理模块（读取.env） |
| `analysis/__init__.py` | Create | Package marker |
| `report/__init__.py` | Create | Package marker |
| `report/templates/` | Create | 报告模板目录（空） |
| `ui/__init__.py` | Create | Package marker |
| `ui/pages/` | Create | 页面目录（空） |
| `tests/__init__.py` | Create | Package marker |
| `tests/conftest.py` | Create | pytest fixtures |
| `tests/pytest.ini` | Create | pytest 配置 |
| `tests/test_config.py` | Create | 配置模块测试 |
| `tests/test_api_connectivity.py` | Create | API连通性测试 |
| `requirements.txt` | Create | 项目依赖清单 |
| `scripts/__init__.py` | Create | Package marker |
| `scripts/verify_api.py` | Create | API连通性验证脚本 |
| `scripts/setup.sh` | Create | Linux/macOS一键初始化脚本 |
| `scripts/setup.ps1` | Create | Windows一键初始化脚本 |

---

### Task 1: 依赖清单与 .env 模板

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: 创建 requirements.txt**

```
streamlit==1.56.0
plotly==6.7.0
jinja2==3.1.6
playwright==1.58.0
duckdb==1.5.2
numpy==2.4.4
pandas==3.0.2
scipy==1.17.1
python-dotenv==1.2.2
pytest==9.0.3
```

> `python-dotenv` 用于配置管理，`pytest` 用于测试基础设施。

- [ ] **Step 2: 创建 .env.example**

```
# 同花顺 API 配置
THS_API_USERNAME=your_username
THS_API_PASSWORD=your_password
THS_API_TOKEN=your_token

# 数据库路径（相对于项目根目录）
DB_PATH=data/fund_analysis.db

# API 请求超时（秒）
API_TIMEOUT=30

# API 重试最大次数
API_MAX_RETRIES=3
```

- [ ] **Step 3: 更新 .gitignore**

在现有 `.gitignore` 末尾追加：

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/

# Environment
.env

# IDE
.vscode/
.idea/

# Streamlit
.streamlit/

# DuckDB
*.duckdb
*.db.wal

# Playwright
.playwright/
```

> 注意：`.env.example` 需要被 git 跟踪，所以不忽略它。已有的 `*.db` 和 `__pycache__/` 已在原文件中，不重复添加。

- [ ] **Step 4: 复制 .env.example 为 .env**

```bash
cp .env.example .env
```

> 用户后续需要手动编辑 `.env` 填入真实凭证。

---

### Task 2: 项目目录脚手架

**Files:**
- Create: `data/__init__.py`
- Create: `analysis/__init__.py`
- Create: `report/__init__.py`
- Create: `ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `scripts/` (directory)
- Create: `report/templates/` (directory)
- Create: `ui/pages/` (directory)

- [ ] **Step 1: 创建所有包目录和 __init__.py**

```bash
mkdir -p data analysis report/templates ui/pages tests scripts
touch data/__init__.py analysis/__init__.py report/__init__.py ui/__init__.py tests/__init__.py scripts/__init__.py
```

目录结构应与 SEPC.md 第6节一致：

```
FundAnalysis/
├── app.py                          # (Phase 4 创建)
├── requirements.txt
├── .env
├── .env.example
├── data/
│   ├── __init__.py
│   ├── fetcher.py                  # (Phase 1 创建)
│   ├── database.py                 # (Phase 1 创建)
│   └── config.py                   # (Task 3 创建)
├── analysis/
│   ├── __init__.py
│   ├── competitor.py               # (Phase 2 创建)
│   ├── metrics.py                  # (Phase 2 创建)
│   └── similarity.py               # (Phase 2 创建)
├── report/
│   ├── __init__.py
│   ├── generator.py                # (Phase 3 创建)
│   ├── summary_templates.py        # (Phase 3 创建)
│   └── templates/
│       └── fund_report.html        # (Phase 3 创建)
├── ui/
│   ├── __init__.py
│   ├── components.py               # (Phase 4 创建)
│   └── pages/
│       ├── dashboard.py            # (Phase 4 创建)
│       └── report_viewer.py        # (Phase 4 创建)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── pytest.ini
│   ├── test_config.py              # (Task 3 创建)
│   ├── test_api_connectivity.py    # (Task 4 创建)
│   ├── test_fetcher.py             # (Phase 1 创建)
│   ├── test_competitor.py          # (Phase 2 创建)
│   └── test_metrics.py             # (Phase 2 创建)
└── scripts/
    ├── __init__.py
    ├── setup.sh                    # (Task 5 创建)
    ├── setup.ps1                   # (Task 5 创建)
    └── verify_api.py               # (Task 4 创建)
```

- [ ] **Step 2: 验证目录结构**

```bash
find . -type f -name "*.py" -o -name "*.txt" -o -name ".env*" | sort
```

确认所有 `__init__.py` 和目录已就位。

---

### Task 3: 配置管理模块

**Files:**
- Create: `data/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 编写配置模块测试**

```python
# tests/test_config.py
import os
from data.config import Settings


def test_settings_loads_from_env():
    """Settings 应从 .env 文件加载配置"""
    settings = Settings()
    assert hasattr(settings, "ths_api_username")
    assert hasattr(settings, "ths_api_password")
    assert hasattr(settings, "ths_api_token")
    assert hasattr(settings, "db_path")
    assert hasattr(settings, "api_timeout")
    assert hasattr(settings, "api_max_retries")


def test_settings_default_values():
    """未设置环境变量时应使用默认值"""
    settings = Settings()
    assert settings.db_path == "data/fund_analysis.db"
    assert settings.api_timeout == 30
    assert settings.api_max_retries == 3


def test_settings_env_overrides_defaults(test_env):
    """环境变量应覆盖默认值"""
    import os
    settings = Settings()
    assert settings.ths_api_username == os.getenv("THS_API_USERNAME")
    assert settings.api_timeout == 10
    assert settings.api_max_retries == 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'data.config'"

- [ ] **Step 3: 实现配置模块**

```python
# data/config.py
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（data/config.py 的上两级）
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")


class Settings:
    """集中管理所有配置项，从环境变量读取。"""

    def __init__(self):
        # 同花顺 API
        self.ths_api_username = os.getenv("THS_API_USERNAME", "")
        self.ths_api_password = os.getenv("THS_API_PASSWORD", "")
        self.ths_api_token = os.getenv("THS_API_TOKEN", "")

        # 数据库
        self.db_path = os.getenv("DB_PATH", "data/fund_analysis.db")

        # API 请求
        self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.api_max_retries = int(os.getenv("API_MAX_RETRIES", "3"))


# 全局单例
settings = Settings()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_config.py -v
```

Expected: 全部 PASS

- [ ] **Step 5: 验证可从外部导入**

```bash
python -c "from data.config import settings; print(f'DB: {settings.db_path}, Timeout: {settings.api_timeout}')"
```

Expected: 输出默认配置值

---

### Task 4: API 连通性验证

**Files:**
- Create: `scripts/verify_api.py`
- Create: `tests/test_api_connectivity.py`

> 注意：同花顺 API 的具体调用方式取决于其 SDK 或 HTTP 接口。由于当前尚未获取到同花顺 API 的真实文档，本任务先搭建验证脚本框架，使用占位实现。用户填入真实凭证后，脚本即可运行。

- [ ] **Step 1: 创建连通性测试**

```python
# tests/test_api_connectivity.py
from unittest.mock import patch


def test_verify_api_success(test_env):
    """模拟 API 连接成功场景"""
    mock_response = {"status": "ok", "message": "连接成功"}

    with patch("scripts.verify_api.connect_to_api", return_value=mock_response) as mock_connect:
        from scripts import verify_api
        result = verify_api.main_logic()
        assert result is True
        mock_connect.assert_called_once()


def test_verify_api_failure(test_env):
    """模拟 API 连接失败场景"""
    with patch("scripts.verify_api.connect_to_api", side_effect=ConnectionError("连接超时")):
        from scripts import verify_api
        result = verify_api.main_logic()
        assert result is False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_api_connectivity.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现连通性验证脚本**

```python
# scripts/verify_api.py
"""同花顺 API 连通性验证脚本。

运行: python scripts/verify_api.py
返回: 0 表示连接成功，1 表示失败
"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.config import settings


def connect_to_api():
    """尝试连接同花顺 API。

    TODO: 接入真实的同花顺 API SDK 或 HTTP 请求。
    当前使用占位实现，仅验证凭证是否已配置。
    """
    if not settings.ths_api_username or not settings.ths_api_token:
        raise ConnectionError(
            "未配置 API 凭证，请编辑 .env 文件填写 THS_API_USERNAME 和 THS_API_TOKEN"
        )

    # TODO: 替换为真实 API 调用
    # 示例：使用同花顺 iFinD SDK 或 HTTP 接口
    # from ths_api import THSClient
    # client = THSClient(username=settings.ths_api_username, token=settings.ths_api_token)
    # client.login()
    # return client.query("test_query")

    return {"status": "ok", "message": "凭证已配置（真实API调用待接入）"}


def main_logic():
    """执行连通性检查，返回 True/False。"""
    try:
        print("正在连接同花顺 API...")
        print(f"  用户名: {settings.ths_api_username or '(未配置)'}")
        print(f"  超时设置: {settings.api_timeout}s")

        result = connect_to_api()

        if result.get("status") == "ok":
            print(f"✓ 连接成功: {result.get('message', 'OK')}")
            return True
        else:
            print(f"✗ 连接失败: {result.get('message', '未知错误')}")
            return False

    except ConnectionError as e:
        print(f"✗ 连接失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = main_logic()
    sys.exit(0 if success else 1)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_api_connectivity.py -v
```

Expected: 全部 PASS

- [ ] **Step 5: 手动运行验证脚本**

```bash
python scripts/verify_api.py
```

Expected: 由于 `.env` 中为占位符，应输出"未配置 API 凭证"提示。这是预期行为。

---

### Task 5: 一键初始化脚本

**Files:**
- Create: `scripts/setup.sh`
- Create: `scripts/setup.ps1`

- [ ] **Step 1: 创建 Bash 初始化脚本**

```bash
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
    echo "  ✓ 找到 $PY_VERSION"
else
    echo "  ✗ 未找到 Python 3，请先安装"
    exit 1
fi

# 2. 创建虚拟环境
echo "2/3 创建虚拟环境..."
if [ -d ".venv" ]; then
    echo "  ⚠ .venv 已存在，跳过"
else
    $PYTHON -m venv .venv
    echo "  ✓ 虚拟环境已创建"
fi

# 3. 激活并安装依赖
echo "3/3 安装依赖..."
source .venv/bin/activate
pip install -q -r requirements.txt
echo "  ✓ 依赖安装完成"

# 验证安装
python -c "import streamlit, duckdb, pandas, plotly, jinja2, pytest; print('  ✓ 所有依赖可正常导入')"

echo ""
echo "=== 初始化完成 ==="
echo ""
echo "后续步骤:"
echo "  1. 编辑 .env 文件，填入同花顺 API 凭证"
echo "  2. 安装同花顺 API SDK（由用户手动完成）"
echo "  3. 运行 python scripts/verify_api.py 验证 API 连通性"
echo "  4. 运行 pytest 确认测试通过"
```

- [ ] **Step 2: 创建 PowerShell 初始化脚本**

```powershell
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
    Write-Host "  ✗ 未找到 Python，请先安装" -ForegroundColor Red
    exit 1
}
$PyVersion = & python --version
Write-Host "  ✓ 找到 $PyVersion"

# 2. 创建虚拟环境
Write-Host "2/3 创建虚拟环境..."
if (Test-Path ".venv") {
    Write-Host "  ⚠ .venv 已存在，跳过" -ForegroundColor Yellow
} else {
    & python -m venv .venv
    Write-Host "  ✓ 虚拟环境已创建"
}

# 3. 激活并安装依赖
Write-Host "3/3 安装依赖..."
& .\.venv\Scripts\Activate.ps1
& pip install -q -r requirements.txt
Write-Host "  ✓ 依赖安装完成"

# 验证安装
Write-Host "验证安装..."
& python -c "import streamlit, duckdb, pandas, plotly, jinja2, pytest; print('  ✓ 所有依赖可正常导入')"

Write-Host ""
Write-Host "=== 初始化完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "后续步骤:"
Write-Host "  1. 编辑 .env 文件，填入同花顺 API 凭证"
Write-Host "  2. 安装同花顺 API SDK（由用户手动完成）"
Write-Host "  3. 运行 python scripts\verify_api.py 验证 API 连通性"
Write-Host "  4. 运行 pytest 确认测试通过"
```

- [ ] **Step 3: 赋予脚本可执行权限（Bash）**

```bash
chmod +x scripts/setup.sh
```

- [ ] **Step 4: 在 Windows 环境运行 PowerShell 脚本验证**

```bash
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Expected: 脚本应成功创建虚拟环境、安装依赖、验证导入。

---

### Task 6: 测试基础设施 (conftest.py)

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/pytest.ini`

- [ ] **Step 1: 创建 pytest 配置**

```ini
# tests/pytest.ini
[pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

- [ ] **Step 2: 创建 pytest 配置和 fixtures**

```python
# tests/conftest.py
import pytest


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """为需要隔离环境的测试提供独立配置。

    使用方式：在测试函数参数中声明 test_env fixture。
    不声明的测试将使用真实环境变量（便于测试默认值行为）。
    """
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("THS_API_USERNAME", "test_user")
    monkeypatch.setenv("THS_API_PASSWORD", "test_pass")
    monkeypatch.setenv("THS_API_TOKEN", "test_token")
    monkeypatch.setenv("API_TIMEOUT", "10")
    monkeypatch.setenv("API_MAX_RETRIES", "1")


@pytest.fixture
def mock_api_response():
    """返回模拟的同花顺 API 响应数据。"""
    return {
        "status": "ok",
        "data": {
            "fund_code": "000001",
            "fund_name": "华夏成长混合",
            "fund_type": "混合型",
            "nav": 1.234,
            "acc_nav": 3.456,
        },
    }
```

- [ ] **Step 3: 运行全部测试验证**

```bash
pytest -v
```

Expected: 所有 Phase 0 相关测试 PASS（test_config.py 和 test_api_connectivity.py）

- [ ] **Step 4: 提交（配置模块 + 测试基础设施）**

```bash
git add data/__init__.py data/config.py tests/__init__.py tests/conftest.py tests/pytest.ini tests/test_config.py
git commit -m "feat: 配置管理模块与测试基础设施"
```

- [ ] **Step 5: 提交（API 验证脚本）**

```bash
git add scripts/__init__.py scripts/verify_api.py tests/test_api_connectivity.py
git commit -m "feat: API 连通性验证脚本（占位实现）"
```

---

### Task 7: Playwright 浏览器安装验证

**Files:**
- No new files

> Playwright 浏览器是 Phase 3 PDF 导出所需的依赖。本任务独立于 setup 脚本，由执行者手动运行。

- [ ] **Step 1: 安装 Playwright 浏览器**

```bash
playwright install chromium
```

> Windows 环境下通常无需额外系统依赖。如果使用虚拟环境，需先激活。

- [ ] **Step 2: 验证 Playwright 可用**

```bash
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print('Playwright OK'); b.close(); p.stop()"
```

Expected: 输出 "Playwright OK"

- [ ] **Step 3: 如果 Step 1 失败（系统依赖缺失），运行**

```bash
playwright install --with-deps chromium
```

> Windows 通常不需要额外系统依赖，如果仍失败需手动排查。

- [ ] **Step 4: 提交（如果有配置变更）**

```bash
git status
```

如果有新增文件（如 Playwright 配置文件），添加并提交：

```bash
git add .
git commit -m "chore: Phase 0 完成 — Playwright 浏览器安装验证"
```

---

## Verification

Phase 0 完成后，应能通过以下命令验证：

```bash
# 1. 目录结构完整
python -c "
import pathlib
dirs = ['data', 'analysis', 'report', 'report/templates', 'ui', 'ui/pages', 'tests', 'scripts']
for d in dirs:
    assert pathlib.Path(d).is_dir(), f'缺少目录: {d}'
print('✓ 所有目录已创建')
"

# 2. 依赖可导入
python -c "import streamlit, duckdb, pandas, plotly, jinja2, pytest; print('✓ 所有依赖可导入')"

# 3. 配置模块可用
python -c "from data.config import settings; print(f'✓ DB: {settings.db_path}')"

# 4. 测试全部通过
pytest -v
# 应看到 test_config.py 和 test_api_connectivity.py 全部 PASS

# 5. Playwright 可用
python -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')"
```

## Task Dependency Graph

```
Task 1 (requirements.txt + .env)
  └── Task 2 (目录脚手架 + scripts/__init__.py)
        ├── Task 3 (配置模块)
        │     └── Task 6 Step 3-4 (测试基础设施, conftest + pytest.ini)
        └── Task 4 (API 验证脚本)
  └── Task 5 (初始化脚本，已移除 API/Playwright 安装)
  └── Task 7 (Playwright) — 独立，最后验证
```

## 用户手动操作项

以下内容不纳入自动初始化脚本，需由用户完成：

| 操作 | 说明 |
|------|------|
| 同花顺 API SDK 安装 | 根据同花顺提供的文档安装 SDK |
| 同花顺 API 连通性验证 | 编辑 `.env` 填入凭证后，运行 `python scripts/verify_api.py` |
