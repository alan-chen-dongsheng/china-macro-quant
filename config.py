"""Configuration — paths, symbols, date ranges."""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent

# Data storage
DB_PATH = PROJECT_ROOT / "data" / "quant.duckdb"

# Output
OUTPUT_DIR = PROJECT_ROOT / "output"
DASHBOARD_PNG = OUTPUT_DIR / "macro_dashboard.png"
DASHBOARD_HTML = OUTPUT_DIR / "macro_dashboard.html"

# Date ranges
END_DATE = "20260501"
START_DATE = "20200101"

# Macro indicators to fetch
MACRO_INDICATORS = ["gdp", "cpi", "ppi", "pmi", "money_supply"]
