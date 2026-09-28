"""Reusable AXÍA Streamlit KPI card. Supply a verified KPIResult from the engine."""
from html import escape
import streamlit as st
from services.financial_kpi_engine import KPIResult, chart_points, delta_state, format_financial_value


def render_financial_kpi_card(metric: str, result: KPIResult,
                              reverse_scale: bool = False, icon: str = "▤"):
    points = chart_points(result)
    value = format_financial_value(result.value, result.currency or "")
    delta = result.growth_pct
    state = delta_state(delta, reverse_scale)
    colour = {"positive": "#059669", "negative": "#dc2626",
              "neutral": "#6b7280"}[state]
    delta_text = "N/A" if delta is None else f"{delta:+.1f}% {result.comparison}"
    bars = "".join(
        '<div title="{tooltip}" style="flex:1;height:{height}%;min-height:2px;'
        'background:#059669;border-radius:3px 3px 0 0"></div>'.format(
            tooltip=escape(f'{p["period"]}: {format_financial_value(p["value"], p["currency"])} '
                           f'({p["date"]})', quote=True),
            height=max(2, p["height_pct"]))
        for p in points
    )
    status = "" if result.status == "ok" else (
        f'<div style="font-size:11px;color:#64748b">{escape(result.status.replace("_", " ").title())}</div>'
    )
    st.markdown(
        '<div style="border:1px solid #d4e2f5;border-radius:16px;padding:20px;'
        'background:white;color:#0f2745">'
        f'<div style="display:flex;gap:16px;align-items:center">'
        f'<div style="background:#1d497d;color:white;border-radius:9px;'
        f'padding:12px;font-size:20px">{escape(icon)}</div>'
        f'<strong>{escape(metric)}</strong> <span style="color:#64748b">({escape(result.label)})</span></div>'
        f'<div style="display:flex;justify-content:space-between;align-items:end;margin-top:12px">'
        f'<div><div style="font-size:34px;font-weight:750">{escape(value)}</div>'
        f'<div style="color:{colour};font-weight:700">{escape(delta_text)}</div>{status}</div>'
        f'<div style="display:flex;gap:4px;align-items:end;width:100px;height:62px">{bars}</div></div>'
        f'<div style="font-size:10px;color:#64748b;margin-top:8px">'
        f'{escape(result.currency or "Currency unavailable")} · {escape(result.source or "Source unavailable")}</div></div>',
        unsafe_allow_html=True,
    )
