"""CSI sector index heatmap — shows which industries are hot/cold recently."""

import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import time

# CSI sector indices (中证行业指数)
CSI_INDICES = {
    'sh000932': '消费',
    'sh000934': '金融',
    'sh000936': '能源',
    'sh000938': '信息',
    'sh000940': '材料',
    'sh000942': '医药',
    'sh000944': '公用',
    'sh000946': '电信',
    'sh000948': '地产',
    'sh000950': '工业',
    'sh000952': '传媒',
    'sh000954': '制造',
}


def fetch_sector_returns(lookback_days: int = 5) -> pd.DataFrame:
    """Fetch returns for all CSI sector indices."""
    results = []
    for sym, name in CSI_INDICES.items():
        try:
            df = ak.stock_zh_index_daily(symbol=sym)
            df['date'] = pd.to_datetime(df['date'])

            max_date = df['date'].max()
            # Buffer to ensure enough trading days
            cutoff = max_date - pd.Timedelta(days=lookback_days * 3)
            recent = df[df['date'] >= cutoff].sort_values('date')

            if len(recent) < 2:
                continue

            # Exact lookback window
            trading_dates = sorted(recent['date'].unique())
            start_idx = max(0, len(trading_dates) - lookback_days)
            start_date = trading_dates[start_idx]

            window = recent[recent['date'] >= start_date]
            if len(window) < 2:
                continue

            first_close = window.iloc[0]['close']
            last_close = window.iloc[-1]['close']

            # 1-day return
            if len(window) >= 2:
                ret_1d = (window.iloc[-1]['close'] / window.iloc[-2]['close'] - 1) * 100
            else:
                ret_1d = 0

            ret_period = (last_close / first_close - 1) * 100

            results.append({
                'name': name,
                'ret_1d': ret_1d,
                f'ret_{lookback_days}d': ret_period,
                'close': last_close,
                'days': len(window),
            })
            time.sleep(0.05)
        except Exception as e:
            print(f"  ⚠️  {name}: {e}")

    return pd.DataFrame(results)


def build_sector_heatmap(
    lookback_days: int = 5,
    output_png: str = None,
    output_html: str = None,
    version: str = "0.2.0",
) -> go.Figure:
    """Build a sector heatmap showing recent industry performance."""

    print(f"  📊 Fetching {len(CSI_INDICES)} CSI sector indices...")
    df = fetch_sector_returns(lookback_days)

    if df.empty:
        raise ValueError("No sector data fetched.")

    df = df.sort_values(f'ret_{lookback_days}d', ascending=True).reset_index(drop=True)

    # Build heatmap — one row per time period
    periods = [f'1D', f'{lookback_days}D']
    columns = ['ret_1d', f'ret_{lookback_days}d']
    industries = df['name'].tolist()

    # Color scale: red (negative) → white (zero) → green (positive)
    fig = go.Figure()

    # Create a grouped bar chart instead — more readable
    colors_up = '#22c55e'
    colors_down = '#ef4444'

    # For each period, create a bar group
    for i, (period, col) in enumerate(zip(periods, columns)):
        values = df[col].values
        bar_colors = [colors_up if v >= 0 else colors_down for v in values]

        fig.add_trace(go.Bar(
            y=industries,
            x=values,
            name=period,
            marker_color=bar_colors,
            orientation='h',
            text=[f"{v:+.2f}%" for v in values],
            textposition='outside' if i == 1 else 'inside',
            textfont=dict(size=11, family="monospace",
                          color=[colors_up if v >= 0 else colors_down for v in values]),
            hovertemplate="<b>%{y}</b><br>" + f"{period} Return: %{{x:+.2f}}%<extra></extra>",
        ))

    max_date = pd.Timestamp.now().date()
    fig.update_layout(
        height=max(400, len(industries) * 35),
        width=900,
        title_text=f"🔥 A-Share Sector Performance — Last {lookback_days} Trading Days",
        title_font_size=18,
        title_x=0.5,
        barmode='group',
        bargap=0.15,
        bargroupgap=0.05,
        legend=dict(orientation="h", yanchor="top", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(
            title="Return (%)",
            tickformat="+.1f%",
            zeroline=True,
            zerolinecolor="gray",
            zerolinewidth=2,
            gridcolor="rgba(0,0,0,0.05)",
        ),
        yaxis=dict(
            autorange="reversed",  # Best performers on top
            tickfont=dict(size=13, family="monospace"),
        ),
        margin=dict(l=60, r=20, t=80, b=40),
        template="plotly_white",
    )

    # Save
    if output_html:
        Path(output_html).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_html, include_plotlyjs="cdn")
        print(f"  ✅ HTML: {output_html}")

    if output_png:
        try:
            fig.write_image(output_png, scale=2)
            print(f"  ✅ PNG:  {output_png}")
        except Exception as e:
            print(f"  ⚠️  PNG export failed: {e}")

    return fig
