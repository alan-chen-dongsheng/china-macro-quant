"""Data fetcher using AkShare — OOP design with retry logic.

Supports both macro indicators (GDP, CPI, PPI, PMI, M2) and market data (A-shares).
"""

import time
from abc import ABC, abstractmethod
from typing import Any

import akshare as ak
import pandas as pd


def _retry(func, retries=3, delay=2, **kwargs):
    """Retry with exponential backoff for AkShare WAF throttling."""
    for attempt in range(retries):
        try:
            return func(**kwargs)
        except Exception as e:
            if attempt < retries - 1:
                wait = delay * (2 ** attempt)
                print(f"  ⚠️  重试 {attempt+1}/{retries} ({wait}s): {e}")
                time.sleep(wait)
            else:
                raise


def _parse_monthly_date(series: pd.Series) -> pd.Series:
    """Parse '2026年04月份' → 2026-04-01."""
    m = series.str.extract(r"(\d{4})年(\d{1,2})")
    return pd.to_datetime(m[0] + "-" + m[1])


def _parse_quarterly_date(series: pd.Series) -> pd.Series:
    """Parse '2025年第1季度' or '2025年第1-3季度' → 2025-01-01."""
    return pd.to_datetime(series.str.extract(r"(\d{4})")[0])


# ── Abstract Base Class ──────────────────────────────────────────────

class BaseDataSource(ABC):
    """Abstract data source — all fetchers must implement these."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fetch_macro(self) -> dict[str, pd.DataFrame]:
        """Return dict of indicator_name → DataFrame."""
        ...

    @abstractmethod
    def fetch_market(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Return market data DataFrame."""
        ...


# ── China Macro Data Source ─────────────────────────────────────────

class ChinaMacroSource(BaseDataSource):
    """Fetches Chinese macro indicators from AkShare."""

    def __init__(self):
        super().__init__("china_macro")

    def fetch_macro(self) -> dict[str, pd.DataFrame]:
        """Fetch all macro indicators, return dict of DataFrames."""
        results: dict[str, pd.DataFrame] = {}

        print("📊 正在获取宏观数据...")

        print("  GDP...")
        results["gdp"] = self._fetch_gdp()

        print("  CPI...")
        results["cpi"] = self._fetch_cpi()

        print("  PPI...")
        results["ppi"] = self._fetch_ppi()

        print("  PMI...")
        results["pmi"] = self._fetch_pmi()

        print("  货币供应量 (M2/M1/M0)...")
        results["money_supply"] = self._fetch_money_supply()

        return results

    def fetch_market(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Fetch A-share daily data (not typically used for macro analysis)."""
        df = _retry(ak.stock_zh_a_hist, symbol=symbol, period="daily",
                    start_date=start, end_date=end, adjust="qfq")
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
        })[["date", "open", "high", "low", "close", "volume", "amount"]]
        df["date"] = pd.to_datetime(df["date"])
        df["symbol"] = symbol
        return df.sort_values("date").reset_index(drop=True)

    # ── Individual fetchers ──────────────────────────────────────────

    def _fetch_gdp(self) -> pd.DataFrame:
        df = _retry(ak.macro_china_gdp)
        df = df.rename(columns={
            "季度": "date",
            "国内生产总值-绝对值": "gdp",
            "国内生产总值-同比增长": "gdp_yoy",
        })[["date", "gdp", "gdp_yoy"]]
        df["date"] = _parse_quarterly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_cpi(self) -> pd.DataFrame:
        df = _retry(ak.macro_china_cpi)
        df = df.rename(columns={
            "月份": "date",
            "全国-同比增长": "cpi_yoy",
            "全国-环比增长": "cpi_mom",
            "全国-当月": "cpi_index",
        })[["date", "cpi_yoy", "cpi_mom", "cpi_index"]]
        df["date"] = _parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_ppi(self) -> pd.DataFrame:
        df = _retry(ak.macro_china_ppi)
        df = df.rename(columns={
            "月份": "date",
            "当月": "ppi_index",
            "当月同比增长": "ppi_yoy",
        })[["date", "ppi_index", "ppi_yoy"]]
        df["date"] = _parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_pmi(self) -> pd.DataFrame:
        df = _retry(ak.macro_china_pmi)
        df = df.rename(columns={
            "月份": "date",
            "制造业-指数": "pmi_manufacturing",
            "非制造业-指数": "pmi_non_manufacturing",
        })[["date", "pmi_manufacturing", "pmi_non_manufacturing"]]
        df["date"] = _parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_money_supply(self) -> pd.DataFrame:
        df = _retry(ak.macro_china_money_supply)
        df = df.rename(columns={
            "月份": "date",
            "货币和准货币(M2)-数量(亿元)": "m2",
            "货币和准货币(M2)-同比增长": "m2_yoy",
            "货币(M1)-数量(亿元)": "m1",
            "货币(M1)-同比增长": "m1_yoy",
            "流通中的现金(M0)-数量(亿元)": "m0",
        })[["date", "m2", "m2_yoy", "m1", "m1_yoy", "m0"]]
        df["date"] = _parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)
