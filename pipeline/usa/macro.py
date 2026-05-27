"""USA macro data source — CPI, PCE, Non-farm, Unemployment, ISM, etc."""

import time
import akshare as ak
import pandas as pd

from pipeline.base import BaseDataSource, retry


class USMacroSource(BaseDataSource):
    """Fetches US macroeconomic indicators from AkShare."""

    def __init__(self):
        super().__init__("usa_macro", "US Macroeconomic Indicators")

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching US macro data...")

        print("  CPI YoY...")
        results["cpi_yoy"] = self._fetch_us_cpi_yoy()
        time.sleep(1)

        print("  Core PCE...")
        results["core_pce"] = self._fetch_us_core_pce()
        time.sleep(1)

        print("  Non-farm Payrolls...")
        results["non_farm"] = self._fetch_us_non_farm()
        time.sleep(1)

        print("  Unemployment Rate...")
        results["unemployment"] = self._fetch_us_unemployment()
        time.sleep(1)

        print("  ISM Manufacturing...")
        results["ism_mfg"] = self._fetch_us_ism_mfg()
        time.sleep(1)

        print("  Consumer Confidence...")
        results["consumer_confidence"] = self._fetch_us_cb_confidence()

        return results

    def _parse_date(self, df: pd.DataFrame, col: str = "日期") -> pd.DataFrame:
        """Standardize date column."""
        df = df.rename(columns={col: "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df

    def _fetch_us_cpi_yoy(self) -> pd.DataFrame:
        df = retry(ak.macro_usa_cpi_yoy)
        df = df.rename(columns={"时间": "date", "现值": "cpi_yoy", "前值": "cpi_prev"})[
            ["date", "cpi_yoy", "cpi_prev"]
        ]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_us_core_pce(self) -> pd.DataFrame:
        df = retry(ak.macro_usa_core_pce_price)
        df = df.rename(columns={
            "日期": "date",
            "今值": "core_pce",
            "预测值": "core_pce_forecast",
            "前值": "core_pce_prev",
        })[["date", "core_pce", "core_pce_forecast", "core_pce_prev"]]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_us_non_farm(self) -> pd.DataFrame:
        df = retry(ak.macro_usa_non_farm)
        df = df.rename(columns={
            "日期": "date",
            "今值": "non_farm",
            "预测值": "non_farm_forecast",
            "前值": "non_farm_prev",
        })[["date", "non_farm", "non_farm_forecast", "non_farm_prev"]]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_us_unemployment(self) -> pd.DataFrame:
        df = retry(ak.macro_usa_unemployment_rate)
        df = df.rename(columns={
            "日期": "date",
            "今值": "unemployment_rate",
            "预测值": "unemployment_forecast",
            "前值": "unemployment_prev",
        })[["date", "unemployment_rate", "unemployment_forecast", "unemployment_prev"]]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_us_ism_mfg(self) -> pd.DataFrame:
        """ISM Manufacturing PMI."""
        df = retry(ak.macro_usa_ism_pmi)
        df = df.rename(columns={
            "日期": "date",
            "今值": "ism_pmi",
            "预测值": "ism_pmi_forecast",
            "前值": "ism_pmi_prev",
        })[["date", "ism_pmi", "ism_pmi_forecast", "ism_pmi_prev"]]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_us_cb_confidence(self) -> pd.DataFrame:
        """Conference Board Consumer Confidence."""
        df = retry(ak.macro_usa_cb_consumer_confidence)
        df = df.rename(columns={
            "日期": "date",
            "今值": "cb_confidence",
            "预测值": "cb_confidence_forecast",
            "前值": "cb_confidence_prev",
        })[["date", "cb_confidence", "cb_confidence_forecast", "cb_confidence_prev"]]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)
