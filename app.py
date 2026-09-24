"""
FinSight AI - Streamlit app

One page: Fielmann Group's real quarterly revenue with a Holt-Winters
forecast for the next two quarters, the FY2025 Plan-vs-Actual guidance
table (a real budget-vs-actual example), and an AI-generated plain-language
narrative tying it together.

Chart follows a fixed, deliberate spec (see docs/DECISION_LOG.md, "chart
polish pass"): explicit y-axis number formatting (Streamlit's default
line_chart auto-formatting was producing garbled/truncated tick labels),
2px lines with visible end markers, a legend (never color-only identity for
2+ series), a hover tooltip, and direct end-labels on the last actual point
and each forecast point.

Run:
    streamlit run app.py
"""
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from forecast import forecast_next_quarters, load_quarterly_series  # noqa: E402
from narrative import generate_narrative  # noqa: E402

st.set_page_config(page_title="FinSight AI", page_icon="📊", layout="wide")

# Fixed categorical colors (identity channel) - not theme-dependent, per the
# project's data-viz palette: slot 1 (blue) for the real series, slot 2
# (orange) for the modeled/forecast series, in that fixed order.
COLOR_ACTUAL = "#3987e5"
COLOR_FORECAST = "#d95926"

st.title("FinSight AI")
st.caption(
    "Quarterly revenue forecast and AI-generated variance narrative, built on "
    "Fielmann Group AG's own real, publicly disclosed financial data. "
    "No synthetic data anywhere - see docs/DECISION_LOG.md for sourcing details."
)

# --- Load data & run forecast ---------------------------------------------
quarterly_df = load_quarterly_series()
forecast_result = forecast_next_quarters(quarterly_df, steps=2)

sector_df = pd.read_csv("data/processed/zva_industry_benchmark_2021_2025.csv")
latest_sector_row = sector_df.iloc[-1]
sector_context = {
    "year": int(latest_sector_row["year"]),
    "growth_pct": float(latest_sector_row["revenue_growth_pct"]),
}
fielmann_fy2025_growth = 7.4  # from fielmann_plan_vs_actual_2025.csv, actual total sales growth

next_q = forecast_result["forecast"][0]

# --- KPI stat tiles ---------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Last actual quarter",
    f"EUR {forecast_result['history_last_actual']['value_eur_m']}m",
    help=forecast_result["history_last_actual"]["period"],
)
k2.metric(
    f"{next_q['period']} forecast",
    f"EUR {next_q['forecast_eur_m']}m",
    delta=f"{next_q['yoy_growth_pct']}% YoY",
)
k3.metric(
    "Model accuracy (in-sample)",
    f"{forecast_result['fitted_params']['in_sample_mape_pct']}% MAPE",
    help="Holt-Winters additive; lower is better",
)
k4.metric(
    "FY2025 growth vs. sector",
    f"{fielmann_fy2025_growth}%",
    delta=f"{round(fielmann_fy2025_growth - sector_context['growth_pct'], 1)} pts vs ZVA sector ({sector_context['growth_pct']}%)",
)

st.divider()

# --- Chart: actual vs forecast ---------------------------------------------
st.subheader("Total consolidated sales - actual vs. forecast")

period_order = [f"{r.year}{r.quarter}" for r in quarterly_df.itertuples()] + [
    row["period"] for row in forecast_result["forecast"]
]

actual_long = quarterly_df[["year", "quarter", "total_consolidated_sales_eur_m"]].copy()
actual_long["period"] = actual_long["year"].astype(str) + actual_long["quarter"]
actual_long = actual_long.rename(columns={"total_consolidated_sales_eur_m": "value"})
actual_long["series"] = "Actual"
actual_long = actual_long[["period", "series", "value"]]

forecast_long = pd.DataFrame(
    [{"period": row["period"], "series": "Forecast", "value": row["forecast_eur_m"]} for row in forecast_result["forecast"]]
)
# bridge point so the forecast line connects visually to the last actual point
bridge = actual_long.iloc[[-1]].copy()
bridge["series"] = "Forecast"

chart_long = pd.concat([actual_long, bridge, forecast_long], ignore_index=True)

base = alt.Chart(chart_long).encode(
    x=alt.X("period:N", sort=period_order, title=None, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y(
        "value:Q",
        title="EUR million",
        axis=alt.Axis(format=".0f", grid=True, tickMinStep=25),
        scale=alt.Scale(zero=False),
    ),
    color=alt.Color(
        "series:N",
        scale=alt.Scale(domain=["Actual", "Forecast"], range=[COLOR_ACTUAL, COLOR_FORECAST]),
        legend=alt.Legend(title=None, orient="top-left"),
    ),
    tooltip=[
        alt.Tooltip("period:N", title="Quarter"),
        alt.Tooltip("series:N", title="Series"),
        alt.Tooltip("value:Q", title="EUR m", format=".1f"),
    ],
)

lines = base.mark_line(strokeWidth=2, interpolate="monotone")
points = base.mark_point(size=70, filled=True, opacity=1)

# Direct end-labels: last actual point + every forecast point (sparing, per spec)
label_rows = pd.concat(
    [
        actual_long.iloc[[-1]],
        forecast_long,
    ],
    ignore_index=True,
)
labels = (
    alt.Chart(label_rows)
    .mark_text(dy=-14, fontSize=12, fontWeight="bold")
    .encode(
        x=alt.X("period:N", sort=period_order),
        y="value:Q",
        text=alt.Text("value:Q", format=".0f"),
        color=alt.Color("series:N", scale=alt.Scale(domain=["Actual", "Forecast"], range=[COLOR_ACTUAL, COLOR_FORECAST]), legend=None),
    )
)

chart = (lines + points + labels).properties(height=380)
st.altair_chart(chart, use_container_width=True, theme="streamlit")

st.caption(
    f"Model: {forecast_result['model']} · "
    f"in-sample MAPE: {forecast_result['fitted_params']['in_sample_mape_pct']}%"
)

st.divider()

# --- AI narrative ------------------------------------------------------
st.subheader("AI-generated narrative")

try:
    narrative = generate_narrative(forecast_result, sector_context=sector_context)
    st.info(narrative, icon="🧠")
except Exception as exc:  # noqa: BLE001
    st.warning(
        "Couldn't reach Groq to generate the narrative right now "
        f"({exc}). Showing the structured forecast data instead."
    )
    st.json(forecast_result)

st.divider()

# --- Real budget vs actual example --------------------------------------
st.subheader("FY2025: Fielmann's own guidance vs. actual results")
st.caption(
    "A real example of budget-vs-actual variance reporting, taken directly "
    "from Fielmann's Annual Report 2025 - not modeled."
)
plan_actual_df = pd.read_csv("data/processed/fielmann_plan_vs_actual_2025.csv")
st.dataframe(plan_actual_df, hide_index=True, width="stretch")

st.caption(
    "Data sources: Fielmann Group AG investor relations (fielmann-group.com) and "
    "ZVA (Zentralverband der Augenoptiker und Optometristen) industry reports. "
    "Full citation log in data/raw/SOURCES.md."
)
