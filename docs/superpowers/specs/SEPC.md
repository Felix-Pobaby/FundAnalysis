# 基金竞品分析软件 - 设计规范 (v2)

**日期**: 2026-04-27
**状态**: 评审后修订 (MVP范围)
**版本**: 2.0

## 评审记录

评审意见收集自5个角色的专家评审，涵盖数据工程、金融领域、产品管理、技术架构和用户体验设计。意见文档链接如下：
- [数据工程师评审意见](reviews/DataEngineer.md)
- [金融领域专家评审意见](reviews/FinanceDomainExpert.md)
- [产品经理评审意见](reviews/ProductManager.md)
- [技术架构师评审意见](reviews/TechnicalArchitect.md)
- [UX设计师评审意见](reviews/UXDesigner.md)

基于5个角色的评审意见，本次修订采用 **MVP先行** 策略。以下为决策记录：

| 评审建议 | 决策 | 理由 |
|----------|------|------|
| DuckDB替代SQLite | ✅ 采纳 | 分析场景性能优势明显，从起点避免迁移成本 |
| Brinson业绩归因 | ⏭ 后置 | 算法复杂度高，MVP先跑通基础指标 |
| 基金经理任职期隔离 | ⏭ 后置 | MVP阶段全历史数据足够 |
| AI摘要改为模板化 | ✅ 采纳 | 零幻觉风险，实现成本低 |
| 索提诺/卡玛/滚动胜率 | ⏭ 后置 | 基础指标已覆盖80%场景 |
| 风格漂移分析 | ⏭ 后置 | 需要额外的因子数据支持 |
| PDF改用Playwright | ✅ 采纳 | 避免Windows兼容性问题 |
| Word导出 | ❌ 砍掉 | 排版复杂，HTML+PDF已够用 |
| 极端行情压力测试 | ⏭ 后置 | 需要额外的时间区间标记逻辑 |
| 竞品推荐加权权重 | ✅ 采纳 | 业绩40%+风格30%+类型20%+规模10% |

## 1. 需求概览

### 1.1 产品定位
为基金从业者（专业金融人士）提供公募基金竞品自动化分析工具，覆盖全维度分析、自动竞品推荐、按需生成报告等核心功能。

### 1.2 核心需求
- **数据来源**：同花顺付费终端
- **分析维度**：全维度（业绩指标 + 持仓风格）
- **竞品选择**：自动推荐 + 用户手动确认
- **对比模式**：目标基金 + 竞品群组
- **报告格式**：HTML为主，可导出PDF
- **AI辅助**：模板化摘要生成（零幻觉）
- **数据范围**：全历史回溯，支持趋势分析
- **更新模式**：按需生成，无固定周期
- **部署方式**：本地单用户运行
- **技术栈**：Python全栈（Streamlit + DuckDB）

## 2. 系统架构

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                    │
│  ┌─────────┐ ┌─────────┐ ┌──────────────────┐   │
│  │ 基金选择 │ │ 监控看板 │ │ 报告生成 & 导出   │   │
│  └────┬────┘ └────┬────┘ └────────┬─────────┘   │
│       │           │               │             │
├───────┼───────────┼───────────────┼─────────────┤
│       ▼           ▼               ▼             │
│              Service Layer                        │
│  ┌─────────┐ ┌─────────┐ ┌──────────────────┐   │
│  │竞品推荐  │ │指标计算  │ │报告渲染引擎       │   │
│  └────┬────┘ └────┬────┘ └────────┬─────────┘   │
│       │           │               │             │
├───────┼───────────┼───────────────┼─────────────┤
│       ▼           ▼               ▼             │
│              Data Layer                           │
│  ┌───────────┐ ┌───────────┐ ┌──────────────────┐   │
│  │同花顺API │ │本地DuckDB│ │报告输出文件       │   │
│  └─────────┘ └───────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────┘
```

**数据流向：**
1. 用户选择目标基金 → 同花顺API拉取 → 存入DuckDB
2. 计算业绩指标 → 匹配竞品 → 存入数据库
3. 用户触发报告 → DuckDB读取快照 → 渲染HTML → 导出PDF

## 3. 核心组件

### 3.1 数据获取层 (`data/fetcher.py`)
- `TongHuaShunFetcher` 封装同花顺API调用
- 支持：净值、持仓、基金经理、规模等数据
- 请求频率控制 + 本地缓存 + 时间戳标记
- 指数退避重试机制

### 3.2 竞品推荐引擎 (`analysis/competitor.py`)
- **相似度评分维度与权重：**
  - 业绩表现相关性（收益率曲线相关系数）— **40%**
  - 投资风格相似度（持仓行业分布、市值偏好）— **30%**
  - 基金类型匹配（股票型/混合型/债券型等）— **20%**
  - 规模区间相近 — **10%**
- 输出相似度排名，用户可确认/剔除

### 3.3 指标计算模块 (`analysis/metrics.py`)
- **业绩指标**：收益率（日/周/月/季/年）、年化收益、夏普比率、最大回撤、Alpha、Beta、信息比率
- **风险指标**：波动率、跟踪误差
- **持仓指标**：重仓股、行业配置比例、资产分布
- **排名指标**：同类排名百分位（银河分类）

> ⏭ **后置指标**（v2+）：索提诺比率、卡玛比率、滚动持有胜率、最大回撤修复天数

### 3.4 报告引擎 (`report/generator.py`)
- Jinja2 模板生成 HTML
- Plotly 图表嵌入
- Playwright 导出 PDF
- 模板化AI摘要（基于结构化数据填充，非LLM）

> ❌ **已砍掉**：Word导出

### 3.5 竞品推荐规则细化
- **强制前置过滤**：先匹配投资范围（Benchmark）和二三级分类
- **同公司内部基金剔除**：可选勾选
- **净值跟踪误差**：作为推荐加权补充指标

## 4. 数据模型

### 4.1 DuckDB Schema

```sql
-- 基金基本信息
CREATE TABLE funds (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    manager TEXT,
    company TEXT,
    benchmark TEXT,
    established_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日净值数据
CREATE TABLE nav_history (
    fund_code TEXT REFERENCES funds(code),
    date DATE,
    nav REAL NOT NULL,
    acc_nav REAL NOT NULL,
    PRIMARY KEY (fund_code, date)
);

-- 定期持仓数据
CREATE TABLE holdings (
    fund_code TEXT REFERENCES funds(code),
    report_date DATE,
    stock_code TEXT,
    stock_name TEXT,
    weight REAL,
    PRIMARY KEY (fund_code, report_date, stock_code)
);

-- 业绩指标缓存
CREATE TABLE metrics_cache (
    fund_code TEXT REFERENCES funds(code),
    metric_name TEXT,
    period TEXT,
    value REAL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (fund_code, metric_name, period)
);

-- 监控列表
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_fund TEXT REFERENCES funds(code),
    competitor_fund TEXT REFERENCES funds(code),
    similarity_score REAL,
    confirmed BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 报告历史
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_fund TEXT REFERENCES funds(code),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    html_path TEXT,
    pdf_path TEXT
);

-- 同步日志（增量更新支持）
CREATE TABLE sync_log (
    fund_code TEXT REFERENCES funds(code),
    sync_type TEXT,
    last_update_date DATE,
    data_fingerprint TEXT,
    PRIMARY KEY (fund_code, sync_type)
);
```

**DuckDB选型说明：**
- 向量化查询引擎，百万级行数据分析性能远超SQLite
- 原生支持Parquet，方便后续数据导出和冷备
- 与pandas无缝集成，适合金融计算场景
- 单文件存储，保持本地部署的简洁性

## 5. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 同花顺API超时/限流 | 指数退避重试3次，失败后使用缓存并标记"数据可能过期" |
| 基金代码不存在 | 提示检查输入，建议搜索功能辅助 |
| 数据源返回空值 | 标记"暂无数据"，不影响其他字段 |
| 新基金数据不足 | 跳过该指标计算并说明原因 |
| 相似度评分失败 | 退回到基础维度匹配（类型+规模） |
| 导出PDF失败 | 提示下载HTML，提供排查建议 |
| 净值数据异常（波动>10%或负数） | 标记is_dirty，不进入分析模型 |

## 6. 项目目录结构

```
FundAnalysis/
├── app.py                          # Streamlit 主入口
├── requirements.txt
├── data/
│   ├── fetcher.py                  # 同花顺API封装
│   ├── database.py                 # DuckDB操作
│   └── config.py                   # 配置
├── analysis/
│   ├── competitor.py               # 竞品推荐
│   ├── metrics.py                  # 指标计算
│   └── similarity.py               # 相似度算法
├── report/
│   ├── generator.py                # 报告生成
│   ├── summary_templates.py        # 模板化摘要
│   └── templates/
│       └── fund_report.html        # 报告模板
├── ui/
│   ├── components.py               # 复用组件
│   └── pages/
│       ├── dashboard.py            # 主看板
│       └── report_viewer.py        # 报告查看
├── tests/
│   ├── test_fetcher.py
│   ├── test_competitor.py
│   └── test_metrics.py
└── data/
    └── fund_analysis.db            # DuckDB数据库 (gitignore)
```

## 7. UI设计

### 7.1 主界面 - 三栏布局
- **左栏（20%）**：基金搜索（代码+名称混合搜索）+ 监控列表
- **中栏（55%）**：指标卡片 + Plotly趋势图（默认开启十字准星线）+ 报告生成按钮
- **右栏（25%）**：竞品群组管理（AI推荐确认 + 异动提示）

> UX优化（MVP包含）：
> - 侧边栏可折叠，避免小屏拥挤
> - 异动提示用数值变色，非弹窗
> - 搜索结果显示基金类型和当前净值

### 7.2 报告页面
- **基金概况**：基本信息表格
- **业绩对比**：趋势图 + 竞品数据对比表
- **持仓分析**：行业配置饼图 + 重仓股对比
- **模板化摘要**：基于结构化数据的文字解读 + 风险提示
- **导出**：PDF 按钮（Playwright渲染）

> 报告导出文件名：`[基金代码]_[基金名称]_竞品分析报告_YYYYMMDD.pdf`

## 8. 依赖列表

```
streamlit>=1.30.0
plotly>=5.18.0
jinja2>=3.1.0
playwright>=1.40.0
duckdb>=0.10.0
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0
```

## 9. MVP路线图

### Phase 1: 数据基础设施
- [ ] 同花顺API对接（净值、持仓、基金经理、规模）
- [ ] DuckDB存储 + 增量更新 + 断点续传
- [ ] 数据质量校验（异常值标记）

### Phase 2: 核心分析
- [ ] 业绩指标计算（收益率、夏普、最大回撤、Alpha/Beta）
- [ ] 竞品推荐引擎（加权评分 + 手动确认）
- [ ] 持仓对比（行业配置、重仓股）

### Phase 3: 报告输出
- [ ] Jinja2 HTML报告模板
- [ ] Plotly图表嵌入
- [ ] Playwright PDF导出

### Phase 4: UI优化
- [ ] 三栏布局 + 可折叠侧边栏
- [ ] 模板化摘要生成
- [ ] 报告导出文件名规范化

## 10. 后续版本规划 (v2+)

| 功能 | 版本 | 复杂度 |
|------|------|--------|
| Brinson业绩归因 | v2 | 高 |
| 基金经理任职期隔离 | v2 | 中 |
| 索提诺比率、卡玛比率、滚动胜率 | v2 | 低 |
| 风格漂移分析（风格箱变动图） | v2 | 中 |
| 极端行情压力测试 | v2 | 中 |
| Word导出 | v3 | 高 |
| 多数据源接入（Wind等） | v3 | 高 |
| 云端多用户 | v4 | 高 |
