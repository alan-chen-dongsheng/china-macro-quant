# China Macro Quant

中国宏观经济 + 量化数据平台 — AkShare 数据获取 → DuckDB 持久化 → Plotly 可视化

## 指标覆盖

| 指标 | 频率 | 说明 |
|------|------|------|
| **GDP** | 季度 | 绝对值 (亿元) + 同比增速 |
| **CPI** | 月度 | 消费者物价指数 同比/环比 |
| **PPI** | 月度 | 生产者物价指数 同比 |
| **PMI** | 月度 | 制造业 & 非制造业 PMI (荣枯线=50) |
| **M2/M1** | 月度 | 货币供应量 同比增速 |

## 架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  AkShare    │────▶│   DuckDB    │────▶│   Plotly    │
│  数据获取    │     │  持久化存储  │     │  可视化     │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 安装

```bash
uv venv && uv pip install -e .
```

## 运行

```bash
# 完整流程: fetch → store → visualize
python main.py

# 仅可视化 (不重新获取数据)
python main.py --viz-only

# 获取 + 可视化 (不存 DuckDB)
python main.py --no-store
```

输出:
- `output/macro_dashboard.png` — 静态高清图片
- `output/macro_dashboard.html` — 可交互图表

## 项目结构

```
china-macro-quant/
├── config.py                 # 路径、指标、日期配置
├── main.py                   # CLI 入口
├── pipeline/
│   ├── fetcher.py            # 数据获取 (OOP: BaseDataSource + ChinaMacroSource)
│   └── storage.py            # DuckDB 持久化 + PIVOT 对齐视图
├── viz/
│   └── dashboard.py          # 4 行仪表盘组装
├── strategy/                  # (预留) 策略模块
├── backtest/                  # (预留) 回测引擎
└── data/
    └── quant.duckdb           # 自动创建 (gitignore)
```

## 数据源

- **AkShare** — 免费、无需注册、覆盖中国 A 股 + 宏观 + 期货
- 内置重试 + 指数退避，应对东方财富 WAF 限速

## 设计要点

- OOP 抽象: `BaseDataSource` 基类，支持扩展 (美股、黄金、加密货币)
- DuckDB: OLAP 引擎，PIVOT 视图对齐不同频率指标
- Plotly: 交互 + 静态双输出，inline 标注最新值
