"""China A-share market data source.

Provides:
- Major A-share indices (Shanghai, Shenzhen, CSI300, etc.) — AkShare `stock_zh_index_daily`
- Representative individual stocks — AkShare `stock_zh_a_hist` (东方财富, WAF throttled)
"""

import akshare as ak
import pandas as pd

from pipeline.base import BaseDataSource, retry


class ChinaAShareSource(BaseDataSource):
    """Fetches A-share index and individual stock data from AkShare."""

    def __init__(self):
        super().__init__("china_ashares", "China A-Share Market Data")

        # Major A-share indices — low WAF risk, high macro value
        self.index_symbols = {
            "sh000001": "SSE Composite",
            "sz399001": "SZSE Component",
            "sz399006": "ChiNext Index",
            "sh000300": "CSI 300",
            "sh000016": "SSE 50",
            "sh000905": "CSI 500",
        }

        # Representative individual stocks (optional, subject to WAF throttling)
        self.stock_symbols = {
            "000001": "Ping An Bank",
            "600519": "Kweichow Moutai",
            "000858": "Wuliangye",
        }

    def fetch_all(
        self,
        start: str = "20200101",
        end: str = "20260601",
        include_stocks: bool = False,
    ) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}

        print("📊 Fetching China A-share data...")

        # ── Indices (primary, WAF-friendly) ──
        print("  📈 Indices:")
        for symbol, desc in self.index_symbols.items():
            print(f"    {symbol} ({desc})...")
            key = f"index_{symbol}"
            results[key] = self._fetch_index(symbol, start, end)

        # ── Individual stocks (optional, WAF risk) ──
        if include_stocks:
            print("  📉 Stocks (东方财富, may throttle):")
            for symbol, desc in self.stock_symbols.items():
                print(f"    {symbol} ({desc})...")
                key = f"stock_{symbol}"
                results[key] = self._fetch_stock(symbol, start, end)

        return results

    # ── Index helpers ──

    def _fetch_index(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Fetch index daily OHLCV via stock_zh_index_daily."""
        df = retry(
            ak.stock_zh_index_daily,
            symbol=symbol,
        )
        df["date"] = pd.to_datetime(df["date"])
        # Filter date range (API returns full history)
        df = df[(df["date"] >= start) & (df["date"] <= end)]
        df = df.rename(columns={
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })
        df["symbol"] = symbol
        return df.sort_values("date").reset_index(drop=True)

    # ── Stock helpers ──

    def _fetch_stock(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Fetch individual stock daily data via stock_zh_a_hist."""
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
