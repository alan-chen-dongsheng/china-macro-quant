# China Macro Quant

Multi-Country Macroeconomic Data Platform v0.2.0 — AkShare → DuckDB → Plotly

## Data Sources

| Country | Module | Indicators |
|---------|--------|------------|
| 🇨🇳 China Macro | `pipeline.china.macro` | GDP, CPI, PPI, PMI, M2/M1 |
| 🇨🇳 China Gold | `pipeline.china.gold` | SGE Spot Benchmark (Au) |
| 🇨🇳 China A-Shares | `pipeline.china.a_shares` | Daily OHLCV (东方财富) |
| 🇺🇸 USA Macro | `pipeline.usa.macro` | CPI, Core PCE, Non-farm, Unemployment, ISM, CB Confidence |
| 🇺🇸 USA Treasury | `pipeline.usa.treasury` | Treasury Index |
| 🇯🇵 Japan Macro | `pipeline.japan.macro` | CPI, Unemployment Rate, Bank Rate |
| 🇰🇷 Korea Macro | `pipeline.korea.macro` | ⏳ NOT IMPLEMENTED (FRED/KOSIS pending) |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Data Sources   │────▶│     DuckDB      │────▶│   Plotly     │
│  (by country)   │     │  (country_*)    │     │  Dashboard   │
└─────────────────┘     └─────────────────┘     └──────────────┘
  china.macro             china_gdp               4-row dashboard
  china.gold              china_sge_spot
  usa.macro               usa_cpi_yoy
  usa.treasury            usa_treasury_index
  japan.macro             japan_cpi
```

## Quick Start

```bash
uv venv && uv pip install -e .
```

### Fetch all sources
```bash
python main.py
```

### Fetch specific country
```bash
python main.py --china
python main.py --usa
python main.py --japan
```

### Visualize (China macro dashboard)
```bash
# From DuckDB
python main.py --viz-only

# Fetch + visualize
python main.py --china --no-store
```

### List available sources
```bash
python main.py --list
```

### Help
```bash
python main.py -h
```

## Project Structure

```
china-macro-quant/
├── config.py                 # Version, paths, indicator lists
├── main.py                   # CLI entry point (argparse)
├── pyproject.toml            # UV dependencies
├── pipeline/
│   ├── base.py               # BaseDataSource, retry(), date parsers
│   ├── storage.py            # DuckDB persistence (country-prefixed tables)
│   ├── china/
│   │   ├── macro.py          # ChinaMacroSource
│   │   ├── gold.py           # ChinaGoldSource
│   │   └── a_shares.py       # ChinaAShareSource
│   ├── usa/
│   │   ├── macro.py          # USMacroSource
│   │   └── treasury.py       # USTreasurySource
│   ├── japan/
│   │   └── macro.py          # JapanMacroSource
│   └── korea/
│       └── macro.py          # KoreaMacroSource (placeholder)
├── viz/
│   └── dashboard.py          # 4-row China macro dashboard
├── strategy/                  # (reserved)
└── backtest/                  # (reserved)
```

## Design Patterns

- **OOP Data Sources**: `BaseDataSource` abstract class with `fetch_all()` interface
- **Retry with backoff**: All AkShare calls use exponential retry for WAF throttling
- **Country-prefixed tables**: `china_gdp`, `usa_cpi_yoy`, `japan_cpi`, etc.
- **CLI routing**: `--china`, `--usa`, `--japan` flags for selective fetching

## Notes

- **A-Share throttling**: 东方财富 API has aggressive WAF. Use `--china` sparingly, cache results in DuckDB
- **Korea**: AkShare has no Korean macro endpoints. Planned: FRED API integration
- **US Treasury**: Limited endpoints in AkShare. For full yield curve, use `fredapi`
