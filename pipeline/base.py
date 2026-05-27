"""Base data source abstraction for all macro/market data fetchers."""

import time
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


def retry(func, retries=3, delay=2, **kwargs):
    """Retry with exponential backoff for API throttling."""
    for attempt in range(retries):
        try:
            return func(**kwargs)
        except Exception as e:
            if attempt < retries - 1:
                wait = delay * (2 ** attempt)
                print(f"  ⚠️  retry {attempt+1}/{retries} ({wait}s): {e}")
                time.sleep(wait)
            else:
                raise


def parse_monthly_date(series: pd.Series) -> pd.Series:
    """Parse '2026年04月份' or '2026年04月' → 2026-04-01."""
    m = series.str.extract(r"(\d{4})[年/](\d{1,2})")
    return pd.to_datetime(m[0] + "-" + m[1])


def parse_quarterly_date(series: pd.Series) -> pd.Series:
    """Parse '2025年第1季度' → 2025-01-01."""
    return pd.to_datetime(series.str.extract(r"(\d{4})")[0])


class BaseDataSource(ABC):
    """Abstract base for all data sources."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    def fetch_all(self) -> dict[str, pd.DataFrame]:
        """Fetch all data for this source, return dict of name → DataFrame."""
        ...

    def summary(self, data: dict[str, pd.DataFrame]) -> str:
        """Return a summary string of all data."""
        lines = [f"📊 {self.name} ({self.description})"]
        for name, df in data.items():
            latest = df["date"].iloc[-1].date()
            lines.append(f"  {name}: {len(df)} rows, latest {latest}")
        return "\n".join(lines)
