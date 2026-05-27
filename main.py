"""China Macro Quant — entry point.

Multi-country macroeconomic data platform.
Fetches, stores, and visualizes macro data from China, USA, Japan, Korea (TODO).

Usage:
    python main.py                      # all sources
    python main.py --china              # China only (macro + gold)
    python main.py --usa                # USA only (macro + treasury)
    python main.py --japan              # Japan only
    python main.py --viz-only           # visualize from DuckDB (China only)
    python main.py --list               # list available sources
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import VERSION, DB_PATH, DASHBOARD_PNG, OUTPUT_DIR
from pipeline.storage import MacroStorage


def list_sources():
    """List all available data sources."""
    print("\n📋 Available Data Sources:\n")
    sources = [
        ("china.macro", "ChinaMacroSource", "GDP, CPI, PPI, PMI, M2/M1"),
        ("china.gold", "ChinaGoldSource", "SGE Spot Benchmark (Au)"),
        ("china.a_shares", "ChinaAShareSource", "A-Share indices + stocks (AkShare, WAF risk)"),
        ("china.a_daily", "ChinaADailySource", "A-Share daily OHLCV + industry (BaoStock, stable)"),
        ("usa.macro", "USMacroSource", "CPI, Core PCE, Non-farm, Unemployment, ISM, CB Confidence"),
        ("usa.treasury", "USTreasurySource", "US Treasury Index"),
        ("japan.macro", "JapanMacroSource", "CPI, Unemployment Rate, Bank Rate"),
        ("korea.macro", "KoreaMacroSource", "NOT IMPLEMENTED — FRED/KOSIS pending"),
    ]
    for path, name, desc in sources:
        print(f"  {path:<25s} {name:<25s} {desc}")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="china-macro-quant",
        description="Multi-Country Macroeconomic Data Platform v" + VERSION,
        epilog="Data source: AkShare (free, no auth required)",
    )
    parser.add_argument("--china", action="store_true", help="Fetch China data only")
    parser.add_argument("--usa", action="store_true", help="Fetch USA data only")
    parser.add_argument("--japan", action="store_true", help="Fetch Japan data only")
    parser.add_argument("--viz-only", action="store_true", help="Visualize from DuckDB (China only)")
    parser.add_argument("--no-store", action="store_true", help="Fetch without saving to DuckDB")
    parser.add_argument("--list", action="store_true", help="List available data sources")
    parser.add_argument("--show-all", action="store_true", help="Generate all country dashboards")

    args = parser.parse_args()

    if args.list:
        list_sources()
        return

    if args.viz_only:
        # Visualize from DuckDB (China macro only for now)
        print("📂 Loading China macro data from DuckDB...")
        from viz.dashboard import build_dashboard
        storage = MacroStorage(DB_PATH)
        data = {}
        for name in ["gdp", "cpi", "ppi", "pmi", "money_supply"]:
            table = f"china_{name}"
            if table in storage.list_tables():
                data[name] = storage.load_table(table)
        if not data:
            print("  ⚠️  No data found. Run without --viz-only first.")
            return
        build_dashboard(data, output_png=str(DASHBOARD_PNG), version=VERSION)
        return

    # Determine which sources to fetch
    sources = []
    if args.china:
        from pipeline.china.macro import ChinaMacroSource
        from pipeline.china.gold import ChinaGoldSource
        from pipeline.china.a_shares import ChinaAShareSource
        from pipeline.china.a_shares_daily import ChinaADailySource
        sources.append(("china", ChinaMacroSource()))
        sources.append(("china_gold", ChinaGoldSource()))
        sources.append(("china_a_shares", ChinaAShareSource()))
        sources.append(("china_a_daily", ChinaADailySource()))
    elif args.usa:
        from pipeline.usa.macro import USMacroSource
        from pipeline.usa.treasury import USTreasurySource
        sources.append(("usa", USMacroSource()))
        sources.append(("usa_treasury", USTreasurySource()))
    elif args.japan:
        from pipeline.japan.macro import JapanMacroSource
        sources.append(("japan", JapanMacroSource()))
    else:
        # Default: all sources
        from pipeline.china.macro import ChinaMacroSource
        from pipeline.china.gold import ChinaGoldSource
        from pipeline.china.a_shares import ChinaAShareSource
        from pipeline.china.a_shares_daily import ChinaADailySource
        from pipeline.usa.macro import USMacroSource
        from pipeline.usa.treasury import USTreasurySource
        from pipeline.japan.macro import JapanMacroSource
        sources.append(("china", ChinaMacroSource()))
        sources.append(("china_gold", ChinaGoldSource()))
        sources.append(("china_a_shares", ChinaAShareSource()))
        sources.append(("china_a_daily", ChinaADailySource()))
        sources.append(("usa", USMacroSource()))
        sources.append(("usa_treasury", USTreasurySource()))
        sources.append(("japan", JapanMacroSource()))

    # Fetch all
    all_data: dict[str, dict] = {}
    storage = MacroStorage(DB_PATH)

    for prefix, source in sources:
        data = source.fetch_all()
        all_data[prefix] = data
        print(f"\n{source.summary(data)}\n")

        if not args.no_store:
            print(f"💾 Saving {prefix} data to DuckDB...")
            storage.save_all(data, prefix=f"{prefix}_")

    if args.show_all:
        from viz.multi_dashboard import save_all

        print("🎨 Generating all country dashboards from DuckDB...\n")
        tables = storage.list_tables()

        # China
        china_data = {}
        for name in ["gdp", "cpi", "ppi", "pmi", "money_supply"]:
            if f"china_{name}" in tables:
                china_data[name] = storage.load_table(f"china_{name}")
        gold_data = None
        if "china_gold_sge_spot" in tables:
            gold_data = storage.load_table("china_gold_sge_spot")

        # USA
        usa_data = {}
        for name in ["cpi_yoy", "core_pce", "non_farm", "unemployment", "ism_mfg", "treasury_index"]:
            if f"usa_{name}" in tables:
                usa_data[name] = storage.load_table(f"usa_{name}")

        # Japan
        japan_data = {}
        for name in ["cpi", "unemployment", "bank_rate"]:
            if f"japan_{name}" in tables:
                japan_data[name] = storage.load_table(f"japan_{name}")

        save_all(OUTPUT_DIR, VERSION,
                 china_data=china_data, gold_data=gold_data,
                 usa_data=usa_data, japan_data=japan_data)

        print(f"\n🎉 Dashboards saved to: {OUTPUT_DIR}")
        return


if __name__ == "__main__":
    main()
