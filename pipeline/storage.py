"""DuckDB persistence for multi-country macro and market data."""

import duckdb
import pandas as pd
from pathlib import Path


class MacroStorage:
    """Stores data in DuckDB with country-prefixed tables."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def save_all(self, data: dict[str, pd.DataFrame], prefix: str = "") -> None:
        """Save DataFrames as individual tables with optional prefix.

        Args:
            data: dict of name → DataFrame
            prefix: table prefix, e.g. "china_" or "usa_"
        """
        conn = duckdb.connect(str(self.db_path))
        for name, df in data.items():
            table = f"{prefix}{name}" if prefix else name
            df_copy = df.copy()
            conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df_copy")
            print(f"  💾 {table}: {len(df)} rows saved")
        conn.close()

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load a specific table."""
        conn = duckdb.connect(str(self.db_path))
        df = conn.execute(f"SELECT * FROM {table_name}").fetchdf()
        conn.close()
        return df

    def list_tables(self) -> list[str]:
        """List all tables in the database."""
        conn = duckdb.connect(str(self.db_path))
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchdf()["table_name"].tolist()
        conn.close()
        return tables
