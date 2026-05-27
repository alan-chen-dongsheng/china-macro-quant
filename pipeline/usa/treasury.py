"""US Treasury data source — yield curve and bond indices."""

import akshare as ak
import pandas as pd

from pipeline.base import BaseDataSource, retry


class USTreasurySource(BaseDataSource):
    """Fetches US Treasury yield data."""

    def __init__(self):
        super().__init__("usa_treasury", "US Treasury Yield Data")

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching US Treasury data...")
        print("  Treasury index...")
        results["treasury_index"] = self._fetch_treasury_index()

        print("  10Y yield (via FRED proxy)...")
        results["yield_10y"] = self._fetch_yield_10y()

        return results

    def _fetch_treasury_index(self) -> pd.DataFrame:
        """US Treasury bond index (中债国债)."""
        df = retry(ak.bond_treasury_index_cbond)
        df = df.rename(columns={"date": "date", "value": "treasury_index"})
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    def _fetch_yield_10y(self) -> pd.DataFrame:
        """US 10Y Treasury yield via AkShare.

        Note: AkShare doesn't have a direct US Treasury yield endpoint.
        This uses the treasury index as a proxy.
        For actual yield curve data, consider fredapi as a fallback.
        """
        df = self._fetch_treasury_index()
        df = df.rename(columns={"treasury_index": "yield_10y_proxy"})
        return df
