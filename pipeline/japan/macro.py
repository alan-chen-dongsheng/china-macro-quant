"""Japan macro data source — CPI, Unemployment Rate, Bank Rate, etc."""

import time
import akshare as ak
import pandas as pd

from pipeline.base import BaseDataSource, retry, parse_monthly_date


class JapanMacroSource(BaseDataSource):
    """Fetches Japanese macroeconomic indicators from AkShare."""

    def __init__(self):
        super().__init__("japan_macro", "Japan Macroeconomic Indicators")

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching Japan macro data...")

        print("  CPI YoY...")
        results["cpi"] = self._fetch_japan_cpi()
        time.sleep(1)

        print("  Unemployment Rate...")
        results["unemployment"] = self._fetch_japan_unemployment()
        time.sleep(1)

        print("  Bank Rate...")
        results["bank_rate"] = self._fetch_japan_bank_rate()

        return results

    def _fetch_japan_cpi(self) -> pd.DataFrame:
        df = retry(ak.macro_japan_cpi_yearly)
        df = df.rename(columns={
            "时间": "date",
            "现值": "cpi_yoy",
            "前值": "cpi_prev",
        })[["date", "cpi_yoy", "cpi_prev"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_japan_unemployment(self) -> pd.DataFrame:
        df = retry(ak.macro_japan_unemployment_rate)
        df = df.rename(columns={
            "时间": "date",
            "现值": "unemployment_rate",
            "前值": "unemployment_prev",
        })[["date", "unemployment_rate", "unemployment_prev"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_japan_bank_rate(self) -> pd.DataFrame:
        df = retry(ak.macro_japan_bank_rate)
        df = df.rename(columns={
            "时间": "date",
            "现值": "bank_rate",
            "前值": "bank_rate_prev",
        })[["date", "bank_rate", "bank_rate_prev"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)
