"""China gold data source — Shanghai Gold Exchange spot prices."""

import akshare as ak
import pandas as pd

from pipeline.base import BaseDataSource, retry


class ChinaGoldSource(BaseDataSource):
    """Fetches SGE (Shanghai Gold Exchange) spot benchmark prices."""

    def __init__(self):
        super().__init__("china_gold", "Shanghai Gold Exchange Spot Prices")

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching China gold data...")
        print("  SGE spot benchmark...")
        results["sge_spot"] = self._fetch_sge_spot()

        return results

    def _fetch_sge_spot(self) -> pd.DataFrame:
        df = retry(ak.spot_golden_benchmark_sge)
        df = df.rename(columns={
            "交易时间": "date",
            "晚盘价": "sge_evening",
            "早盘价": "sge_morning",
        })[["date", "sge_evening", "sge_morning"]]
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)
