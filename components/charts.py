"""
components/charts.py - Plotly figures used by the pages.

All numbers come from fuzzy_model.py; nothing is recomputed here except
sampling the membership functions for plotting.
"""

import numpy as np
import plotly.graph_objects as go

from components.ui import LEVEL_BG, LEVEL_COLOR, TERM_COLORS
from fuzzy_model import (INPUT_VARIABLES, OUTPUT_UNIVERSE, OUTPUT_VARIABLE, category_thresholds,
                         trapmf)

FONT = dict(family="Inter, Segoe UI, sans-serif", size=12)


def _layout(fig, height, **kw):
    fig.update_layout(height=height, margin=dict(t=40, b=40, l=40, r=20), font=FONT,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.3, x=0), **kw)
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    return fig


def fatigue_gauge(index: float, level: str):
    t_low, t_high = category_thresholds()
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=index,
        number={"suffix": " / 100", "font": {"size": 38}, "valueformat": ".1f"},
        gauge={
            "axis": {"range": [0, 100], "tickvals": [0, t_low, t_high, 100],
                     "ticktext": ["0", f"{t_low:.2f}", f"{t_high:.2f}", "100"]},
            "bar": {"color": LEVEL_COLOR[level], "thickness": 0.3},
            "steps": [
                {"range": [0, t_low], "color": LEVEL_BG["LOW"]},
                {"range": [t_low, t_high], "color": LEVEL_BG["MODERATE"]},
                {"range": [t_high, 100], "color": LEVEL_BG["HIGH"]},
            ],
            "threshold": {"line": {"color": "#1E293B", "width": 3}, "thickness": 0.8, "value": index},
        },
    ))
    fig.update_layout(height=260, margin=dict(t=20, b=10, l=30, r=30), font=FONT,
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def input_mf(var: str, value: float | None = None, height: int = 260):
    """Membership functions of one input; optional marker at the crisp value."""
    spec = INPUT_VARIABLES[var]
    lo, hi = spec["range"]
    xs = np.linspace(lo, hi, 400)
    fig = go.Figure()
    for (term, params), color in zip(spec["terms"].items(), TERM_COLORS):
        fig.add_trace(go.Scatter(x=xs, y=trapmf(xs, *params), name=term, mode="lines",
                                 line=dict(color=color, width=2)))
    if value is not None:
        fig.add_vline(x=value, line_dash="dash", line_color="#64748B")
        for (term, params), color in zip(spec["terms"].items(), TERM_COLORS):
            d = trapmf(value, *params)
            if d > 0:
                fig.add_trace(go.Scatter(x=[value], y=[d], mode="markers+text", showlegend=False,
                                         marker=dict(color=color, size=9), text=[f"{d:.2f}"],
                                         textposition="middle right", hoverinfo="skip"))
    fig.update_layout(title=dict(text=spec["label"], font=dict(size=14)))
    fig.update_xaxes(title_text=spec["unit"], range=[lo, hi])
    fig.update_yaxes(title_text="μ", range=[-0.05, 1.15])
    return _layout(fig, height)


def output_mf(result=None, height: int = 320):
    """Output membership functions, with the aggregated set and centroid if given."""
    fig = go.Figure()
    for (term, params), color in zip(OUTPUT_VARIABLE["terms"].items(), TERM_COLORS):
        fig.add_trace(go.Scatter(x=OUTPUT_UNIVERSE, y=trapmf(OUTPUT_UNIVERSE, *params), name=term,
                                 mode="lines", line=dict(color=color, width=1.5, dash="dash")))
    if result is not None:
        fig.add_trace(go.Scatter(x=OUTPUT_UNIVERSE, y=result.aggregated, name="aggregated output",
                                 mode="lines", fill="tozeroy", line=dict(color="#475569", width=1),
                                 fillcolor="rgba(71,85,105,0.35)"))
        fig.add_vline(x=result.fatigue_index, line_color="#1E293B", line_width=2,
                      annotation_text=f"centroid z* = {result.fatigue_index:.2f}",
                      annotation_position="top right")
    fig.update_xaxes(title_text="Fatigue Index", range=[0, 100])
    fig.update_yaxes(title_text="μ", range=[-0.05, 1.2])
    return _layout(fig, height)


def membership_bars(memberships: dict, height: int = 300):
    """Grouped bars: degree of every label of every input."""
    fig = go.Figure()
    for i in range(3):
        xs, ys, texts = [], [], []
        for var, degs in memberships.items():
            term, d = list(degs.items())[i]
            xs.append(INPUT_VARIABLES[var]["label"])
            ys.append(d)
            texts.append(term)
        fig.add_trace(go.Bar(x=xs, y=ys, name=["label 1", "label 2", "label 3"][i],
                             marker_color=TERM_COLORS[i], text=texts, textposition="outside",
                             hovertemplate="%{text}: %{y:.3f}<extra></extra>"))
    fig.update_layout(barmode="group", showlegend=False)
    fig.update_yaxes(title_text="μ", range=[0, 1.2])
    return _layout(fig, height)


def factor_bars(factors: list, height: int = 220):
    """Horizontal bars of risk memberships, e.g. [("Short sleep", 0.5), ...]."""
    names = [f for f, _ in factors][::-1]
    vals = [v for _, v in factors][::-1]
    colors = [LEVEL_COLOR["HIGH"] if v >= 0.5 else LEVEL_COLOR["MODERATE"] for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=colors,
                           text=[f"{v:.2f}" for v in vals], textposition="outside"))
    fig.update_xaxes(range=[0, 1.15], title_text="membership in risk label")
    return _layout(fig, height, showlegend=False)


def sensitivity(sweep, var: str, current: float | None = None, height: int = 320):
    t_low, t_high = category_thresholds()
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=t_low, fillcolor=LEVEL_BG["LOW"], opacity=0.5, line_width=0)
    fig.add_hrect(y0=t_low, y1=t_high, fillcolor=LEVEL_BG["MODERATE"], opacity=0.5, line_width=0)
    fig.add_hrect(y0=t_high, y1=100, fillcolor=LEVEL_BG["HIGH"], opacity=0.5, line_width=0)
    fig.add_trace(go.Scatter(x=sweep[var], y=sweep["fatigue_index"], mode="lines",
                             line=dict(color="#2563EB", width=2.5), name="fatigue index"))
    if current is not None:
        fig.add_vline(x=current, line_dash="dash", line_color="#64748B",
                      annotation_text="baseline", annotation_position="top")
    fig.update_xaxes(title_text=f"{INPUT_VARIABLES[var]['label']} ({INPUT_VARIABLES[var]['unit']})")
    fig.update_yaxes(title_text="Fatigue Index", range=[0, 100])
    return _layout(fig, height, showlegend=False)


def histogram(series, title: str, height: int = 230):
    fig = go.Figure(go.Histogram(x=series, nbinsx=8, marker_color="#2563EB",
                                 marker_line=dict(color="white", width=1)))
    fig.update_layout(title=dict(text=title, font=dict(size=13)), bargap=0.05)
    return _layout(fig, height, showlegend=False)


def scatter_index_vs_self(scored, height: int = 360):
    fig = go.Figure(go.Scatter(
        x=scored["self_reported_fatigue"], y=scored["fuzzy_index"], mode="markers",
        marker=dict(size=10, color=[LEVEL_COLOR[l] for l in scored["fuzzy_level"]],
                    line=dict(color="white", width=1)),
        text=scored["student_id"],
        hovertemplate="%{text}<br>self-report %{x}<br>fuzzy index %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text="self-reported fatigue (1-10)", range=[0.5, 10.5])
    fig.update_yaxes(title_text="fuzzy fatigue index (0-100)", range=[0, 100])
    return _layout(fig, height, showlegend=False)


def confusion_heatmap(cm, height: int = 360):
    fig = go.Figure(go.Heatmap(
        z=cm.to_numpy(), x=list(cm.columns), y=list(cm.index), colorscale="Blues",
        text=cm.to_numpy(), texttemplate="%{text}", showscale=False,
        hovertemplate="self-report %{y}<br>fuzzy %{x}<br>n = %{z}<extra></extra>"))
    fig.update_xaxes(title_text="fuzzy level", showgrid=False)
    fig.update_yaxes(title_text="self-report level", autorange="reversed", showgrid=False)
    return _layout(fig, height, showlegend=False)
