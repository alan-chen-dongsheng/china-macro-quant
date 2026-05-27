"""Korea macro data source — placeholder.

Note: AkShare does NOT have direct Korean macro data endpoints.
Future implementation options:
  1. FRED API (fredapi) — CPI, unemployment, GDP for Korea
  2. yfinance — KOSPI index as proxy
  3. Korean statistical office API (KOSIS)

Current: returns empty dict with warning.
"""

import pandas as pd

from pipeline.base import BaseDataSource


class KoreaMacroSource(BaseDataSource):
    """Placeholder for Korean macroeconomic indicators.

    AkShare has no Korean macro data. This class exists as a stub
    for future implementation via FRED or other sources.
    """

    def __init__(self):
        super().__init__(
            "korea_macro",
            "Korea Macroeconomic Indicators (NOT IMPLEMENTED)",
        )

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        print("⚠️  Korea macro data: NOT YET IMPLEMENTED")
        print("  AkShare has no Korean macro endpoints.")
        print("  Future: FRED API or KOSIS integration.")
        return {}
