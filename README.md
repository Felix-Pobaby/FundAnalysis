# FundAnalysis — 基金竞品分析工具

为基金从业者提供公募基金竞品自动化分析，覆盖全维度分析、自动竞品推荐、按需生成报告。

## 快速开始

```bash
pip install -r requirements.txt
playwright install        # PDF导出需要
streamlit run app.py
```

## 测试

```bash
pytest                    # 全部测试
pytest tests/test_fetcher.py  # 单个测试
```

## 完整文档

详细架构、数据模型、UI设计、错误处理和MVP路线图见 [SEPC.md](docs/superpowers/specs/SEPC.md)。
