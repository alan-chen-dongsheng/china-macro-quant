"""A-share industry heatmap — shows which sectors are hot/cold recently."""

import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

from pipeline.storage import MacroStorage


def build_industry_heatmap(
    db_path: str,
    lookback_days: int = 5,
    output_png: str = None,
    output_html: str = None,
    version: str = "0.2.0",
) -> go.Figure:
    """Build an industry heatmap showing recent sector performance.

    For each stock, compute cumulative return over the last N trading days.
    Then aggregate by industry (median return) and display as a heatmap.

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

    # Ensure date is datetime
    daily["date"] = pd.to_datetime(daily["date"])

    # Get the latest trading date and lookback window
    max_date = daily["date"].max()
    cutoff = pd.Timestamp(max_date - pd.DateOffset(days=lookback_days * 2))

    # Recent data (buffer to ensure we get enough trading days)
    recent = daily[daily["date"] >= cutoff].copy()

    # Get the exact earliest date within our window
    trading_dates = sorted(recent["date"].unique())
    if len(trading_dates) < 2:
        raise ValueError("Not enough recent trading data.")

    start_date = trading_dates[-min(lookback_days, len(trading_dates))]

    # Filter to window
    window = recent[recent["date"] >= start_date].copy()

    # Calculate cumulative return per stock
    def _calc_return(group):
        group = group.sort_values("date")
        first_close = group["close"].iloc[0]
        last_close = group["close"].iloc[-1]
        return (last_close / first_close - 1) * 100

    returns = window.groupby("symbol").apply(_calc_return, include_groups=False)
    returns = returns.reset_index()
    returns.columns = ["symbol", "pct_return"]

    # Merge with industry
    merged = returns.merge(
        industry[["symbol", "industry", "code_name"]],
        on="symbol", how="left",
    )
    merged = merged.dropna(subset=["industry"])

    # Aggregate by industry: median return + stock count
    agg = merged.groupby("industry").agg(
        median_return=("pct_return", "median"),
        mean_return=("pct_return", "mean"),
        stock_count=("pct_return", "count"),
        pct_up=("pct_return", lambda x: (x > 0).sum() / len(x) * 100),
    ).reset_index()

    # Only keep industries with >= 3 stocks
    agg = agg[agg["stock_count"] >= 3].sort_values("median_return", ascending=False)

    # Create heatmap
    industries = agg["industry"].tolist()
    values = agg["median_return"].values
    counts = agg["stock_count"].values

    # Build hover text
    hover_text = []
    for _, row in agg.iterrows():
        hover_text.append(
            f"<b>{row['industry']}</b><br>"
            f"Median: {row['median_return']:+.2f}%<br>"
            f"Mean: {row['mean_return']:+.2f}%<br>"
            f"% Stocks Up: {row['pct_up']:.0f}%<br>"
            f"Stock Count: {int(row['stock_count'])}"
        )

    fig = go.Figure(data=go.Heatmap(
        z=[values],
        x=industries,
        y=[f"🔥 Hot Sectors ({lookback_days}D)"],
        text=[[f"{v:+.2f}%" for v in values]],
        texttemplate="%{text}",
        textfont=dict(size=11, family="monospace"),
        hoverongaps=False,
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=[hover_text],
        colorscale="RdYlGn",
        zmid=0,
        colorbar=dict(
            title="Median Return (%)",
            tickformat="+.1f%",
            len=0.8,
        ),
    ))

    fig.update_layout(
        height=400,
        width=max(1400, len(industries) * 120),
        title_text=f"A-Share Industry Performance Heatmap — Last {lookback_days} Trading Days (as of {max_date.date()})",
        title_font_size=16,
        title_x=0.5,
        xaxis=dict(
            tickangle=60,
            tickfont=dict(size=10),
            side="bottom",
        ),
        yaxis=dict(
            tickfont=dict(size=12, family="monospace"),
        ),
        margin=dict(l=10, r=10, t=80, b=100),
        template="plotly_white",
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
