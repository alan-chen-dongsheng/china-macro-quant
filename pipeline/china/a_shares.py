"""China A-share market data source.

Note: AkShare A-share API (东方财富) has aggressive WAF throttling.
Use retry + caching. For bulk historical data, consider BaoStock fallback.
"""

import akshare as ak
import pandas as pd

from pipeline.base import BaseDataSource, retry


class ChinaAShareSource(BaseDataSource):
    """Fetches A-share daily data from AkShare (东方财富)."""

    def __init__(self):
        super().__init__("china_ashares", "China A-Share Market Data")
        # Major A-share indices / representative stocks
        self.symbols = {
            "000001": "SSE Composite Index (平安银行 as proxy)",
            "600519": "Kweichow Moutai (蓝筹代表)",
            "000858": "Wuliangye (消费代表)",
        }

    def fetch_all(self, start: str = "20200101", end: str = "20260501") -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching China A-share data...")

        for symbol, desc in self.symbols.items():
            print(f"  {symbol} ({desc})...")
            results[f"stock_{symbol}"] = self._fetch_daily(symbol, start, end)

        return results

    def _fetch_daily(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        df = retry(
            ak.stock_zh_a_hist,
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq",
        )
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "pct_change",
            "涨跌额": "change",
            "换手率": "turnover",
        })[["date", "open", "high", "low", "close", "volume", "amount",
             "pct_change", "change", "turnover"]]
        df["date"] = pd.to_datetime(df["date"])
        df["symbol"] = symbol
        return df.sort_values("date").reset_index(drop=True)
