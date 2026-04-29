# Phase 1: 数据基础设施 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the data layer — DuckDB schema, iFinD API fetcher, incremental sync, and data quality validation.

**Architecture:** `data/database.py` 负责 DuckDB 建表和 CRUD，`data/fetcher.py` 封装同花顺 API 调用（含重试/增量/校验），通过 `data/config.py` 的 Settings 读取配置。所有模块可独立运行，也可被上层 analysis 模块调用。

**Tech Stack:** DuckDB 1.5.2, pandas 3.0.2, iFinDAPI (iFinDPy), pytest 9.0.3, python-dotenv 1.2.2

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `data/__init__.py` | Modify | 导出公共接口 |
| `data/database.py` | Create | DuckDB 连接管理、7 张表建表、CRUD 操作 |
| `data/fetcher.py` | Create | 同花顺 API 封装：净值/持仓/基金经理/规模拉取、增量更新、数据校验 |
| `tests/test_database.py` | Create | 数据库建表、数据写入、增量更新测试 |
| `tests/test_fetcher.py` | Create | API 调用模拟、数据解析、校验逻辑测试 |
| `scripts/verify_api.py` | Modify | 清理占位符，改用真实 THS 连接 |
| `tests/conftest.py` | Modify | 增加 fetcher 和 database 相关 fixtures |
| `.env.example` | Create | 环境变量占位符模板 |

---

### Task 1: `.env.example` 模板

**Files:**
- Create: `.env.example`

- [ ] **Step 1: 创建 `.env.example`**

```bash
# 同花顺 iFinD API 凭证
THS_API_USERNAME=
THS_API_PASSWORD=
THS_API_TOKEN=

# 数据库路径
DB_PATH=data/fund_analysis.db

# API 请求配置
API_TIMEOUT=30
API_MAX_RETRIES=3
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "feat(Phase1): 添加 .env.example 环境变量模板"
```

---

### Task 2: `data/database.py` — DuckDB Schema & CRUD

**Files:**
- Create: `data/database.py`
- Modify: `data/__init__.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Write failing tests for database creation**

```python
"""tests/test_database.py"""
import pytest
import duckdb
from pathlib import Path


def test_create_tables_creates_all_7_tables(test_env):
    """所有 7 张表应该被创建。"""
    from data.database import FundDatabase

    db = FundDatabase()
    conn = db.get_connection()

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {t[0] for t in tables}

    expected = {
        "funds", "nav_history", "holdings", "metrics_cache",
        "watchlist", "reports", "sync_log",
    }
    assert expected.issubset(table_names), f"缺失表: {expected - table_names}"


def test_insert_fund_basic_info(test_env):
    """应该能插入并查询基金基本信息。"""
    from data.database import FundDatabase

    db = FundDatabase()
    db.insert_fund(
        code="000001",
        name="华夏成长混合",
        type="混合型",
        manager="张三",
        company="华夏基金",
        benchmark="沪深300指数",
        established_date="2020-01-01",
    )

    fund = db.get_fund("000001")
    assert fund is not None
    assert fund["code"] == "000001"
    assert fund["name"] == "华夏成长混合"
    assert fund["type"] == "混合型"


def test_insert_nav_history(test_env):
    """应该能插入并查询净值历史。"""
    from data.database import FundDatabase

    db = FundDatabase()
    db.insert_fund("000001", "华夏成长混合", "混合型")
    db.insert_nav("000001", "2024-01-01", 1.500, 2.000)
    db.insert_nav("000001", "2024-01-02", 1.520, 2.020)

    navs = db.get_nav("000001")
    assert len(navs) == 2
    assert navs[0]["nav"] == 1.500
    assert navs[1]["nav"] == 1.520


def test_get_last_sync_date_returns_none_when_no_sync(test_env):
    """无同步记录时应返回 None。"""
    from data.database import FundDatabase

    db = FundDatabase()
    result = db.get_last_sync_date("000001", "full")
    assert result is None


def test_update_sync_log(test_env):
    """应该能更新同步日志。"""
    from data.database import FundDatabase

    db = FundDatabase()
    db.update_sync_log("000001", "incremental", "2024-01-15", "fingerprint_abc")

    last_date = db.get_last_sync_date("000001", "incremental")
    assert str(last_date) == "2024-01-15"


def test_nav_upsert_prevents_duplicates(test_env):
    """重复插入同一日期的净值应该覆盖而非重复。"""
    from data.database import FundDatabase

    db = FundDatabase()
    db.insert_fund("000001", "华夏成长混合", "混合型")
    db.insert_nav("000001", "2024-01-01", 1.500, 2.000)
    db.insert_nav("000001", "2024-01-01", 1.510, 2.010)  # 覆盖

    navs = db.get_nav("000001")
    assert len(navs) == 1
    assert navs[0]["nav"] == 1.510


def test_insert_holdings(test_env):
    """应该能插入并查询持仓数据。"""
    from data.database import FundDatabase

    db = FundDatabase()
    db.insert_fund("000001", "华夏成长混合", "混合型")
    db.insert_holding("000001", "2024-06-30", "600519", "贵州茅台", 5.12)
    db.insert_holding("000001", "2024-06-30", "000858", "五粮液", 3.45)

    holdings = db.get_holdings("000001", "2024-06-30")
    assert len(holdings) == 2
    assert holdings[0]["stock_code"] == "600519"
    assert holdings[0]["weight"] == 5.12


def test_insert_fund_idempotent(test_env):
    """重复插入同一基金应该覆盖更新而非报错。"""
    from data.database import FundDatabase

    db = FundDatabase()
    db.insert_fund("000001", "华夏成长混合", "混合型", manager="张三")
    db.insert_fund("000001", "华夏成长混合A", "混合型", manager="李四")

    fund = db.get_fund("000001")
    assert fund["name"] == "华夏成长混合A"
    assert fund["manager"] == "李四"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_database.py -v
```
Expected: All FAIL with "ModuleNotFoundError: No module named 'data.database'"

- [ ] **Step 3: Implement `data/database.py`**

```python
"""data/database.py — DuckDB 数据库管理。"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from data.config import settings

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

_SCHEMA = """
CREATE TABLE IF NOT EXISTS funds (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    manager TEXT,
    company TEXT,
    benchmark TEXT,
    established_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nav_history (
    fund_code TEXT REFERENCES funds(code),
    date DATE,
    nav REAL NOT NULL,
    acc_nav REAL NOT NULL,
    PRIMARY KEY (fund_code, date)
);

CREATE TABLE IF NOT EXISTS holdings (
    fund_code TEXT REFERENCES funds(code),
    report_date DATE,
    stock_code TEXT,
    stock_name TEXT,
    weight REAL,
    PRIMARY KEY (fund_code, report_date, stock_code)
);

CREATE TABLE IF NOT EXISTS metrics_cache (
    fund_code TEXT REFERENCES funds(code),
    metric_name TEXT,
    period TEXT,
    value REAL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (fund_code, metric_name, period)
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_fund TEXT REFERENCES funds(code),
    competitor_fund TEXT REFERENCES funds(code),
    similarity_score REAL,
    confirmed BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_fund TEXT REFERENCES funds(code),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    html_path TEXT,
    pdf_path TEXT
);

CREATE TABLE IF NOT EXISTS sync_log (
    fund_code TEXT REFERENCES funds(code),
    sync_type TEXT,
    last_update_date DATE,
    data_fingerprint TEXT,
    PRIMARY KEY (fund_code, sync_type)
);
"""


class FundDatabase:
    """DuckDB 数据库操作层。"""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or settings.db_path
        full_path = BASE_DIR / self._db_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(full_path))
        self._init_schema()

    def _init_schema(self) -> None:
        """创建所有表（幂等）。"""
        for stmt in _SCHEMA.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._conn.execute(stmt)
        self._conn.execute("CHECKPOINT")

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """返回底层连接（仅供测试）。"""
        return self._conn

    # --- funds 表操作 ---

    def insert_fund(
        self,
        code: str,
        name: str,
        type: str,
        manager: str | None = None,
        company: str | None = None,
        benchmark: str | None = None,
        established_date: str | None = None,
    ) -> None:
        """插入或更新基金基本信息（幂等）。"""
        self._conn.execute(
            """
            INSERT INTO funds (code, name, type, manager, company, benchmark, established_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                manager = excluded.manager,
                company = excluded.company,
                benchmark = excluded.benchmark,
                established_date = excluded.established_date,
                updated_at = CURRENT_TIMESTAMP
            """,
            [code, name, type, manager, company, benchmark, established_date],
        )

    def get_fund(self, code: str) -> dict[str, Any] | None:
        """按代码查询基金信息。"""
        result = self._conn.execute(
            "SELECT * FROM funds WHERE code = ?", [code]
        ).fetchone()
        if result is None:
            return None
        cols = [desc[0] for desc in self._conn.description]
        return dict(zip(cols, result))

    # --- nav_history 表操作 ---

    def insert_nav(
        self,
        fund_code: str,
        date_str: str,
        nav: float,
        acc_nav: float,
    ) -> None:
        """插入净值记录（幂等，重复日期会覆盖）。"""
        self._conn.execute(
            """
            INSERT INTO nav_history (fund_code, date, nav, acc_nav)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(fund_code, date) DO UPDATE SET
                nav = excluded.nav,
                acc_nav = excluded.acc_nav
            """,
            [fund_code, date_str, nav, acc_nav],
        )

    def get_nav(self, fund_code: str) -> list[dict[str, Any]]:
        """查询基金全部净值，按日期升序。"""
        rows = self._conn.execute(
            "SELECT * FROM nav_history WHERE fund_code = ? ORDER BY date ASC",
            [fund_code],
        ).fetchall()
        cols = [desc[0] for desc in self._conn.description]
        return [dict(zip(cols, r)) for r in rows]

    # --- holdings 表操作 ---

    def insert_holding(
        self,
        fund_code: str,
        report_date: str,
        stock_code: str,
        stock_name: str,
        weight: float,
    ) -> None:
        """插入持仓记录（幂等）。"""
        self._conn.execute(
            """
            INSERT INTO holdings (fund_code, report_date, stock_code, stock_name, weight)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fund_code, report_date, stock_code) DO UPDATE SET
                stock_name = excluded.stock_name,
                weight = excluded.weight
            """,
            [fund_code, report_date, stock_code, stock_name, weight],
        )

    def get_holdings(
        self, fund_code: str, report_date: str
    ) -> list[dict[str, Any]]:
        """查询指定报告期的持仓。"""
        rows = self._conn.execute(
            "SELECT * FROM holdings WHERE fund_code = ? AND report_date = ?",
            [fund_code, report_date],
        ).fetchall()
        cols = [desc[0] for desc in self._conn.description]
        return [dict(zip(cols, r)) for r in rows]

    # --- sync_log 表操作 ---

    def update_sync_log(
        self,
        fund_code: str,
        sync_type: str,
        last_update_date: str,
        data_fingerprint: str | None = None,
    ) -> None:
        """更新同步日志。"""
        self._conn.execute(
            """
            INSERT INTO sync_log (fund_code, sync_type, last_update_date, data_fingerprint)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(fund_code, sync_type) DO UPDATE SET
                last_update_date = excluded.last_update_date,
                data_fingerprint = excluded.data_fingerprint
            """,
            [fund_code, sync_type, last_update_date, data_fingerprint],
        )

    def get_last_sync_date(
        self, fund_code: str, sync_type: str
    ) -> date | None:
        """获取上次同步日期。"""
        result = self._conn.execute(
            "SELECT last_update_date FROM sync_log WHERE fund_code = ? AND sync_type = ?",
            [fund_code, sync_type],
        ).fetchone()
        if result is None:
            return None
        return result[0]

    def close(self) -> None:
        """关闭连接。"""
        self._conn.close()
```

- [ ] **Step 4: Update `data/__init__.py`**

```python
"""data 包 — 数据获取与存储。"""
from data.database import FundDatabase
from data.fetcher import TongHuaShunFetcher

__all__ = ["FundDatabase", "TongHuaShunFetcher"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_database.py -v
```
Expected: All 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add data/database.py data/__init__.py tests/test_database.py
git commit -m "feat(Phase1-M1): 实现 DuckDB schema 和 CRUD 操作层"
```

---

### Task 3: `data/fetcher.py` — 同花顺 API 封装（M1 核心）

**Files:**
- Create: `data/fetcher.py`
- Modify: `tests/conftest.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write failing tests for fetcher**

```python
"""tests/test_fetcher.py"""
import pytest
from unittest.mock import patch, MagicMock


# --- 净值解析测试 ---

def test_parse_nav_response_parses_valid_data():
    """应该能正确解析 API 返回的净值数据。"""
    from data.fetcher import TongHuaShunFetcher

    # 模拟 iFinDAPI THS_HQ 返回格式
    mock_response = MagicMock()
    mock_response.errorcode = 0
    mock_response.time = ["2024-01-01", "2024-01-02", "2024-01-03"]
    mock_response.data = {
        "unit_nav": ["1.500", "1.520", "1.480"],
        "acc_nav": ["2.000", "2.020", "1.980"],
    }

    fetcher = TongHuaShunFetcher()
    result = fetcher._parse_nav_response(mock_response)

    assert len(result) == 3
    assert result[0]["date"] == "2024-01-01"
    assert result[0]["nav"] == 1.500
    assert result[0]["acc_nav"] == 2.000


def test_parse_nav_response_handles_empty():
    """空响应应返回空列表。"""
    from data.fetcher import TongHuaShunFetcher

    mock_response = MagicMock()
    mock_response.errorcode = 0
    mock_response.time = []
    mock_response.data = {"unit_nav": [], "acc_nav": []}

    fetcher = TongHuaShunFetcher()
    result = fetcher._parse_nav_response(mock_response)

    assert result == []


# --- 持仓解析测试 ---

def test_parse_holdings_response_parses_valid_data():
    """应该能正确解析 API 返回的持仓数据。"""
    from data.fetcher import TongHuaShunFetcher

    # 模拟 THS_BD 持仓返回：各指标值为列表
    mock_response = MagicMock()
    mock_response.errorcode = 0
    mock_response.data = {
        "fund_portfolio_stockcode": ["600519", "000858"],
        "fund_portfolio_stockname": ["贵州茅台", "五粮液"],
        "fund_portfolio_weight": [5.12, 3.45],
    }

    fetcher = TongHuaShunFetcher()
    result = fetcher._parse_holdings_response(mock_response)

    assert len(result) == 2
    assert result[0]["stock_code"] == "600519"
    assert result[0]["weight"] == 5.12


# --- 数据校验测试 ---

def test_validate_nav_flags_negative_nav():
    """负数净值应标记为脏数据。"""
    from data.fetcher import TongHuaShunFetcher

    fetcher = TongHuaShunFetcher()
    navs = [
        {"date": "2024-01-01", "nav": 1.500, "acc_nav": 2.000},
        {"date": "2024-01-02", "nav": -0.100, "acc_nav": 1.900},  # 负数
    ]
    flagged = fetcher.validate_nav_data(navs)
    assert len(flagged) == 1
    assert flagged[0]["date"] == "2024-01-02"


def test_validate_nav_flags_extreme_fluctuation():
    """单日波动 >10% 应标记为脏数据。"""
    from data.fetcher import TongHuaShunFetcher

    fetcher = TongHuaShunFetcher()
    navs = [
        {"date": "2024-01-01", "nav": 1.000, "acc_nav": 1.500},
        {"date": "2024-01-02", "nav": 1.150, "acc_nav": 1.650},  # +15%
    ]
    flagged = fetcher.validate_nav_data(navs)
    assert len(flagged) == 1
    assert flagged[0]["date"] == "2024-01-02"


def test_validate_nav_clean_data_passes():
    """正常数据不应被标记。"""
    from data.fetcher import TongHuaShunFetcher

    fetcher = TongHuaShunFetcher()
    navs = [
        {"date": "2024-01-01", "nav": 1.000, "acc_nav": 1.500},
        {"date": "2024-01-02", "nav": 1.010, "acc_nav": 1.510},  # +1%
    ]
    flagged = fetcher.validate_nav_data(navs)
    assert len(flagged) == 0


# --- 基金信息解析测试 ---

def test_parse_fund_info_parses_valid_data():
    """应该能正确解析基金基本信息。"""
    from data.fetcher import TongHuaShunFetcher

    # 模拟 THS_BD 返回格式（data 为 dict）
    mock_response = MagicMock()
    mock_response.errorcode = 0
    mock_response.thscode = "000001.OF"
    mock_response.data = {
        "fund_name": "华夏成长混合",
        "fund_type": "混合型",
        "fund_manager": "张三",
        "fund_company": "华夏基金",
        "fund_benchmark": "沪深300指数",
        "established_date": "2020-01-01",
    }

    fetcher = TongHuaShunFetcher()
    result = fetcher._parse_fund_info_response(mock_response)

    assert result["code"] == "000001"
    assert result["name"] == "华夏成长混合"
    assert result["type"] == "混合型"
    assert result["manager"] == "张三"


# --- 重试机制测试 ---

def test_fetch_with_retry_succeeds_on_third_attempt():
    """第3次重试成功应返回结果。"""
    from data.fetcher import TongHuaShunFetcher

    call_count = 0

    def flaky_call(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Network error")
        mock_resp = MagicMock()
        mock_resp.errorcode = 0
        return mock_resp

    fetcher = TongHuaShunFetcher()
    result = fetcher._fetch_with_retry(flaky_call, "arg1")
    assert call_count == 3
    assert result.errorcode == 0
```

- [ ] **Step 2: Add fetcher fixtures to `tests/conftest.py`**

在现有 conftest.py 末尾追加：

```python
@pytest.fixture
def mock_nav_api_response():
    """模拟 THS_HQ 净值返回。"""
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.errorcode = 0
    resp.time = ["2024-01-01", "2024-01-02"]
    resp.data = {
        "unit_nav": ["1.500", "1.520"],
        "acc_nav": ["2.000", "2.020"],
    }
    return resp


@pytest.fixture
def mock_holdings_api_response():
    """模拟 THS_BD 持仓返回。"""
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.errorcode = 0
    resp.data = {
        "fund_portfolio_stockcode": ["600519", "000858"],
        "fund_portfolio_stockname": ["贵州茅台", "五粮液"],
        "fund_portfolio_weight": [5.12, 3.45],
    }
    return resp


@pytest.fixture
def mock_fund_info_api_response():
    """模拟 THS_BD 基金信息返回。"""
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.errorcode = 0
    resp.thscode = "000001.OF"
    resp.data = {
        "fund_name": "华夏成长混合",
        "fund_type": "混合型",
        "fund_manager": "张三",
        "fund_company": "华夏基金",
        "fund_benchmark": "沪深300指数",
        "established_date": "2020-01-01",
    }
    return resp
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_fetcher.py -v
```
Expected: All FAIL with "ModuleNotFoundError: No module named 'data.fetcher'"

**API 函数映射（来自 `docs/THS_API.md`）：**

| 用途 | THS 函数 | 签名 | 说明 |
|------|----------|------|------|
| 登录 | `THS_iFinDLogin` | `THS_iFinDLogin(username, password)` | errorcode=0 成功，-201 重复登录，-2 用户名/密码错误 |
| 基金基本信息 | `THS_BD` | `THS_BD(thsCode, indicatorName, paramOption)` | 基础数据，返回 `resp.data`（json/dict） |
| 净值历史 | `THS_HQ` | `THS_HQ(thscode, jsonIndicator, jsonparam, begintime, endtime)` | 历史行情，返回 `resp.tables` 包含 time 列表 + data |
| 持仓数据 | `THS_BD` | `THS_BD(thsCode, indicatorName, paramOption)` | 通过基金持仓类指标获取 |

**净值指标名**: `unit_nav;acc_nav`（单位净值、累计净值）
**基金信息指标名**: `fund_name;fund_type;fund_manager;fund_company;fund_benchmark;established_date`
**持仓指标名**: `fund_portfolio_stockcode;fund_portfolio_stockname;fund_portfolio_weight`
**历史行情参数(jsonparam)**: `CPS:2`（前复权，分红再投）、`fill:Omit`（非交易日跳过）

- [ ] **Step 4: Implement `data/fetcher.py`**

```python
"""data/fetcher.py — 同花顺 iFinD API 封装。

入口命令:
    python data/fetcher.py <fund_code>           # 全量拉取
    python data/fetcher.py <fund_code> --validate # 拉取 + 数据校验

使用的 iFinDPy 函数（参见 docs/THS_API.md）:
    THS_iFinDLogin(username, password)  — 登录
    THS_BD(thsCode, indicatorName, paramOption)  — 基础数据（基金信息、持仓）
    THS_HQ(thscode, jsonIndicator, jsonparam, begintime, endtime)  — 历史行情（净值）
"""
from __future__ import annotations

import hashlib
import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable

# 将项目根目录加入 sys.path（支持直接运行）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.config import settings

logger = logging.getLogger(__name__)


class TongHuaShunFetcher:
    """同花顺 iFinD API 数据获取器。

    负责：
    - 净值历史拉取与解析（THS_HQ）
    - 基金基本信息拉取与解析（THS_BD）
    - 持仓数据拉取与解析（THS_BD）
    - 指数退避重试
    - 数据质量校验
    """

    def __init__(self):
        self._max_retries = settings.api_max_retries
        self._timeout = settings.api_timeout

    # ==================== 公共接口 ====================

    def fetch_fund(self, fund_code: str, db=None, validate: bool = False) -> dict[str, Any]:
        """拉取单只基金的全部数据并可选写入数据库。

        Args:
            fund_code: 基金代码，如 "000001"
            db: FundDatabase 实例（可选，传入则写入）
            validate: 是否执行数据质量校验
        """
        logger.info(f"开始拉取基金 {fund_code} 数据...")

        # 1. 拉取基金基本信息
        fund_info = self.fetch_fund_info(fund_code)

        # 2. 拉取净值历史（增量模式：检查上次同步日期）
        start_date = None
        if db is not None:
            last_sync = db.get_last_sync_date(fund_code, "full")
            if last_sync is not None:
                from datetime import timedelta
                start_date = (last_sync + timedelta(days=1)).isoformat()
                logger.info(f"增量模式: 从 {start_date} 开始拉取")
            else:
                logger.info("全量模式: 无同步记录，拉取全部历史")

        nav_data = self.fetch_nav_history(fund_code, start_date=start_date)

        # 3. 数据校验
        dirty_navs = []
        if validate:
            dirty_navs = self.validate_nav_data(nav_data)
            if dirty_navs:
                logger.warning(f"发现 {len(dirty_navs)} 条脏数据: {[d['date'] for d in dirty_navs]}")
            # 过滤脏数据
            dirty_dates = {d["date"] for d in dirty_navs}
            nav_data = [n for n in nav_data if n["date"] not in dirty_dates]

        # 4. 拉取持仓（最近一期）
        holdings_data = self.fetch_holdings(fund_code)

        # 5. 写入数据库
        if db is not None:
            db.insert_fund(
                code=fund_info["code"],
                name=fund_info["name"],
                type=fund_info["type"],
                manager=fund_info.get("manager"),
                company=fund_info.get("company"),
                benchmark=fund_info.get("benchmark"),
                established_date=fund_info.get("established_date"),
            )
            for nav in nav_data:
                db.insert_nav(fund_code, nav["date"], nav["nav"], nav["acc_nav"])
            for h in holdings_data:
                db.insert_holding(fund_code, h["report_date"], h["stock_code"], h["stock_name"], h["weight"])

            # 更新同步日志
            if nav_data:
                latest_date = nav_data[-1]["date"]
                fingerprint = self._compute_fingerprint(nav_data)
                sync_type = "full" if start_date is None else "incremental"
                db.update_sync_log(fund_code, sync_type, latest_date, fingerprint)

        return {
            "fund_info": fund_info,
            "nav_count": len(nav_data),
            "holdings_count": len(holdings_data),
            "dirty_count": len(dirty_navs),
        }

    def fetch_fund_info(self, fund_code: str) -> dict[str, Any]:
        """拉取基金基本信息（使用 THS_BD）。"""
        ths_code = self._to_ths_code(fund_code)
        # THS_BD 指标：基金名称、类型、经理、公司、基准、成立日期
        indicators = "fund_name;fund_type;fund_manager;fund_company;fund_benchmark;established_date"

        resp = self._fetch_with_retry(
            self._call_ths_bd, ths_code, indicators
        )
        return self._parse_fund_info_response(resp)

    def fetch_nav_history(self, fund_code: str, start_date: str | None = None) -> list[dict[str, Any]]:
        """拉取净值历史（使用 THS_HQ）。

        Args:
            fund_code: 基金代码
            start_date: 起始日期（增量模式，格式 YYYY-MM-DD）
        """
        ths_code = self._to_ths_code(fund_code)
        # 指标：单位净值、累计净值
        indicators = "unit_nav;acc_nav"
        # 参数：前复权（分红再投），非交易日跳过
        params = "CPS:2,fill:Omit"

        begin = start_date or "1990-01-01"
        # 截止日期用今天
        from datetime import date
        end = date.today().isoformat()

        resp = self._fetch_with_retry(
            self._call_ths_hq, ths_code, indicators, params, begin, end
        )
        return self._parse_nav_response(resp)

    def fetch_holdings(self, fund_code: str) -> list[dict[str, Any]]:
        """拉取最近一期持仓（使用 THS_BD）。"""
        ths_code = self._to_ths_code(fund_code)
        # 持仓指标：重仓股票代码、名称、比例
        indicators = "fund_portfolio_stockcode;fund_portfolio_stockname;fund_portfolio_weight"

        resp = self._fetch_with_retry(
            self._call_ths_bd, ths_code, indicators
        )
        return self._parse_holdings_response(resp)

    # ==================== 数据校验 ====================

    def validate_nav_data(self, nav_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """校验净值数据，返回脏数据列表。

        规则:
        - 净值 < 0 → 脏数据
        - 单日波动 > 10% → 脏数据
        """
        dirty = []
        for i, nav in enumerate(nav_data):
            if nav["nav"] < 0:
                dirty.append(nav)
                continue

            if i > 0:
                prev_nav = nav_data[i - 1]["nav"]
                if prev_nav > 0:
                    change = abs(nav["nav"] - prev_nav) / prev_nav
                    if change > 0.10:
                        dirty.append(nav)

        return dirty

    # ==================== 内部方法 ====================

    def _to_ths_code(self, fund_code: str) -> str:
        """基金代码转同花顺格式。"""
        return f"{fund_code}.OF"

    def _parse_fund_info_response(self, resp) -> dict[str, Any]:
        """解析 THS_BD 返回的基金信息。

        THS_BD 返回结构：
            resp.errorcode — 错误码
            resp.data — dict，键为指标名，值为对应的数据
        """
        if resp.errorcode != 0:
            raise RuntimeError(f"API 返回错误: errorcode={resp.errorcode}")

        data = resp.data if hasattr(resp, "data") else {}

        # thscode 可能在 resp 中，也可能需要从调用上下文获取
        thscode = ""
        if hasattr(resp, "thscode") and resp.thscode:
            thscode = resp.thscode
        else:
            # 如果 data 中有 thscode 键
            thscode = data.get("thscode", "")

        # 从 thscode 提取纯数字代码 (e.g., "000001.OF" → "000001")
        code = thscode.split(".")[0] if thscode else ""

        return {
            "code": code,
            "name": data.get("fund_name", ""),
            "type": data.get("fund_type", ""),
            "manager": data.get("fund_manager"),
            "company": data.get("fund_company"),
            "benchmark": data.get("fund_benchmark"),
            "established_date": data.get("established_date"),
        }

    def _parse_nav_response(self, resp) -> list[dict[str, Any]]:
        """解析 THS_HQ 返回的净值数据。

        THS_HQ 返回结构：
            resp.errorcode — 错误码
            resp.time — 时间列表，如 ["2024-01-01", "2024-01-02", ...]
            resp.data — 指标数据，根据指标顺序排列
                - 如果返回的是 dict：键为指标名，值为列表
                - 如果返回的是 list：按指标顺序排列

        指标顺序: unit_nav (索引0), acc_nav (索引1)
        """
        if resp.errorcode != 0:
            raise RuntimeError(f"API 返回错误: errorcode={resp.errorcode}")

        time_list = getattr(resp, "time", [])
        if not time_list:
            return []

        # 获取净值数据
        data = resp.data if hasattr(resp, "data") else {}

        # THS_HQ 返回的 data 可能是 dict 或 list
        # 如果是 dict，键为指标名
        if isinstance(data, dict):
            unit_navs = data.get("unit_nav", [])
            acc_navs = data.get("acc_nav", [])
        elif isinstance(data, (list, tuple)):
            # 按指标顺序：第一个是 unit_nav，第二个是 acc_nav
            unit_navs = data[0] if len(data) > 0 else []
            acc_navs = data[1] if len(data) > 1 else []
        else:
            return []

        results = []
        for i, t in enumerate(time_list):
            if i < len(unit_navs) and i < len(acc_navs):
                try:
                    date_str = str(t)[:10]  # YYYY-MM-DD
                    results.append({
                        "date": date_str,
                        "nav": float(unit_navs[i]),
                        "acc_nav": float(acc_navs[i]),
                    })
                except (ValueError, TypeError):
                    continue  # 跳过无法解析的行

        return results

    def _parse_holdings_response(self, resp) -> list[dict[str, Any]]:
        """解析 THS_BD 返回的持仓数据。

        持仓数据返回结构类似 fund_info，data 为 dict，
        值为列表形式：["股票代码列表"], ["股票名称列表"], ["权重列表"]
        """
        if resp.errorcode != 0:
            raise RuntimeError(f"API 返回错误: errorcode={resp.errorcode}")

        data = resp.data if hasattr(resp, "data") else {}
        if not data:
            return []

        # THS_BD 持仓返回：各指标的值为列表
        stock_codes = data.get("fund_portfolio_stockcode", [])
        stock_names = data.get("fund_portfolio_stockname", [])
        weights = data.get("fund_portfolio_weight", [])

        # 如果值是字符串（单条目），转为列表
        if isinstance(stock_codes, str):
            stock_codes = [stock_codes]
        if isinstance(stock_names, str):
            stock_names = [stock_names]
        if isinstance(weights, str):
            weights = [weights]

        results = []
        for i in range(min(len(stock_codes), len(stock_names), len(weights))):
            try:
                results.append({
                    "report_date": "",  # THS_BD 持仓不直接返回报告期
                    "stock_code": str(stock_codes[i]),
                    "stock_name": str(stock_names[i]),
                    "weight": float(weights[i]),
                })
            except (ValueError, TypeError, IndexError):
                continue

        return results

    def _compute_fingerprint(self, nav_data: list[dict[str, Any]]) -> str:
        """计算数据指纹（用于检测数据是否变更）。"""
        text = "|".join(f"{n['date']}:{n['nav']}" for n in nav_data[-5:])
        return hashlib.md5(text.encode()).hexdigest()[:16]

    # ==================== 重试机制 ====================

    def _fetch_with_retry(self, func: Callable, *args, **kwargs):
        """指数退避重试调用。"""
        last_error = None
        for attempt in range(self._max_retries):
            try:
                result = func(*args, **kwargs)
                if hasattr(result, "errorcode") and result.errorcode != 0:
                    raise RuntimeError(f"API errorcode={result.errorcode}")
                return result
            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"API 调用失败 (尝试 {attempt + 1}/{self._max_retries})，{wait}s 后重试: {e}")
                    time.sleep(wait)
        raise last_error

    # ==================== THS API 调用封装 ====================

    def _call_ths_bd(self, ths_code: str, indicators: str):
        """调用 THS_BD 获取基础数据（基金信息、持仓）。"""
        from iFinDPy import THS_BD
        return THS_BD(ths_code, indicators, "")

    def _call_ths_hq(self, ths_code: str, indicators: str, params: str, begin: str, end: str):
        """调用 THS_HQ 获取历史行情（净值）。"""
        from iFinDPy import THS_HQ
        return THS_HQ(ths_code, indicators, params, begin, end)


def main():
    """CLI 入口：拉取单只基金数据。"""
    import argparse
    from data.database import FundDatabase

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 先登录
    from iFinDPy import THS_iFinDLogin
    login_result = THS_iFinDLogin(settings.ths_api_username, settings.ths_api_password)
    if login_result and getattr(login_result, "errorcode", -1) != 0:
        logger.error(f"登录失败: {getattr(login_result, 'errmsg', 'unknown')}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="同花顺基金数据拉取工具")
    parser.add_argument("fund_code", help="基金代码，如 000001")
    parser.add_argument("--validate", action="store_true", help="启用数据质量校验")
    args = parser.parse_args()

    db = FundDatabase()
    fetcher = TongHuaShunFetcher()

    try:
        result = fetcher.fetch_fund(args.fund_code, db=db, validate=args.validate)
        print(f"拉取完成:")
        print(f"  基金: {result['fund_info']['name']} ({result['fund_info']['code']})")
        print(f"  净值条数: {result['nav_count']}")
        print(f"  持仓条数: {result['holdings_count']}")
        if result["dirty_count"] > 0:
            print(f"  脏数据: {result['dirty_count']} 条已标记")
    except Exception as e:
        logger.error(f"拉取失败: {e}")
        sys.exit(1)
    finally:
        db.close()
        # 登出
        from iFinDPy import THS_iFinDLogout
        THS_iFinDLogout()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_fetcher.py -v
```
Expected: All 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add data/fetcher.py tests/test_fetcher.py tests/conftest.py
git commit -m "feat(Phase1-M1): 实现同花顺 API 封装、数据解析和质量校验"
```

---

### Task 4: 增量更新测试（M2）

**说明**: 增量逻辑已在 Task 3 的 `fetch_fund` 中实现。本 Task 仅添加测试。

**Files:**
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write failing test for incremental fetch**

在 `tests/test_fetcher.py` 中追加：

```python
def test_incremental_fetch_uses_sync_log_date(test_env):
    """第二次运行时应从上次同步日期开始增量拉取。"""
    from data.fetcher import TongHuaShunFetcher
    from data.database import FundDatabase

    db = FundDatabase()
    # 模拟已有同步记录
    db.update_sync_log("000001", "full", "2024-01-15", "fingerprint_abc")

    fetcher = TongHuaShunFetcher()

    # 模拟 API 调用，验证传入了正确的 start_date
    with patch.object(fetcher, "fetch_nav_history", wraps=fetcher.fetch_nav_history) as mock_nav:
        with patch.object(fetcher, "fetch_fund_info", return_value={
            "code": "000001", "name": "测试基金", "type": "混合型"
        }):
            with patch.object(fetcher, "fetch_holdings", return_value=[]):
                fetcher.fetch_fund("000001", db=db)

                # 应使用增量日期调用 fetch_nav_history
                mock_nav.assert_called_once_with("000001", start_date="2024-01-16")


def test_first_fetch_is_full(test_env):
    """首次运行时应全量拉取。"""
    from data.fetcher import TongHuaShunFetcher
    from data.database import FundDatabase

    db = FundDatabase()
    fetcher = TongHuaShunFetcher()

    with patch.object(fetcher, "fetch_nav_history", return_value=[
        {"date": "2024-01-01", "nav": 1.0, "acc_nav": 1.5}
    ]) as mock_nav:
        with patch.object(fetcher, "fetch_fund_info", return_value={
            "code": "000001", "name": "测试基金", "type": "混合型"
        }):
            with patch.object(fetcher, "fetch_holdings", return_value=[]):
                fetcher.fetch_fund("000001", db=db)

                mock_nav.assert_called_once_with("000001", start_date=None)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_fetcher.py::test_incremental_fetch_uses_sync_log_date -v
pytest tests/test_fetcher.py::test_first_fetch_is_full -v
```
Expected: FAIL — `fetch_fund` doesn't check sync_log yet

- [ ] **Step 3: 确认 `fetch_fund` 已包含增量逻辑**

Task 3 的 `fetch_fund` 已经在 Step 4 中实现了增量检查（通过 `db.get_last_sync_date` 判断 start_date）。运行测试确认即可。

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_fetcher.py -v
```
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add data/fetcher.py tests/test_fetcher.py
git commit -m "feat(Phase1-M2): 实现增量更新与断点续传"
```

---

### Task 5: 数据质量校验端到端测试（M3）

**说明**: `validate` 逻辑已在 Task 3 的 `fetch_fund` 和 `validate_nav_data` 中实现。本 Task 仅添加端到端测试。

**Files:**
- Create: `tests/test_data_quality.py`

- [ ] **Step 1: Write tests for dirty data isolation**

```python
"""tests/test_data_quality.py — M3: 数据质量校验端到端测试。"""
import pytest


def test_dirty_nav_not_inserted_into_db(test_env):
    """脏数据不应写入数据库。"""
    from data.fetcher import TongHuaShunFetcher
    from data.database import FundDatabase
    from unittest.mock import patch

    db = FundDatabase()
    fetcher = TongHuaShunFetcher()

    # 模拟含脏数据的返回
    nav_with_dirty = [
        {"date": "2024-01-01", "nav": 1.000, "acc_nav": 1.500},
        {"date": "2024-01-02", "nav": 1.010, "acc_nav": 1.510},
        {"date": "2024-01-03", "nav": -0.500, "acc_nav": 1.000},  # 负数，脏数据
    ]

    with patch.object(fetcher, "fetch_nav_history", return_value=nav_with_dirty):
        with patch.object(fetcher, "fetch_fund_info", return_value={
            "code": "000001", "name": "测试基金", "type": "混合型"
        }):
            with patch.object(fetcher, "fetch_holdings", return_value=[]):
                fetcher.fetch_fund("000001", db=db, validate=True)

    # 只应有 2 条净值（脏数据被过滤）
    navs = db.get_nav("000001")
    assert len(navs) == 2
    assert all(n["nav"] > 0 for n in navs)


def test_extreme_fluctuation_flagged(test_env):
    """单日波动 >10% 的净值应被标记。"""
    from data.fetcher import TongHuaShunFetcher

    fetcher = TongHuaShunFetcher()
    navs = [
        {"date": "2024-01-01", "nav": 1.000, "acc_nav": 1.500},
        {"date": "2024-01-02", "nav": 1.050, "acc_nav": 1.550},
        {"date": "2024-01-03", "nav": 1.200, "acc_nav": 1.700},  # +14.3%
    ]
    dirty = fetcher.validate_nav_data(navs)
    assert len(dirty) == 1
    assert dirty[0]["date"] == "2024-01-03"


def test_boundary_10_percent_not_flagged(test_env):
    """恰好 10% 波动不应被标记（阈值是 >10%）。"""
    from data.fetcher import TongHuaShunFetcher

    fetcher = TongHuaShunFetcher()
    navs = [
        {"date": "2024-01-01", "nav": 1.000, "acc_nav": 1.500},
        {"date": "2024-01-02", "nav": 1.100, "acc_nav": 1.600},  # 恰好 +10%
    ]
    dirty = fetcher.validate_nav_data(navs)
    assert len(dirty) == 0


def test_validate_without_db_still_returns_results(test_env):
    """不传 db 时，validate 仍应返回过滤后的结果。"""
    from data.fetcher import TongHuaShunFetcher
    from unittest.mock import patch

    fetcher = TongHuaShunFetcher()
    nav_with_dirty = [
        {"date": "2024-01-01", "nav": 1.000, "acc_nav": 1.500},
        {"date": "2024-01-02", "nav": -0.100, "acc_nav": 1.400},
    ]

    with patch.object(fetcher, "fetch_nav_history", return_value=nav_with_dirty):
        with patch.object(fetcher, "fetch_fund_info", return_value={
            "code": "000001", "name": "测试基金", "type": "混合型"
        }):
            with patch.object(fetcher, "fetch_holdings", return_value=[]):
                result = fetcher.fetch_fund("000001", db=None, validate=True)

    assert result["nav_count"] == 1
    assert result["dirty_count"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_data_quality.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Confirm `fetch_fund` with validate=True already filters dirty data**

Task 3 的实现已经包含了 `validate` 参数支持。如果测试通过则无需修改。如果测试失败，说明 `fetch_fund` 中 validate 分支有问题，修复即可。

- [ ] **Step 4: Run all tests**

```bash
pytest -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_data_quality.py
git commit -m "feat(Phase1-M3): 数据质量校验 — 端到端测试与验收"
```

---

### Task 6: 清理 `scripts/verify_api.py` 并更新测试

**Files:**
- Modify: `scripts/verify_api.py`
- Modify: `tests/test_api_connectivity.py`

- [ ] **Step 1: 更新 `scripts/verify_api.py`**

将 `main_THS` 函数改为正确的登录+查询验证：

```python
def main_THS():
    """同花顺 API 连接测试入口。"""
    print("=== 同花顺 API 连通性验证 ===")
    try:
        from iFinDPy import THS_iFinDLogin, THS_RQ

        print(f"正在登录 (用户: {settings.ths_api_username})...")
        login_result = THS_iFinDLogin(settings.ths_api_username, settings.ths_api_password)

        if login_result and getattr(login_result, "errorcode", -1) == 0:
            print("[OK] 登录成功，执行测试查询...")
            # THS_RQ(thscode, jsonIndicator, jsonparam) — 实时行情
            result = THS_RQ("920000.BJ", "open")
            print(f"测试查询结果: {result}")
            if hasattr(result, "errorcode") and result.errorcode == 0:
                print("[OK] 测试查询成功，API 完全可用")
                return True
            else:
                print(f"[WARN] 登录成功但查询返回错误: {getattr(result, 'errorcode', 'unknown')}")
                return True  # 登录成功即认为 API 可用
        else:
            ec = getattr(login_result, "errorcode", "unknown")
            errmsg = getattr(login_result, "errmsg", "unknown")
            print(f"[FAIL] 登录失败: errorcode={ec}, errmsg={errmsg}")
            return False
    except ImportError:
        print("[FAIL] iFinDPy 模块未安装，请运行: pip install iFinDAPI")
        return False
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return False
```

- [ ] **Step 2: Commit**

```bash
git add scripts/verify_api.py
git commit -m "fix(Phase1): 清理 verify_api.py 占位符，使用真实 THS 连接"
```

---

## Verification

完整验证命令序列：

```bash
# 1. 运行全部测试
pytest -v

# 2. 验证 CLI 入口（需真实 API 凭证）
python data/fetcher.py 000001 --validate

# 3. 验证数据库内容
python -c "
from data.database import FundDatabase
db = FundDatabase()
fund = db.get_fund('000001')
print('基金信息:', fund)
navs = db.get_nav('000001')
print(f'净值条数: {len(navs)}')
if navs:
    print(f'最新净值: {navs[-1]}')
db.close()
"
```

## Dependency Chain

```
Task 1 (.env.example) → 无依赖，可独立
Task 2 (database.py) → 无依赖
Task 3 (fetcher.py) → 依赖 Task 2 的 FundDatabase 接口；已包含 M2 增量 + M3 校验逻辑
Task 4 (增量测试) → 依赖 Task 3 的 fetch_fund（仅新增测试）
Task 5 (校验测试) → 依赖 Task 3 的 validate_nav_data（仅新增测试）
Task 6 (清理脚本) → 无依赖，可并行
```

建议执行顺序：Task 1, Task 2 → Task 3 → Task 4, Task 5 → Task 6

> **注意**：API 指标名（`fund_name`, `unit_nav`, `fund_portfolio_stockcode` 等）可能需根据实际同花顺 iFinD 的指标字典调整。如果首次运行时 THS_BD 返回空数据或报错，需在 SuperCommand 客户端或工具→指标函数中确认正确的指标名。这是实施阶段需要验证的关键假设。
