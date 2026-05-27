"""DuckDB persistence for macro and market data."""

import duckdb
import pandas as pd
from pathlib import Path


class MacroStorage:
    """Stores macro DataFrames in DuckDB, creates aligned views."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def save_all(self, data: dict[str, pd.DataFrame]) -> None:
        """Save each macro indicator as its own table."""
        conn = duckdb.connect(str(self.db_path))
        for name, df in data.items():
            table = f"macro_{name}"
            df_copy = df.copy()
            conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df_copy")
            print(f"  💾 {table}: {len(df)} rows saved")
        conn.close()

    def create_aligned_view(self) -> None:
        """Create macro_wide PIVOT view from all indicator tables.

        Aligns different frequencies (GDP=quarterly, CPI=monthly)
        into a single wide-format view.
        """
        conn = duckdb.connect(str(self.db_path))

        # Discover macro tables
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name LIKE 'macro_%' AND table_name != 'macro_wide'"
        ).fetchdf()["table_name"].tolist()

        if not tables:
            print("  ⚠️  没有宏数据表，跳过视图创建")
            conn.close()
            return

        # Build UNION ALL for long format
        parts = []
        for table in tables:
            cols = conn.execute(f"DESCRIBE {table}").fetchdf()
            for _, row in cols.iterrows():
                col = row["column_name"]
                if col == "date":
                    continue
                parts.append(
                    f"SELECT date, '{table}_{col}' AS indicator, "
                    f"CAST({col} AS DOUBLE) AS value FROM {table}"
                )

        union_sql = " UNION ALL ".join(parts)
        conn.execute(f"CREATE OR REPLACE VIEW macro_long AS {union_sql}")

        # PIVOT to wide format
        indicators = conn.execute(
            "SELECT DISTINCT indicator FROM macro_long ORDER BY indicator"
        ).fetchdf()["indicator"].tolist()

        indicator_list = ", ".join([f"'{i}'" for i in indicators])
        conn.execute(f"""
            CREATE OR REPLACE VIEW macro_wide AS
            SELECT * FROM macro_long
            PIVOT (FIRST(value) FOR indicator IN ({indicator_list}))
            ORDER BY date
        """)

        print(f"  📊 macro_wide 视图已创建 ({len(indicators)} indicators)")
        conn.close()

    def load_wide(self) -> pd.DataFrame:
        """Load the aligned macro_wide view as a DataFrame."""
        conn = duckdb.connect(str(self.db_path))
        df = conn.execute("SELECT * FROM macro_wide").fetchdf()
        conn.close()
        return df

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load a specific macro table."""
        conn = duckdb.connect(str(self.db_path))
        df = conn.execute(f"SELECT * FROM {table_name}").fetchdf()
        conn.close()
        return df
