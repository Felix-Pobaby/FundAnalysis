# FundAnalysis 里程碑拆分设计

**日期**: 2026-04-28
**状态**: 待确认
**版本**: 1.0

## 拆分原则

每个里程碑必须满足**可运行、可演示、可验收**三个标准：
- **可运行**：有明确的入口命令或脚本可以执行
- **可演示**：能展示具体功能效果
- **可验收**：有明确的验收标准，不依赖主观判断

---

## Phase 0: 前置环境准备

> 目标：消除所有后续开发的阻塞点，建立可立即开始编码的基础设施

| # | 内容 | 可运行 | 可演示 | 验收标准 |
|---|------|--------|--------|----------|
| M0.1 | `.env` / `.env.example` | - | 查看文件结构 | `.env.example` 包含所有必要占位符 |
| M0.2 | 同花顺 API 账号/token 准备 | - | - | 账号密码/token 已获取并存入 `.env` |
| M0.3 | 工程目录结构脚手架 | `ls` 检查 | 查看目录树 | 与 SEPC.md 第6节目录结构一致 |
| M0.4 | Python 虚拟环境 + 依赖安装 | `python -m venv` + `pip install` | `python -c "import streamlit"` | 所有依赖可导入，无报错 |
| M0.5 | bash/powershell 脚本工具 | 运行脚本 | 执行 `setup.sh` / `setup.ps1` | 一键完成 M0.2-M0.4 |
| M0.6 | API 连通性验证脚本 | `python scripts/verify_api.py` | 输出"连接成功" | 认证通过，网络可达，数据可拉取 |
| M0.7 | 配置管理模块 | `python -c "from data.config import settings"` | 查看配置值 | 数据库路径、API端点、超时等集中管理 |
| M0.8 | 测试基础设施 | `pytest` | 看到 `conftest.py` fixtures | 可运行至少一个基础测试，有 mock 框架 |
| M0.9 | Playwright 浏览器安装 | `playwright install` | 浏览器二进制文件存在 | PDF 导出所需的浏览器环境就绪 |

---

## Phase 1: 数据基础设施（M1-M3）

### M1: 数据库 + 基础数据获取

**入口**: `python data/fetcher.py <fund_code>`

**功能**:
- 创建 DuckDB 及全部 7 张表（funds, nav_history, holdings, metrics_cache, watchlist, reports, sync_log）
- 拉取单只基金的净值、持仓、基金经理、规模数据
- 写入数据库

**验收标准**:
- 查询 `funds` 表能看到基金基本信息
- 查询 `nav_history` 表有净值数据
- `sync_log` 有同步记录

### M2: 增量更新 + 断点续传

**入口**: `python data/fetcher.py <fund_code>`（第二次运行）

**功能**:
- 读取 `sync_log.last_update_date`，只拉取增量数据
- 更新 `sync_log` 记录

**验收标准**:
- 第二次运行时间显著缩短（< 5秒）
- 数据不重复，增量部分正确入库

### M3: 数据质量校验

**入口**: `python data/fetcher.py --validate <fund_code>`

**功能**:
- 检测异常净值（负数、单日波动>10%）
- 标记脏数据（`is_dirty` 字段）
- 脏数据不进入分析模型

**验收标准**:
- 注入异常数据后，`is_dirty=1`
- 正常数据不受影响

---

## Phase 2: 核心分析（M4-M6）

### M4: 业绩指标计算

**入口**: `python analysis/metrics.py <fund_code>`

**功能**:
- 计算：收益率（日/周/月/季/年）、年化收益、夏普比率、最大回撤、Alpha、Beta、信息比率、波动率、跟踪误差
- 结果写入 `metrics_cache`

**验收标准**:
- 计算结果与手动计算一致（误差<1%）
- 多只基金可批量计算

### M5: 竞品推荐引擎

**入口**: `python analysis/competitor.py <fund_code>`

**功能**:
- 相似度评分：业绩40% + 风格30% + 类型20% + 规模10%
- 强制前置过滤：Benchmark匹配 + 二三级分类匹配
- 输出 Top-N 竞品列表及相似度评分

**验收标准**:
- 推荐结果符合金融常识（同类基金排名靠前）
- 同公司内部基金可勾选剔除

### M6: 持仓对比

**入口**: `python analysis/metrics.py --compare <fund_code1> <fund_code2>`

**功能**:
- 重仓股重叠度分析
- 行业配置差异对比
- 资产分布对比

**验收标准**:
- 能正确识别共同持仓股
- 行业配置差异百分比正确

---

## Phase 3: 报告输出（M7-M8）

### M7: HTML报告生成

**入口**: `python report/generator.py <fund_code> --competitors <code1> <code2>`

**功能**:
- Jinja2 模板生成 HTML
- 包含：基金概况、业绩对比、持仓分析、模板化摘要
- 嵌入 Plotly 交互图表

**验收标准**:
- HTML 文件可在浏览器打开
- 图表可交互（十字准星、缩放）

### M8: PDF导出

**入口**: `python report/generator.py <fund_code> --export-pdf`

**功能**:
- Playwright 渲染 HTML → PDF
- 文件名格式：`[基金代码]_[基金名称]_竞品分析报告_YYYYMMDD.pdf`

**验收标准**:
- PDF 排版完整，图表正常渲染
- 文件名格式正确

---

## Phase 4: UI优化（M9-M10）

### M9: Streamlit三栏布局

**入口**: `streamlit run app.py`

**功能**:
- 左栏（20%）：基金搜索（代码+名称混合）+ 监控列表
- 中栏（55%）：指标卡片 + Plotly趋势图 + 报告生成按钮
- 右栏（25%）：竞品群组管理（AI推荐确认 + 异动提示）
- 侧边栏可折叠
- 异动用数值变色显示

**验收标准**:
- 三栏布局正确渲染
- 搜索支持代码+名称，显示基金类型和当前净值
- 侧边栏可折叠

### M10: 报告查看 + 导出集成

**入口**: `streamlit run app.py` → UI操作

**功能**:
- UI中点击按钮生成报告
- 模板化摘要显示
- 导出PDF，文件名规范化

**验收标准**:
- 端到端流程完整：选择基金 → 确认竞品 → 生成报告 → 导出PDF
- 所有交互无报错

---

## 里程碑依赖关系

```
Phase 0: M0.1 → M0.3 → M0.4 → M0.5 → M0.6 → M0.7 → M0.8 → M0.9 (部分可并行)
Phase 1: M1 → M2 → M3
Phase 2: M1完成 → M4, M5, M6 (M5依赖M4的部分结果)
Phase 3: M4, M5, M6完成 → M7 → M8
Phase 4: M7, M8完成 → M9 → M10
```

## 后续版本 (v2+)

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
