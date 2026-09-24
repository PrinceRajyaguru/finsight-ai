# FinSight AI

Finance KPI forecasting + AI-generated plain-language variance narrative, built on Fielmann Group AG's own real, publicly disclosed financial data, benchmarked against the German optical retail industry (ZVA).

**Status: working end-to-end.** Data sourcing, forecast model, Groq narrative, and the Streamlit app are all built and confirmed running.

## Why Fielmann's own data

Built ahead of an interview for a Data Scientist (AI & Automation) role at Fielmann's Finance department. Rather than a generic synthetic demo, this forecasts Fielmann's own real, publicly reported revenue and compares it against real German optical-industry benchmark data. No synthetic or fabricated figures anywhere. Full reasoning in [docs/DECISION_LOG.md](docs/DECISION_LOG.md).

## What it does

1. Loads Fielmann Group's real quarterly total consolidated sales (Q1/2023-Q2/2026), derived from their own published interim statements and annual reports.
2. Forecasts the next two quarters with a Holt-Winters additive model (level + trend + quarterly seasonality), implemented directly with `numpy`/`scipy` so every step is inspectable rather than hidden in a library call. Current output: 2026Q3 at EUR 677.5m (+9.6% YoY), 2026Q4 at EUR 644.2m (+8.6% YoY), in-sample MAPE 2.6%.
3. Sends the forecast, its year-over-year growth, and the German optical retail sector's benchmark growth rate to a Groq-hosted model (`openai/gpt-oss-120b`), which writes a short executive-style narrative.
4. Displays a chart of actual vs. forecast revenue, the narrative, Fielmann's own FY2025 Plan-vs-Actual guidance table (a real budget-vs-actual example, not modeled), and a sector-comparison metric, in a one-page Streamlit app. Falls back to showing the structured forecast data directly if Groq is unreachable.

## Architecture

```
Fielmann quarterly revenue (real, cited)
  -> Holt-Winters forecast (numpy/scipy, src/forecast.py)
  -> forecast + YoY variance + sector benchmark -> structured prompt
  -> Groq API (openai/gpt-oss-120b, src/narrative.py) -> plain-language narrative
  -> Streamlit app (app.py): chart + narrative + plan-vs-actual + sector metric
```

## Data

All data is real, sourced from primary public disclosures, and fully cited in [data/raw/SOURCES.md](data/raw/SOURCES.md):

- `data/processed/fielmann_annual_2021_2025.csv` - Group key figures, FY2021-FY2025
- `data/processed/fielmann_quarterly_2023_2026.csv` - Group total consolidated sales by quarter, Q1/2023-Q2/2026
- `data/processed/fielmann_plan_vs_actual_2025.csv` - Fielmann's own published guidance vs. actual results, FY2025
- `data/processed/fielmann_segment_2025.csv` - Revenue by region, FY2025
- `data/processed/zva_industry_benchmark_2021_2025.csv` - German optical retail industry revenue, store count, employment, 2021-2025 (ZVA)

## Key decisions (see docs/DECISION_LOG.md for full reasoning)

- **Real data only, no synthetic padding.** Considered blending in synthetic figures to fill gaps; rejected it because mixing real, named-company data with invented numbers is harder to defend under scrutiny than either being fully real or openly synthetic - especially for a finance audience that scrutinizes data provenance closely.
- **Quarterly, not monthly.** Fielmann doesn't publicly disclose monthly revenue (normal for a company at this reporting cadence), so the model works at the quarterly/annual cadence the real data actually supports - which also matches how real corporate FP&A forecasting is actually done.
- **Holt-Winters, not a plain trend line.** A first pass with trend-only smoothing missed a real, consistent seasonal pattern: Fielmann's Q4 revenue dips versus Q3 in every year in the series. Adding a seasonal component (still a simple, explainable method - no external forecasting library) dropped in-sample error and captured that pattern.
- **ZVA over Destatis/handelsdaten.** ZVA (the German optical trade association) publishes a free, public annual industry report; Destatis's sector-level breakdown wasn't easily extractable, and handelsdaten.de's series is paywalled beyond a single data point.
- **Groq model swap.** The originally planned `llama-3.3-70b-versatile` returned a 404 against the real API key despite still appearing in Groq's docs; queried Groq's `/models` endpoint directly to find what the key actually had access to, and switched to `openai/gpt-oss-120b`. The model is now set via a `GROQ_MODEL` env var so this doesn't require a code change again.

## Things worth knowing before presenting this

- The forecast is model output, not a certainty, and the sector comparison currently rests on one year (2025) of ZVA benchmark data. Worth saying so plainly rather than letting the chart imply more precision than it has.
- The fitted smoothing parameters are alpha=0.99, beta=0.01, gamma=0.01 - the model leans almost entirely on the most recent quarter's level, with a very stable trend/seasonal estimate. Worth being able to explain that if asked, since it's a specific, checkable claim about the model's behavior.
- Groq's free tier allows 1,000 requests/day - fine for a demo, not for production traffic.
- `.env` holds the real API key - never commit it (it's in `.gitignore`) or paste it anywhere shared.

## How to run

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

Get a free Groq API key at [console.groq.com](https://console.groq.com), then create a `.env` file in the project root:

```
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-120b
```

Check the forecast logic on its own:

```bash
python src/forecast.py
```

Check the Groq narrative call on its own:

```bash
python src/narrative.py
```

Run the app (restart the server after any `.env` change - Streamlit caches environment state across reruns within a session):

```bash
streamlit run app.py
```

## Screenshot

_Add a screenshot here._

## Cost

EUR 0 - all data sources are free/public, Groq's free API tier, Streamlit Community Cloud free tier if deployed.

## Scope note

Built quickly and deliberately time-boxed as a demo, not a production system: no automated tests, no CI, no error-rate monitoring on the forecast. The data pipeline (sourcing, citation, verification) got the most care, since that's the part that has to hold up under questions.
