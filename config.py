"""Configuration — paths, version, symbols, date ranges."""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent

# Version
VERSION = "0.2.0"

# Data storage
DB_PATH = PROJECT_ROOT / "data" / "quant.duckdb"

# Output
OUTPUT_DIR = PROJECT_ROOT / "output"
DASHBOARD_PNG = OUTPUT_DIR / "macro_dashboard.png"

# Date ranges
END_DATE = "20260501"
START_DATE = "20200101"

# China macro indicators
CHINA_MACRO = ["gdp", "cpi", "ppi", "pmi", "money_supply"]

# US macro indicators
US_MACRO = ["cpi_yoy", "core_pce", "non_farm", "unemployment", "ism_mfg", "consumer_confidence"]

# Japan macro indicators
JAPAN_MACRO = ["cpi", "unemployment", "bank_rate"]
