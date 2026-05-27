"""China macro data source — GDP, CPI, PPI, PMI, M2/M1."""

import akshare as ak
import pandas as pd

from pipeline.base import (
    BaseDataSource, retry,
    parse_monthly_date, parse_quarterly_date,
)


class ChinaMacroSource(BaseDataSource):
    """Fetches Chinese macro indicators from AkShare."""

    def __init__(self):
        super().__init__("china_macro", "China Macroeconomic Indicators")

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching China macro data...")

        print("  GDP...")
        results["gdp"] = self._fetch_gdp()

        print("  CPI...")
        results["cpi"] = self._fetch_cpi()

        print("  PPI...")
        results["ppi"] = self._fetch_ppi()

        print("  PMI...")
        results["pmi"] = self._fetch_pmi()

        print("  Money Supply (M2/M1)...")
        results["money_supply"] = self._fetch_money_supply()

        return results

    def _fetch_gdp(self) -> pd.DataFrame:
        df = retry(ak.macro_china_gdp)
        df = df.rename(columns={
            "季度": "date",
            "国内生产总值-绝对值": "gdp",
            "国内生产总值-同比增长": "gdp_yoy",
        })[["date", "gdp", "gdp_yoy"]]
        df["date"] = parse_quarterly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_cpi(self) -> pd.DataFrame:
        df = retry(ak.macro_china_cpi)
        df = df.rename(columns={
            "月份": "date",
            "全国-同比增长": "cpi_yoy",
            "全国-环比增长": "cpi_mom",
            "全国-当月": "cpi_index",
        })[["date", "cpi_yoy", "cpi_mom", "cpi_index"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_ppi(self) -> pd.DataFrame:
        df = retry(ak.macro_china_ppi)
        df = df.rename(columns={
            "月份": "date",
            "当月": "ppi_index",
            "当月同比增长": "ppi_yoy",
        })[["date", "ppi_index", "ppi_yoy"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_pmi(self) -> pd.DataFrame:
        df = retry(ak.macro_china_pmi)
        df = df.rename(columns={
            "月份": "date",
            "制造业-指数": "pmi_manufacturing",
            "非制造业-指数": "pmi_non_manufacturing",
        })[["date", "pmi_manufacturing", "pmi_non_manufacturing"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_money_supply(self) -> pd.DataFrame:
        df = retry(ak.macro_china_money_supply)
        df = df.rename(columns={
            "月份": "date",
            "货币和准货币(M2)-数量(亿元)": "m2",
            "货币和准货币(M2)-同比增长": "m2_yoy",
            "货币(M1)-数量(亿元)": "m1",
            "货币(M1)-同比增长": "m1_yoy",
            "流通中的现金(M0)-数量(亿元)": "m0",
        })[["date", "m2", "m2_yoy", "m1", "m1_yoy", "m0"]]
        df["date"] = parse_monthly_date(df["date"])
        return df.sort_values("date").reset_index(drop=True)
