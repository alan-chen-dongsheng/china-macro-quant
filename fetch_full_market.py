"""Fetch full-market daily returns for all A-share stocks via BaoStock.

This is a one-shot data fetch — queries BaoStock for the last N trading days
for every stock in the industry table. Results are stored in DuckDB.

Usage:
    python fetch_full_market.py --days 5 --sleep 0.05
"""

import argparse
import time
import datetime
import pandas as pd
import baostock as bs
import duckdb
from pathlib import Path

DB_PATH = "data/quant.duckdb"


def get_trading_dates(start: str, end: str) -> list[str]:
    """Get list of trading dates."""
    lg = bs.login()
    rs = bs.query_trade_dates(start_date=start, end_date=end)
    df = rs.get_data()
    bs.logout()
    trading = df[df["is_trading_day"] == 1]["calendar_date"].tolist()
    return trading


def fetch_all_stocks_daily(
    start_date: str,
    end_date: str,
    sleep_sec: float = 0.05,
) -> pd.DataFrame:
    """Fetch daily K-lines for ALL A-share stocks in the industry table."""
    lg = bs.login()

    # Get all stocks with industry classification
    rs_ind = bs.query_stock_industry()
    ind_df = rs_ind.get_data()
    ind_df = ind_df[ind_df["industry"] != ""]
    all_codes = ind_df["code"].tolist()

    print(f"Fetching daily data for {len(all_codes)} stocks ({start_date} → {end_date})...", flush=True)

    fields = "date,code,close,pctChg"
    all_rows: list[pd.DataFrame] = []

    for i, code in enumerate(all_codes):
        rs = bs.query_history_k_data_plus(
            code,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3",
        )
        df = rs.get_data()
        if not df.empty:
            all_rows.append(df)

        if (i + 1) % 500 == 0:
            print(f"  [{i+1}/{len(all_codes)}] {len(all_rows)} stocks fetched...", flush=True)

        if i < len(all_codes) - 1:
            time.sleep(sleep_sec)

    bs.logout()

    if all_rows:
        result = pd.concat(all_rows, ignore_index=True)
        result["symbol"] = result["code"].str.replace(r"^(sh|sz)\.", "", regex=True)
        result["date"] = pd.to_datetime(result["date"])
        for col in ["close", "pctChg"]:
            result[col] = pd.to_numeric(result[col], errors="coerce")
        return result[["date", "symbol", "close", "pctChg"]]

    return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=5, help="Trading days to fetch")
    parser.add_argument("--sleep", type=float, default=0.03, help="Sleep between requests")
    parser.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    # BaoStock has data through 2026-05-26 but query_trade_dates doesn't cover it
    # Use hard-coded date range
    end_date = args.end or "2026-05-26"
    if args.start:
        lookback_start = args.start
    else:
        # Go back ~10 calendar days to ensure we get N trading days
        from datetime import timedelta
        end_dt = pd.Timestamp(end_date)
        lookback_start = (end_dt - timedelta(days=args.days * 3)).strftime("%Y-%m-%d")

    print(f"Fetching daily data: {lookback_start} → {end_date}", flush=True)

    df = fetch_all_stocks_daily(lookback_start, end_date, args.sleep)

    if df.empty:
        print("No data fetched.", flush=True)
        return

    # Save to DuckDB
    db = duckdb.connect(DB_PATH)
    db.execute("CREATE OR REPLACE TABLE china_a_full_daily AS SELECT * FROM df")
    count = db.execute("SELECT COUNT(*) FROM china_a_full_daily").fetchone()[0]
    db.close()

    print(f"\n✅ Saved {count} rows to china_a_full_daily", flush=True)


if __name__ == "__main__":
    main()
