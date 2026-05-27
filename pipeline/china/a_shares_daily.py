"""China A-share market data — BaoStock backend.

Provides:
- Individual stock daily K-lines (OHLCV + valuation) via BaoStock
- Industry classification (CSRC 证监会行业分类, static dimension table)
- Full A-share stock universe listing

Why BaoStock: AkShare's 东方财富 WAF throttles aggressively from overseas IPs.
BaoStock is free, no auth required, and stable from境外 servers.

Usage:
    source = ChinaADailySource()

    # 1. Full stock universe + industry (one-shot, fast)
    data = source.fetch_all(include_daily=False)

    # 2. Daily K-lines for specific stocks
    data = source.fetch_all(
        codes=["000001", "600519", "000858"],  # Ping An, Moutai, Wuliangye
        start_date="2024-01-01", end_date="2026-05-27",
    )

    # 3. Industry + daily K-lines
    data = source.fetch_all(
        codes=["000001", "600519"],
        start_date="2025-01-01", end_date="2026-05-27",
        include_industry=True,
    )
"""

import time
import pandas as pd
import baostock as bs

from pipeline.base import BaseDataSource


class ChinaADailySource(BaseDataSource):
    """Fetches A-share daily market data from BaoStock."""

    def __init__(self):
        super().__init__(
            "china_a_daily",
            "China A-Share Daily Market Data (BaoStock)",
        )
        # Default: major A-share representative stocks
        self.default_codes = {
            "000001": "平安银行",
            "600519": "贵州茅台",
            "000858": "五粮液",
            "600036": "招商银行",
            "000333": "美的集团",
            "601318": "中国平安",
            "600276": "恒瑞医药",
            "300750": "宁德时代",
            "002594": "比亚迪",
            "601899": "紫金矿业",
        }

    def _login(self):
        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"BaoStock login failed: {lg.error_msg}")

    @staticmethod
    def _logout():
        try:
            bs.logout()
        except Exception:
            pass

    # ── Public API ──

    def fetch_all(
        self,
        codes: list[str] = None,
        start_date: str = "20240101",
        end_date: str = None,
        include_industry: bool = True,
        include_universe: bool = True,
        include_daily: bool = True,
        sleep_sec: float = 0.15,
    ) -> dict[str, pd.DataFrame]:
        """Fetch A-share market data.

        Args:
            codes: List of stock codes (without exchange prefix).
                   Defaults to representative stocks.
            start_date: Start date for daily K-lines (YYYYMMDD or YYYY-MM-DD).
            end_date: End date (default: today).
            include_industry: Fetch industry classification table.
            include_universe: Fetch full A-share stock listing.
            include_daily: Fetch daily K-lines for specified codes.
            sleep_sec: Pause between per-stock requests.

        Returns:
            Dict with keys: 'universe', 'industry', 'daily' (as requested).
        """
        results: dict[str, pd.DataFrame] = {}

        if end_date is None:
            end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

        start_date = start_date.replace("/", "-")
        end_date = end_date.replace("/", "-")
        # Ensure YYYY-MM-DD format
        if len(start_date) == 8:
            start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        if len(end_date) == 8:
            end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

        self._login()

        try:
            # ── Stock universe (static, one request) ──
            if include_universe:
                results["universe"] = self._fetch_universe()

            # ── Industry classification (static, one request) ──
            if include_industry:
                results["industry"] = self._fetch_industry()

            # ── Daily K-lines (per-stock, rate-limited) ──
            if include_daily:
                target_codes = codes or list(self.default_codes.keys())
                results["daily"] = self._fetch_daily_klines(
                    target_codes, start_date, end_date, sleep_sec,
                )

        finally:
            self._logout()

        return results

    # ── Internal helpers ──

    def _fetch_universe(self) -> pd.DataFrame:
        """Fetch full A-share stock universe."""
        rs = bs.query_stock_basic()
        df = rs.get_data()

        if df.empty:
            return df

        # Filter to A-share stocks
        df = df[df["code"].str.match(r"^(sh|sz)\.[036]")].copy()
        df["symbol"] = df["code"].str.replace(r"^(sh|sz)\.", "", regex=True)
        return df.sort_values("symbol").reset_index(drop=True)

    def _fetch_industry(self) -> pd.DataFrame:
        """Fetch industry classification for all A-share stocks."""
        rs = bs.query_stock_industry()
        df = rs.get_data()

        if df.empty:
            return df

        df["symbol"] = df["code"].str.replace(r"^(sh|sz)\.", "", regex=True)
        df = df[df["industry"] != ""].copy()
        df["updateDate"] = pd.to_datetime(df["updateDate"])
        return df.sort_values("symbol").reset_index(drop=True)

    def _fetch_daily_klines(
        self,
        codes: list[str],
        start_date: str,
        end_date: str,
        sleep_sec: float,
    ) -> pd.DataFrame:
        """Fetch daily K-lines for a list of stock codes."""
        fields = (
            "date,code,open,high,low,close,preclose,volume,amount,"
            "pctChg,turn,peTTM,pbMRQ"
        )
        all_rows: list[pd.DataFrame] = []

        for i, code in enumerate(codes):
            # Add exchange prefix if missing
            bs_code = code if "." in code else self._add_prefix(code)

            rs = bs.query_history_k_data_plus(
                bs_code,
                fields=fields,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3",  # 前复权
            )
            df = rs.get_data()

            if not df.empty:
                # Normalize code (remove exchange prefix)
                df["symbol"] = df["code"].str.replace(r"^(sh|sz)\.", "", regex=True)

                # Type conversions
                for col in ["open", "high", "low", "close", "preclose",
                            "peTTM", "pbMRQ"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                for col in ["volume", "amount", "pctChg", "turn"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                df["date"] = pd.to_datetime(df["date"])
                all_rows.append(df)

            status = "✓" if not df.empty else "✗"
            print(f"    [{i+1}/{len(codes)}] {status} {code}: {len(df)} rows")

            if i < len(codes) - 1:
                time.sleep(sleep_sec)

        if all_rows:
            return pd.concat(all_rows, ignore_index=True).sort_values(
                ["date", "symbol"]
            ).reset_index(drop=True)

        return pd.DataFrame()

    @staticmethod
    def _add_prefix(code: str) -> str:
        """Add exchange prefix to stock code."""
        if code.startswith("6"):
            return f"sh.{code}"
        elif code.startswith(("0", "3")):
            return f"sz.{code}"
        return code

    def summary(self, data: dict[str, pd.DataFrame]) -> str:
        """Return a summary string of all data."""
        lines = [f"📊 {self.name} ({self.description})"]
        for name, df in data.items():
            if df.empty:
                lines.append(f"  {name}: 0 rows")
            elif "date" in df.columns:
                latest = df["date"].iloc[-1]
                lines.append(f"  {name}: {len(df)} rows, latest {pd.Timestamp(latest).date()}")
            else:
                lines.append(f"  {name}: {len(df)} rows (static)")
        return "\n".join(lines)
