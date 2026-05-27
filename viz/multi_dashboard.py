"""Multi-country dashboard — generates separate pages per country."""

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from pathlib import Path

pio.templates.default = "plotly_white"


def _label(value_col, label, color, xref, yref):
    """Fixed-position annotation, top-right of subplot."""
    last_val = value_col.iloc[-1]
    return go.layout.Annotation(
        x=0.97, y=last_val,
        text=f"{label} {last_val:.1f}",
        showarrow=False,
        font=dict(color=color, size=9, family="monospace"),
        xref=xref, yref=yref,
        xanchor="right", yanchor="top",
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(200,200,200,0.4)",
        borderwidth=1,
        borderpad=3,
    )


def build_china_dashboard(data: dict, version: str = "0.2.0",
                          gold_data: pd.DataFrame = None) -> go.Figure:
    """China macro + gold dashboard."""
    has_gold = gold_data is not None and not gold_data.empty
    rows = 5 if has_gold else 4

    fig = make_subplots(
        rows=rows, cols=1,
        specs=[[{"secondary_y": True}], [{}], [{}], [{}], [{}]] if has_gold
              else [[{"secondary_y": True}], [{}], [{}], [{}]],
        subplot_titles=(
            "GDP — Absolute Value & YoY Growth",
            "CPI vs PPI — YoY Growth Comparison",
            "PMI — Manufacturing & Non-Manufacturing (Boom/Bust Line=50)",
            "Money Supply M2 & M1 — YoY Growth",
            "SGE Gold Spot Price (CNY/gram)" if has_gold else "",
        ),
        vertical_spacing=0.08,
    )

    gdp = data["gdp"]
    fig.add_trace(go.Bar(x=gdp["date"], y=gdp["gdp"], name="GDP (100M CNY)",
                         marker_color="#3B82F6", opacity=0.6), row=1, col=1)
    fig.add_trace(go.Scatter(x=gdp["date"], y=gdp["gdp_yoy"], name="GDP YoY (%)",
                             mode="lines+markers", line=dict(color="#EF4444", width=2)),
                  row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="GDP (100M CNY)", row=1, col=1)
    fig.update_yaxes(title_text="YoY (%)", secondary_y=True, row=1, col=1)

    cpi, ppi = data["cpi"], data["ppi"]
    fig.add_trace(go.Scatter(x=cpi["date"], y=cpi["cpi_yoy"], name="CPI YoY (%)",
                             mode="lines+markers", line=dict(color="#F59E0B", width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=ppi["date"], y=ppi["ppi_yoy"], name="PPI YoY (%)",
                             mode="lines+markers", line=dict(color="#8B5CF6", width=2)), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)
    fig.update_yaxes(title_text="YoY (%)", row=2, col=1)

    pmi = data["pmi"]
    fig.add_trace(go.Scatter(x=pmi["date"], y=pmi["pmi_manufacturing"], name="Mfg PMI",
                             mode="lines+markers", line=dict(color="#10B981", width=2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=pmi["date"], y=pmi["pmi_non_manufacturing"], name="Non-Mfg PMI",
                             mode="lines+markers", line=dict(color="#6366F1", width=2)), row=3, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="red", line_width=2, row=3, col=1)
    fig.update_yaxes(title_text="PMI Index", row=3, col=1)

    ms = data["money_supply"]
    fig.add_trace(go.Scatter(x=ms["date"], y=ms["m2_yoy"], name="M2 YoY (%)",
                             mode="lines+markers", line=dict(color="#06B6D4", width=2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=ms["date"], y=ms["m1_yoy"], name="M1 YoY (%)",
                             mode="lines+markers", line=dict(color="#EC4899", width=2)), row=4, col=1)
    fig.update_yaxes(title_text="YoY (%)", row=4, col=1)

    if has_gold:
        fig.add_trace(go.Scatter(x=gold_data["date"], y=gold_data["sge_evening"],
                                 name="SGE Evening (CNY/g)",
                                 mode="lines", line=dict(color="#D4AF37", width=2)), row=5, col=1)
        fig.update_yaxes(title_text="CNY/gram", row=5, col=1)

    # Annotations
    gdp_last = gdp["gdp_yoy"].iloc[-1]
    fig.add_annotation(_label(gdp["gdp_yoy"], "GDP YoY", "#EF4444", "x domain", "y2"))
    fig.add_annotation(_label(cpi["cpi_yoy"], "CPI", "#F59E0B", "x2 domain", "y3"))
    fig.add_annotation(_label(ppi["ppi_yoy"], "PPI", "#8B5CF6", "x2 domain", "y3"))
    fig.add_annotation(_label(pmi["pmi_manufacturing"], "Mfg PMI", "#10B981", "x3 domain", "y4"))
    fig.add_annotation(_label(ms["m2_yoy"], "M2", "#06B6D4", "x4 domain", "y5"))

    fig.update_layout(
        height=2000 if has_gold else 1700, width=1100,
        title_text=f"🇨🇳 China Macroeconomic Dashboard v{version}",
        title_font_size=20, title_x=0.5,
        legend=dict(orientation="h", yanchor="top", y=0.995,
                    xanchor="center", x=0.5, font=dict(size=10)),
        hovermode="x unified", template="plotly_white", showlegend=True,
        margin=dict(r=40, t=80),
    )
    for i in range(1, rows + 1):
        fig.update_xaxes(tickformat="%Y-%m", tickangle=45, nticks=15, row=i, col=1)

    return fig


def build_usa_dashboard(data: dict, version: str = "0.2.0") -> go.Figure:
    """USA macro dashboard."""
    has_treasury = "treasury_index" in data

    # Determine rows
    rows = 3
    if "treasury_index" in data:
        rows += 1

    fig = make_subplots(
        rows=rows, cols=1,
        specs=[
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{}],
            [{}] if has_treasury else None,
        ] if has_treasury else [
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{}],
        ],
        subplot_titles=(
            "CPI YoY vs Core PCE",
            "Non-farm Payrolls & Unemployment Rate",
            "ISM Manufacturing PMI",
            "US Treasury Index" if has_treasury else "",
        ),
        vertical_spacing=0.08,
    )

    row_idx = 1
    # CPI + Core PCE
    if "cpi_yoy" in data:
        fig.add_trace(go.Scatter(x=data["cpi_yoy"]["date"], y=data["cpi_yoy"]["cpi_yoy"],
                                 name="CPI YoY (%)", mode="lines+markers",
                                 line=dict(color="#EF4444", width=2)), row=1, col=1)
    if "core_pce" in data:
        fig.add_trace(go.Scatter(x=data["core_pce"]["date"], y=data["core_pce"]["core_pce"],
                                 name="Core PCE (%)", mode="lines+markers",
                                 line=dict(color="#F59E0B", width=2)), row=1, col=1)
    fig.add_hline(y=2, line_dash="dash", line_color="gray", opacity=0.5,
                  annotation_text="Fed Target 2%", row=1, col=1)
    fig.update_yaxes(title_text="YoY (%)", row=1, col=1)
    row_idx = 2

    # Non-farm + Unemployment
    if "non_farm" in data:
        fig.add_trace(go.Scatter(x=data["non_farm"]["date"], y=data["non_farm"]["non_farm"],
                                 name="Non-farm (K)", mode="lines+markers",
                                 line=dict(color="#10B981", width=2)), row=2, col=1)
    if "unemployment" in data:
        fig.add_trace(go.Scatter(x=data["unemployment"]["date"], y=data["unemployment"]["unemployment_rate"],
                                 name="Unemployment Rate (%)", mode="lines+markers",
                                 line=dict(color="#8B5CF6", width=2), yaxis="y3"), row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Non-farm (K)", row=2, col=1)
    fig.update_yaxes(title_text="Unemployment (%)", secondary_y=True, row=2, col=1)
    row_idx = 3

    # ISM
    if "ism_mfg" in data:
        fig.add_trace(go.Scatter(x=data["ism_mfg"]["date"], y=data["ism_mfg"]["ism_pmi"],
                                 name="ISM PMI", mode="lines+markers",
                                 line=dict(color="#06B6D4", width=2)), row=3, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="red", line_width=2,
                  annotation_text="Expansion Line", row=3, col=1)
    fig.update_yaxes(title_text="ISM Index", row=3, col=1)
    row_idx = 4

    # Treasury
    if has_treasury:
        fig.add_trace(go.Scatter(x=data["treasury_index"]["date"], y=data["treasury_index"]["treasury_index"],
                                 name="Treasury Index", mode="lines",
                                 line=dict(color="#EC4899", width=2)), row=4, col=1)
        fig.update_yaxes(title_text="Index Value", row=4, col=1)

    fig.update_layout(
        height=1700, width=1100,
        title_text=f"🇺🇸 USA Macroeconomic Dashboard v{version}",
        title_font_size=20, title_x=0.5,
        legend=dict(orientation="h", yanchor="top", y=0.995,
                    xanchor="center", x=0.5, font=dict(size=10)),
        hovermode="x unified", template="plotly_white", showlegend=True,
        margin=dict(r=40, t=80),
    )
    for i in range(1, rows + 1):
        fig.update_xaxes(tickformat="%Y-%m", tickangle=45, nticks=15, row=i, col=1)

    return fig


def build_japan_dashboard(data: dict, version: str = "0.2.0") -> go.Figure:
    """Japan macro dashboard."""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            "CPI YoY",
            "Unemployment Rate",
            "Bank of Japan Rate",
        ),
        vertical_spacing=0.1,
    )

    if "cpi" in data:
        fig.add_trace(go.Scatter(x=data["cpi"]["date"], y=data["cpi"]["cpi_yoy"],
                                 name="CPI YoY (%)", mode="lines+markers",
                                 line=dict(color="#F59E0B", width=2)), row=1, col=1)
        fig.add_hline(y=2, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)
        fig.update_yaxes(title_text="YoY (%)", row=1, col=1)

    if "unemployment" in data:
        fig.add_trace(go.Scatter(x=data["unemployment"]["date"],
                                 y=data["unemployment"]["unemployment_rate"],
                                 name="Unemployment Rate (%)", mode="lines+markers",
                                 line=dict(color="#8B5CF6", width=2)), row=2, col=1)
        fig.update_yaxes(title_text="Unemployment (%)", row=2, col=1)

    if "bank_rate" in data:
        fig.add_trace(go.Scatter(x=data["bank_rate"]["date"], y=data["bank_rate"]["bank_rate"],
                                 name="BOJ Rate (%)", mode="lines+markers",
                                 line=dict(color="#06B6D4", width=2)), row=3, col=1)
        fig.update_yaxes(title_text="Rate (%)", row=3, col=1)

    fig.update_layout(
        height=1200, width=1100,
        title_text=f"🇯🇵 Japan Macroeconomic Dashboard v{version}",
        title_font_size=20, title_x=0.5,
        legend=dict(orientation="h", yanchor="top", y=0.995,
                    xanchor="center", x=0.5, font=dict(size=10)),
        hovermode="x unified", template="plotly_white", showlegend=True,
        margin=dict(r=40, t=80),
    )
    for i in range(1, 4):
        fig.update_xaxes(tickformat="%Y-%m", tickangle=45, nticks=15, row=i, col=1)

    return fig


def _save_fig(fig, output_dir: Path, name: str):
    """Save a figure as both HTML and PNG."""
    html_path = output_dir / f"dashboard_{name}.html"
    png_path = output_dir / f"dashboard_{name}.png"

    fig.write_html(str(html_path), include_plotlyjs="cdn")
    print(f"  ✅ HTML: {html_path}")

    try:
        fig.write_image(str(png_path), scale=2)
        print(f"  ✅ PNG:  {png_path}")
    except Exception as e:
        print(f"  ⚠️  PNG export failed: {e}")


def _export_csvs(data_map: dict[str, pd.DataFrame], output_dir: Path, name: str) -> list[str]:
    """Export each indicator DataFrame to CSV."""
    csv_paths = []
    for indicator, df in data_map.items():
        csv_path = output_dir / f"{name}_{indicator}.csv"
        df.to_csv(csv_path, index=False)
        csv_paths.append(str(csv_path))
        print(f"  📄 CSV:  {csv_path} ({len(df)} rows)")
    return csv_paths


def save_all(output_dir: Path, version: str = "0.2.0",
             china_data: dict = None, gold_data: pd.DataFrame = None,
             usa_data: dict = None, japan_data: dict = None):
    """Generate and save all dashboards (HTML + PNG + CSV)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if china_data:
        fig = build_china_dashboard(china_data, version, gold_data)
        _save_fig(fig, output_dir, "china")
        _export_csvs(china_data, output_dir, "china")
        if gold_data is not None and not gold_data.empty:
            _export_csvs({"gold_sge_spot": gold_data}, output_dir, "china")

    if usa_data:
        fig = build_usa_dashboard(usa_data, version)
        _save_fig(fig, output_dir, "usa")
        _export_csvs(usa_data, output_dir, "usa")

    if japan_data:
        fig = build_japan_dashboard(japan_data, version)
        _save_fig(fig, output_dir, "japan")
        _export_csvs(japan_data, output_dir, "japan")
