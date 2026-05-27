"""Dashboard assembler — 4-row macro dashboard with inline labels."""

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

pio.templates.default = "plotly_white"


def build_dashboard(data: dict[str, pd.DataFrame],
                    output_png: str = "output/macro_dashboard.png") -> str:
    """Build a 4-row vertical dashboard with annotations.

    Args:
        data: dict with keys 'gdp', 'cpi', 'ppi', 'pmi', 'money_supply'
        output_png: output PNG filename

    Returns:
        The output PNG path.
    """
    fig = make_subplots(
        rows=4, cols=1,
        specs=[
            [{"secondary_y": True}],
            [{}],
            [{}],
            [{}],
        ],
        subplot_titles=(
            "GDP — 绝对值 & 同比增速",
            "CPI vs PPI — 同比增速对比",
            "PMI — 制造业 & 非制造业 (荣枯线=50)",
            "货币供应量 M2 & M1 — 同比增速",
        ),
        vertical_spacing=0.09,
        shared_xaxes=False,
    )

    # ── Row 1: GDP ──
    gdp = data["gdp"]
    fig.add_trace(go.Bar(
        x=gdp["date"], y=gdp["gdp"],
        name="GDP 绝对值 (亿元)",
        marker_color="#3B82F6",
        opacity=0.6,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=gdp["date"], y=gdp["gdp_yoy"],
        name="GDP 同比 (%)",
        mode="lines+markers",
        line=dict(color="#EF4444", width=2),
        marker=dict(size=5),
    ), row=1, col=1, secondary_y=True)

    fig.update_yaxes(title_text="GDP (亿元)", row=1, col=1)
    fig.update_yaxes(title_text="同比 (%)", secondary_y=True, row=1, col=1)

    # ── Row 2: CPI vs PPI ──
    cpi, ppi = data["cpi"], data["ppi"]
    fig.add_trace(go.Scatter(
        x=cpi["date"], y=cpi["cpi_yoy"],
        name="CPI 同比 (%)",
        mode="lines+markers",
        line=dict(color="#F59E0B", width=2),
        marker=dict(size=5),
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=ppi["date"], y=ppi["ppi_yoy"],
        name="PPI 同比 (%)",
        mode="lines+markers",
        line=dict(color="#8B5CF6", width=2),
        marker=dict(size=5),
    ), row=2, col=1)

    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)
    fig.update_yaxes(title_text="同比 (%)", row=2, col=1)

    # ── Row 3: PMI ──
    pmi = data["pmi"]
    fig.add_trace(go.Scatter(
        x=pmi["date"], y=pmi["pmi_manufacturing"],
        name="制造业 PMI",
        mode="lines+markers",
        line=dict(color="#10B981", width=2),
        marker=dict(size=5),
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=pmi["date"], y=pmi["pmi_non_manufacturing"],
        name="非制造业 PMI",
        mode="lines+markers",
        line=dict(color="#6366F1", width=2),
        marker=dict(size=5),
    ), row=3, col=1)

    fig.add_hline(
        y=50, line_dash="dash", line_color="red", line_width=2,
        row=3, col=1,
    )
    fig.update_yaxes(title_text="PMI", row=3, col=1)

    # ── Row 4: Money Supply ──
    ms = data["money_supply"]
    fig.add_trace(go.Scatter(
        x=ms["date"], y=ms["m2_yoy"],
        name="M2 同比 (%)",
        mode="lines+markers",
        line=dict(color="#06B6D4", width=2),
        marker=dict(size=5),
    ), row=4, col=1)

    fig.add_trace(go.Scatter(
        x=ms["date"], y=ms["m1_yoy"],
        name="M1 同比 (%)",
        mode="lines+markers",
        line=dict(color="#EC4899", width=2),
        marker=dict(size=5),
    ), row=4, col=1)

    fig.update_yaxes(title_text="同比 (%)", row=4, col=1)

    # ── Annotations: inline labels at data endpoints ──
    def _label(date_col, value_col, label, color, xref, yref):
        fig.add_annotation(
            x=date_col.iloc[-1], y=value_col.iloc[-1],
            text=f"{label} {value_col.iloc[-1]:.1f}",
            showarrow=False,
            font=dict(color=color, size=12),
            xshift=45, yshift=5,
            xref=xref, yref=yref,
        )

    # Row 1: GDP YoY (secondary axis)
    _label(gdp["date"], gdp["gdp_yoy"], "GDP同比", "#EF4444", "x", "y2")

    # Row 2: CPI & PPI
    _label(cpi["date"], cpi["cpi_yoy"], "CPI", "#F59E0B", "x2", "y2")
    _label(ppi["date"], ppi["ppi_yoy"], "PPI", "#8B5CF6", "x2", "y2")

    # Row 3: PMI
    _label(pmi["date"], pmi["pmi_manufacturing"], "制造业PMI", "#10B981", "x3", "y3")
    _label(pmi["date"], pmi["pmi_non_manufacturing"], "非制造业PMI", "#6366F1", "x3", "y3")

    # Row 4: M2 & M1
    _label(ms["date"], ms["m2_yoy"], "M2", "#06B6D4", "x4", "y4")
    _label(ms["date"], ms["m1_yoy"], "M1", "#EC4899", "x4", "y4")

    # ── Layout ──
    fig.update_layout(
        height=1600,
        width=1100,
        title_text="中国宏观经济数据仪表盘",
        title_font_size=22,
        title_x=0.5,
        legend=dict(orientation="h", yanchor="bottom", y=1.0,
                    xanchor="center", x=0.5, font=dict(size=11)),
        hovermode="x unified",
        template="plotly_white",
        showlegend=True,
    )

    for i in range(1, 5):
        fig.update_xaxes(
            tickformat="%Y-%m", tickangle=45,
            nticks=15,
            row=i, col=1,
        )

    # ── Save ──
    output_html = str(output_png).replace(".png", ".html")

    fig.write_html(output_html, include_plotlyjs="cdn")
    print(f"  ✅ 交互版: {output_html}")

    try:
        fig.write_image(str(output_png), scale=2)
        print(f"  ✅ 静态图: {output_png}")
    except Exception as e:
        print(f"  ⚠️  PNG 导出失败: {e}")

    return str(output_png)
