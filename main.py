"""China Macro Quant — entry point.

Usage:
    python main.py                    # fetch → store → visualize
    python main.py --no-store         # fetch → visualize only (no DuckDB)
    python main.py --viz-only         # load from DuckDB → visualize
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import DB_PATH, DASHBOARD_PNG, OUTPUT_DIR
from pipeline.fetcher import ChinaMacroSource
from pipeline.storage import MacroStorage
from viz.dashboard import build_dashboard


def main():
    args = set(sys.argv[1:])
    no_store = "--no-store" in args
    viz_only = "--viz-only" in args

    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if viz_only:
        # Load from existing DuckDB
        print("📂 从 DuckDB 加载数据...")
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
        if not no_store:
            print("\n💾 保存到 DuckDB...")
            storage = MacroStorage(DB_PATH)
            storage.save_all(data)
            storage.create_aligned_view()

    # Print summary
    print("\n📋 数据摘要:")
    for name, df in data.items():
        latest = df["date"].iloc[-1].date()
        print(f"  {name}: {len(df)} 条, 最新 {latest}")

    # Visualize
    print("\n🎨 生成可视化...")
    build_dashboard(data, output_png=str(DASHBOARD_PNG))

    print(f"\n🎉 完成！")
    print(f"   静态图: {DASHBOARD_PNG}")
    print(f"   交互图: {DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
