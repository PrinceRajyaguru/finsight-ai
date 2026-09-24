"""
FinSight AI - Streamlit app

One page: Fielmann Group's real quarterly revenue with a Holt-Winters
forecast for the next two quarters, the FY2025 Plan-vs-Actual guidance
table (a real budget-vs-actual example), and an AI-generated plain-language
narrative tying it together.

Run:
    streamlit run app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from forecast import forecast_next_quarters, load_quarterly_series  # noqa: E402
from narrative import generate_narrative  # noqa: E402

st.set_page_config(page_title="FinSight AI", page_icon="📊", layout="centered")

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

# --- Chart: actual vs forecast ---------------------------------------------
st.subheader("Total consolidated sales - actual vs. forecast")

chart_df = quarterly_df[["year", "quarter", "total_consolidated_sales_eur_m"]].copy()
chart_df["period"] = chart_df["year"].astype(str) + chart_df["quarter"]
chart_df = chart_df.rename(columns={"total_consolidated_sales_eur_m": "Actual (EUR m)"})
chart_df["Forecast (EUR m)"] = float("nan")

forecast_rows = pd.DataFrame(
    [
        {"period": row["period"], "Actual (EUR m)": float("nan"), "Forecast (EUR m)": row["forecast_eur_m"]}
        for row in forecast_result["forecast"]
    ]
)
# bridge point so the forecast line connects to the last actual point
bridge = chart_df[["period", "Actual (EUR m)", "Forecast (EUR m)"]].iloc[[-1]].copy()
bridge["Forecast (EUR m)"] = bridge["Actual (EUR m)"]

plot_df = pd.concat(
    [chart_df[["period", "Actual (EUR m)", "Forecast (EUR m)"]], bridge, forecast_rows],
    ignore_index=True,
)
plot_df = plot_df.set_index("period")
st.line_chart(plot_df)

st.caption(
    f"Model: {forecast_result['model']} · "
    f"in-sample MAPE: {forecast_result['fitted_params']['in_sample_mape_pct']}%"
)

# --- AI narrative ------------------------------------------------------
st.subheader("AI-generated narrative")

try:
    narrative = generate_narrative(forecast_result, sector_context=sector_context)
    st.write(narrative)
except Exception as exc:  # noqa: BLE001
    st.warning(
        "Couldn't reach Groq to generate the narrative right now "
        f"({exc}). Showing the structured forecast data instead."
    )
    st.json(forecast_result)

# --- Real budget vs actual example --------------------------------------
st.subheader("FY2025: Fielmann's own guidance vs. actual results")
st.caption(
    "A real example of budget-vs-actual variance reporting, taken directly "
    "from Fielmann's Annual Report 2025 - not modeled."
)
plan_actual_df = pd.read_csv("data/processed/fielmann_plan_vs_actual_2025.csv")
st.dataframe(plan_actual_df, hide_index=True, width="stretch")

# --- Sector benchmark -----------------------------------------------------
st.subheader("Sector benchmark")
fielmann_fy2025_growth = 7.4  # from fielmann_plan_vs_actual_2025.csv, actual total sales growth
st.metric(
    label=f"Fielmann FY2025 revenue growth vs. German optical retail sector (ZVA, {sector_context['year']})",
    value=f"{fielmann_fy2025_growth}%",
    delta=f"{round(fielmann_fy2025_growth - sector_context['growth_pct'], 1)} pts vs sector ({sector_context['growth_pct']}%)",
)

st.caption(
    "Data sources: Fielmann Group AG investor relations (fielmann-group.com) and "
    "ZVA (Zentralverband der Augenoptiker und Optometristen) industry reports. "
    "Full citation log in data/raw/SOURCES.md."
)
