"""Dashboard assembler — 4-row macro dashboard with inline labels."""

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

pio.templates.default = "plotly_white"


def build_dashboard(data: dict[str, pd.DataFrame],
                    output_png: str = "output/macro_dashboard.png",
                    version: str = "0.1.0") -> str:
    """Build a 4-row vertical dashboard with annotations.

    Args:
        data: dict with keys 'gdp', 'cpi', 'ppi', 'pmi', 'money_supply'
        output_png: output PNG filename
        version: project version string to display in title

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
            "GDP — Absolute Value & YoY Growth",
            "CPI vs PPI — YoY Growth Comparison",
            "PMI — Manufacturing & Non-Manufacturing (Boom/Bust Line=50)",
            "Money Supply M2 & M1 — YoY Growth",
        ),
        vertical_spacing=0.09,
        shared_xaxes=False,
    )

    # ── Row 1: GDP ──
    gdp = data["gdp"]
    fig.add_trace(go.Bar(
        x=gdp["date"], y=gdp["gdp"],
        name="GDP Absolute (100M CNY)",
        marker_color="#3B82F6",
        opacity=0.6,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=gdp["date"], y=gdp["gdp_yoy"],
        name="GDP YoY (%)",
        mode="lines+markers",
        line=dict(color="#EF4444", width=2),
        marker=dict(size=5),
    ), row=1, col=1, secondary_y=True)

    fig.update_yaxes(title_text="GDP (100M CNY)", row=1, col=1)
    fig.update_yaxes(title_text="YoY (%)", secondary_y=True, row=1, col=1)

    # ── Row 2: CPI vs PPI ──
    cpi, ppi = data["cpi"], data["ppi"]
    fig.add_trace(go.Scatter(
        x=cpi["date"], y=cpi["cpi_yoy"],
        name="CPI YoY (%)",
        mode="lines+markers",
        line=dict(color="#F59E0B", width=2),
        marker=dict(size=5),
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=ppi["date"], y=ppi["ppi_yoy"],
        name="PPI YoY (%)",
        mode="lines+markers",
        line=dict(color="#8B5CF6", width=2),
        marker=dict(size=5),
    ), row=2, col=1)

    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)
    fig.update_yaxes(title_text="YoY (%)", row=2, col=1)

    # ── Row 3: PMI ──
    pmi = data["pmi"]
    fig.add_trace(go.Scatter(
        x=pmi["date"], y=pmi["pmi_manufacturing"],
        name="Manufacturing PMI",
        mode="lines+markers",
        line=dict(color="#10B981", width=2),
        marker=dict(size=5),
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=pmi["date"], y=pmi["pmi_non_manufacturing"],
        name="Non-Manufacturing PMI",
        mode="lines+markers",
        line=dict(color="#6366F1", width=2),
        marker=dict(size=5),
    ), row=3, col=1)

    fig.add_hline(
        y=50, line_dash="dash", line_color="red", line_width=2,
        row=3, col=1,
    )
    fig.update_yaxes(title_text="PMI Index", row=3, col=1)

    # ── Row 4: Money Supply ──
    ms = data["money_supply"]
    fig.add_trace(go.Scatter(
        x=ms["date"], y=ms["m2_yoy"],
        name="M2 YoY (%)",
        mode="lines+markers",
        line=dict(color="#06B6D4", width=2),
        marker=dict(size=5),
    ), row=4, col=1)

    fig.add_trace(go.Scatter(
        x=ms["date"], y=ms["m1_yoy"],
        name="M1 YoY (%)",
        mode="lines+markers",
        line=dict(color="#EC4899", width=2),
        marker=dict(size=5),
    ), row=4, col=1)

    fig.update_yaxes(title_text="YoY (%)", row=4, col=1)

    # ── Annotations: fixed-position labels, top-right of each subplot ──
    # Place labels at fixed positions so they NEVER overlap with data or each other.
    # Each label gets a dedicated row with a clean white background box.
    def _fixed_label(label, color, xref, yref, x_pos, y_pos):
        fig.add_annotation(
            x=x_pos, y=y_pos,
            text=label,
            showarrow=False,
            font=dict(color=color, size=10, family="monospace"),
            xref=xref, yref=yref,
            xanchor="right", yanchor="top",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(180,180,180,0.5)",
            borderwidth=1,
            borderpad=4,
        )

    # Row 1: GDP YoY (y2)
    gdp_yoy_val = gdp["gdp_yoy"].iloc[-1]
    _fixed_label(f"GDP YoY  {gdp_yoy_val:.1f}%", "#EF4444", "x domain", "y2", 0.98, 0.95)

    # Row 2: CPI & PPI (y3) — more vertical spacing
    cpi_val = cpi["cpi_yoy"].iloc[-1]
    ppi_val = ppi["ppi_yoy"].iloc[-1]
    _fixed_label(f"CPI  {cpi_val:.1f}%", "#F59E0B", "x2 domain", "y3", 0.98, 0.93)
    _fixed_label(f"PPI  {ppi_val:.1f}%", "#8B5CF6", "x2 domain", "y3", 0.98, 0.83)

    # Row 3: PMI (y4) — more vertical spacing
    mfg_val = pmi["pmi_manufacturing"].iloc[-1]
    nmfg_val = pmi["pmi_non_manufacturing"].iloc[-1]
    _fixed_label(f"Mfg PMI  {mfg_val:.1f}", "#10B981", "x3 domain", "y4", 0.98, 0.93)
    _fixed_label(f"Non-Mfg PMI  {nmfg_val:.1f}", "#6366F1", "x3 domain", "y4", 0.98, 0.83)

    # Row 4: M2 & M1 (y5) — more vertical spacing
    m2_val = ms["m2_yoy"].iloc[-1]
    m1_val = ms["m1_yoy"].iloc[-1]
    _fixed_label(f"M2  {m2_val:.1f}%", "#06B6D4", "x4 domain", "y5", 0.98, 0.93)
    _fixed_label(f"M1  {m1_val:.1f}%", "#EC4899", "x4 domain", "y5", 0.98, 0.83)

    # ── Layout ──
    fig.update_layout(
        height=1700,
        width=1100,
        title_text=f"China Macroeconomic Dashboard v{version}",
        title_font_size=22,
        title_x=0.5,
        legend=dict(orientation="h", yanchor="top", y=0.995,
                    xanchor="center", x=0.5, font=dict(size=10)),
        hovermode="x unified",
        template="plotly_white",
        showlegend=True,
        margin=dict(r=40, t=80),
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
    print(f"  ✅ Interactive: {output_html}")

    try:
        fig.write_image(str(output_png), scale=2)
        print(f"  ✅ Static: {output_png}")
    except Exception as e:
        print(f"  ⚠️  PNG export failed: {e}")

    return str(output_png)
