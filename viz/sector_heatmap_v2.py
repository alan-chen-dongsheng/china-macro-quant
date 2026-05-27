"""A-share sector heatmap + trend chart.

1. Heatmap: Warm/cold colors show hot/cold sectors
2. Trend: Line chart showing sector performance over recent days

Uses BaoStock for sector indices (reliable from overseas).
"""

import baostock as bs
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from pathlib import Path
import time

pio.templates.default = "plotly_white"

# Sector indices from multiple sources
# BaoStock SSE sector indices + CSI sectors
SECTOR_INDICES = [
    # BaoStock SSE sector indices
    ('sh.000005', '上证工业'),
    ('sh.000006', '上证商业'),
    ('sh.000007', '上证地产'),
    ('sh.000008', '上证公用'),
    ('sh.000009', '上证综合'),
    ('sh.000010', '上证180'),
    ('sh.000004', '上证A股'),
    # CSI sector indices (via BaoStock)
    ('sh.000932', '中证消费'),
    ('sh.000934', '中证金融'),
    ('sh.000936', '中证能源'),
    ('sh.000938', '中证信息'),
    ('sh.000940', '中证材料'),
    ('sh.000942', '中证医药'),
    ('sh.000944', '中证公用'),
    ('sh.000946', '中证电信'),
    ('sh.000948', '中证地产'),
    ('sh.000950', '中证工业'),
    ('sh.000952', '中证传媒'),
    ('sh.000954', '中证制造'),
]


def fetch_sector_data(start_date: str = "2026-05-15", end_date: str = "2026-05-26") -> dict[str, pd.DataFrame]:
    """Fetch daily data for all sector indices via BaoStock."""
    data = {}
    print(f"  Fetching {len(SECTOR_INDICES)} sector indices...", flush=True)

    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock login failed: {lg.error_msg}")

    for sym, name in SECTOR_INDICES:
        try:
            rs = bs.query_history_k_data_plus(
                sym,
                fields='date,close,pctChg',
                start_date=start_date,
                end_date=end_date,
                frequency='d',
                adjustflag='3',
            )
            df = rs.get_data()
            if not df.empty and len(df) >= 2:
                df['date'] = pd.to_datetime(df['date'])
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                df['pctChg'] = pd.to_numeric(df['pctChg'], errors='coerce')
                data[name] = df.sort_values('date')
            time.sleep(0.02)
        except Exception:
            pass

    bs.logout()
    return data


def build_sector_charts(
    lookback_days: int = 5,
    output_png: str = None,
    output_html: str = None,
    version: str = "0.2.0",
):
    """Build heatmap (warm/cold) + trend chart for sector performance."""

    # ── Fetch data ──
    data = fetch_sector_data()
    if not data:
        raise ValueError("No sector data fetched.")

    print(f"  Got {len(data)} sectors with data", flush=True)

    # ── Determine date window ──
    max_date = max(df['date'].max() for df in data.values())
    all_dates = set()
    for df in data.values():
        all_dates.update(df['date'].tolist())
    trading_dates = sorted(all_dates)

    start_idx = max(0, len(trading_dates) - lookback_days)
    start_date = trading_dates[start_idx]

    # ── Heatmap data: period return ──
    heatmap_data = {}
    for name, df in data.items():
        window = df[(df['date'] >= start_date) & (df['date'] <= max_date)]
        if len(window) >= 2:
            first_close = window.iloc[0]['close']
            last_close = window.iloc[-1]['close']
            ret = (last_close / first_close - 1) * 100
            heatmap_data[name] = ret

    # Sort by return (hottest first)
    sorted_items = sorted(heatmap_data.items(), key=lambda x: x[1], reverse=True)
    sorted_names = [n for n, _ in sorted_items]
    sorted_values = [v for _, v in sorted_items]

    # ── Build figure ──
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.3, 0.7],
        vertical_spacing=0.15,
    )

    # ── Row 1: Heatmap (warm = hot, cold = cold) ──
    fig.add_trace(go.Heatmap(
        z=[sorted_values],
        x=sorted_names,
        y=[''],
        text=[[f"{v:+.1f}%" for v in sorted_values]],
        texttemplate="%{text}",
        textfont=dict(size=12, family="monospace", color="white"),
        # Custom colorscale: deep blue (cold) → white → deep red (hot)
        colorscale=[
            [0.0, '#1e3a8a'],   # deep blue (coldest)
            [0.2, '#3b82f6'],   # blue
            [0.4, '#93c5fd'],   # light blue
            [0.5, '#f8fafc'],   # white (neutral)
            [0.6, '#fca5a5'],   # light red
            [0.8, '#ef4444'],   # red (hot)
            [1.0, '#7f1d1d'],   # deep red (hottest)
        ],
        zmid=0,
        showscale=True,
        colorbar=dict(
            title="Return %",
            tickformat="+.0f%",
            len=0.5,
            thickness=12,
        ),
        hovertemplate="<b>%{x}</b><br>Return: %{z:+.1f}%<extra></extra>",
    ), row=1, col=1)

    # ── Row 2: Trend lines ──
    for name in sorted_names:
        df = data[name]
        window = df[(df['date'] >= start_date) & (df['date'] <= max_date)].copy()
        if window.empty:
            continue

        # Normalize: first close = 100
        base = window.iloc[0]['close']
        window['normalized'] = window['close'] / base * 100

        fig.add_trace(go.Scatter(
            x=window['date'],
            y=window['normalized'],
            name=name,
            mode='lines+markers',
            line=dict(width=2.5),
            marker=dict(size=5),
            hovertemplate=f"<b>{name}</b><br>Date: %{{x|%Y-%m-%d}}<br>Index: %{{y:.1f}}<extra></extra>",
        ), row=2, col=1)

    # Baseline at 100
    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.3, row=2, col=1)

    # ── Layout ──
    fig.update_layout(
        height=700,
        width=1100,
        title_text=f"🔥 A-Share Sector Performance — {lookback_days} Trading Days (as of {max_date.date()})",
        title_font_size=18,
        title_x=0.5,
        margin=dict(l=50, r=30, t=60, b=60),
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(size=9),
        ),
    )

    fig.update_xaxes(tickangle=45, nticks=8, row=1, col=1)
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=45, nticks=10, row=2, col=1)
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="Normalized (base=100)", row=2, col=1)

    # Hide y-axis labels for heatmap row
    fig.update_yaxes(showticklabels=False, row=1, col=1)

    # Save
    if output_html:
        Path(output_html).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_html, include_plotlyjs="cdn")
        print(f"  ✅ HTML: {output_html}", flush=True)

    if output_png:
        try:
            fig.write_image(output_png, scale=2)
            print(f"  ✅ PNG:  {output_png}", flush=True)
        except Exception as e:
            print(f"  ⚠️  PNG export failed: {e}", flush=True)

    return fig
