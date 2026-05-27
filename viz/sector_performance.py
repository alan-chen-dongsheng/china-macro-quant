"""A-share sector performance chart — per-stock returns colored by industry."""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

from pipeline.storage import MacroStorage


def build_sector_performance(
    db_path: str,
    lookback_days: int = 5,
    output_png: str = None,
    output_html: str = None,
    version: str = "0.2.0",
) -> go.Figure:
    """Build a sector performance bar chart showing recent stock returns.

    For each stock, compute cumulative return over the last N trading days.
    Bars are colored by industry and sorted by return.

    Args:
        db_path: Path to the DuckDB database.
        lookback_days: Number of recent trading days to analyze.
        output_png: Optional output PNG path.
        output_html: Optional output HTML path.
        version: Project version.

    Returns:
        The Plotly Figure object.
    """
    storage = MacroStorage(db_path)

    # Load data
    daily = storage.load_table("china_a_daily_daily")
    industry = storage.load_table("china_a_daily_industry")

    daily["date"] = pd.to_datetime(daily["date"])
    max_date = daily["date"].max()

    # Get lookback window
    trading_dates = sorted(daily["date"].unique())
    recent_dates = [d for d in trading_dates if d >= max_date - pd.Timedelta(days=lookback_days * 3)]
    if len(recent_dates) < 2:
        raise ValueError("Not enough recent trading data.")

    start_date = recent_dates[-min(lookback_days, len(recent_dates))]

    window = daily[daily["date"] >= start_date].copy()

    # Cumulative return per stock
    def _calc_return(group):
        group = group.sort_values("date")
        return (group["close"].iloc[-1] / group["close"].iloc[0] - 1) * 100

    returns = window.groupby("symbol").apply(_calc_return, include_groups=False)
    returns = returns.reset_index()
    returns.columns = ["symbol", "pct_return"]

    # Merge with industry
    merged = returns.merge(
        industry[["symbol", "industry", "code_name"]].drop_duplicates(),
        on="symbol", how="left",
    )
    merged = merged.dropna(subset=["pct_return"])
    merged["industry"] = merged["industry"].fillna("Unknown")
    merged = merged.sort_values("pct_return", ascending=False).reset_index(drop=True)

    # Assign colors by industry
    industries = merged["industry"].unique().tolist()
    # Use a qualitative palette
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#1a5599", "#cc5500", "#1f8c22", "#a62728", "#7467bd",
    ]
    color_map = {ind: palette[i % len(palette)] for i, ind in enumerate(industries)}
    merged["color"] = merged["industry"].map(color_map)

    # Build figure
    fig = go.Figure()

    for ind_name, group in merged.groupby("industry", sort=False):
        fig.add_trace(go.Bar(
            x=group["symbol"].tolist(),
            y=group["pct_return"].tolist(),
            name=ind_name,
            marker_color=group["color"].tolist(),
            hovertext=[
                f"<b>{row['code_name']} ({row['symbol']})</b><br>"
                f"Industry: {row['industry']}<br>"
                f"Return ({lookback_days}D): {row['pct_return']:+.2f}%"
                for _, row in group.iterrows()
            ],
            hovertemplate="%{hovertext}<extra></extra>",
        ))

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        height=500,
        width=1100,
        title_text=f"A-Share Stock Performance by Industry — Last {lookback_days} Trading Days (as of {max_date.date()})",
        title_font_size=16,
        title_x=0.5,
        barmode="group",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(size=9),
        ),
        xaxis=dict(tickangle=45, tickfont=dict(size=10)),
        yaxis=dict(title="Return (%)", tickformat="+.1f%"),
        margin=dict(l=50, r=20, t=80, b=120),
        template="plotly_white",
        hovermode="x unified",
    )

    # Save
    output_dir = Path(output_png or output_html).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_html:
        fig.write_html(output_html, include_plotlyjs="cdn")
        print(f"  ✅ HTML: {output_html}")

    if output_png:
        try:
            fig.write_image(output_png, scale=2)
            print(f"  ✅ PNG:  {output_png}")
        except Exception as e:
            print(f"  ⚠️  PNG export failed: {e}")

    return fig
