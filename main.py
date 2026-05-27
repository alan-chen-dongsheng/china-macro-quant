"""China Macro Quant — entry point.

China Macroeconomic Data Platform
Fetches GDP, CPI, PPI, PMI, M2 data via AkShare,
stores in DuckDB, and generates Plotly dashboards.

Usage:
    python main.py                    # fetch → store → visualize
    python main.py --no-store         # fetch → visualize only (no DuckDB)
    python main.py --viz-only         # load from DuckDB → visualize
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import VERSION, DB_PATH, DASHBOARD_PNG, OUTPUT_DIR
from pipeline.fetcher import ChinaMacroSource
from pipeline.storage import MacroStorage
from viz.dashboard import build_dashboard


def main():
    parser = argparse.ArgumentParser(
        prog="china-macro-quant",
        description="China Macroeconomic Data Platform — Fetch, store, and visualize key economic indicators.",
        epilog="Data source: AkShare (free, no auth required)"
    )
    parser.add_argument("--no-store", action="store_true",
                        help="Fetch and visualize without saving to DuckDB")
    parser.add_argument("--viz-only", action="store_true",
                        help="Visualize using existing data in DuckDB")
    
    args = parser.parse_args()

    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.viz_only:
        # Load from existing DuckDB
        print("📂 Loading data from DuckDB...")
        storage = MacroStorage(DB_PATH)
        data = {}
        for name in ["gdp", "cpi", "ppi", "pmi", "money_supply"]:
            table = f"macro_{name}"
            data[name] = storage.load_table(table)
    else:
        # Fetch fresh data
        source = ChinaMacroSource()
        data = source.fetch_macro()

        # Store in DuckDB
        if not args.no_store:
            print("\n💾 Saving to DuckDB...")
            storage = MacroStorage(DB_PATH)
            storage.save_all(data)
            storage.create_aligned_view()

    # Print summary
    print("\n📋 Data Summary:")
    for name, df in data.items():
        latest = df["date"].iloc[-1].date()
        print(f"  {name}: {len(df)} rows, latest {latest}")

    # Visualize
    print(f"\n🎨 Generating Dashboard v{VERSION}...")
    build_dashboard(data, output_png=str(DASHBOARD_PNG), version=VERSION)

    html_path = str(DASHBOARD_PNG).replace(".png", ".html")
    print(f"\n🎉 Done!")
    print(f"   Static: {DASHBOARD_PNG}")
    print(f"   Interactive: {html_path}")


if __name__ == "__main__":
    main()
