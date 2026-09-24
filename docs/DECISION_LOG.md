# FinSight AI — Decision Log

A running record of the reasoning behind this project's design, kept so the choices can be explained clearly in an interview. Written as decisions are made, not reconstructed afterward.

## Why this project exists

Built ahead of an interview for a Data Scientist (AI & Automation) role at Fielmann's Finance department. The job description asks for two things specifically: forecasting/budgeting/scenario modeling, and using Generative AI to make finance processes more efficient. This project demonstrates both together, deliberately, as a fast and focused build rather than a multi-week one.

## Decision 1: Concept

A finance KPI forecast paired with an AI-generated plain-language narrative that explains the forecast and any variance against a benchmark — mirroring what a finance analyst actually produces for stakeholders: a number, a trend, and a "why."

## Decision 2: Architecture

Dataset -> time-series forecast (statsmodels) -> forecast + variance passed as structured input to an LLM (Groq, Llama 3.3) -> plain-language narrative -> displayed in a small Streamlit app.

Chose Groq's free API over self-hosting an open model (extra setup time, not worth it for a time-boxed build) or Hugging Face's free inference (slower, flakier rate limits). Chose statsmodels (ETS/Holt-Winters) over Prophet: Prophet's cmdstanpy backend risks install friction that works against a time-boxed build, and ETS gives a cleaner story to explain live in an interview.

## Decision 3: Real data vs. synthetic data — the key pivot

The original plan (see original handoff, preserved below) called for a synthetic finance dataset, since that's the fastest path and doesn't depend on finding a suitable real one.

Revisited this after realizing a much stronger option existed: Fielmann Group AG is itself a public company (XETRA: FIE), so its own quarterly and annual financial disclosures are freely available. Using the actual company the interview is for, with its own real numbers, is a substantially stronger interview story than a generic synthetic demo — and avoids the most common failure mode of portfolio projects, which is looking like every other Kaggle-dataset demo.

Considered, and rejected, blending real Fielmann data with synthetic data to fill gaps (e.g. months/quarters not disclosed). Reasoning: finance audiences are trained to scrutinize data provenance above almost everything else. A dataset that's *partly* real and *partly* invented, sitting under a real company's name, is a worse position than either being fully real or being openly, separately synthetic — it's harder to defend under a follow-up question in an interview ("which of these numbers are real?") than a clean "these are their actual disclosed figures, sourced from X" answer. Fabricating numbers under a real company's name in a finance context specifically is also simply the wrong instinct to practice, independent of the interview.

Decision: use only real, cited data. Where more data density was wanted, the fix was a second *real* data source, not synthetic padding.

## Decision 4: Benchmark data source

Considered Destatis (German Federal Statistical Office) retail trade turnover statistics — free and authoritative, but sector-level granularity for optical retail specifically (WZ 47.78.1) wasn't confirmed available in an easily extractable form at the time of research, and its GENESIS-Online database is not straightforward to query programmatically without further investigation.

Considered handelsdaten.de's optical industry revenue time series — real, well-sourced, but paywalled beyond a single visible data point.

Chose ZVA (Zentralverband der Augenoptiker und Optometristen) annual "Branchenbericht" — the German optical/optometry trade association's own free, public annual industry report. This is the primary source that other outlets (including the paywalled ones) ultimately draw from, gives a clean 2021-2025 annual series for total German optical retail industry revenue, store counts, and employment, and lets the project compute Fielmann's growth against the sector's growth rather than presenting Fielmann's numbers in isolation.

## Decision 5: Data granularity

Fielmann does not publicly disclose monthly revenue (normal for a public company of this type — quarterly/annual is the standard disclosure cadence). Rather than manufacture monthly granularity synthetically, the project works at the cadence the real data actually supports: quarterly for the company series (2023 Q1 - 2026 Q2, derived by differencing the cumulative Q1/H1/9M/FY figures each report discloses), annual for the 2021-2022 period where only annual figures were published, and annual for the industry benchmark. This is also more realistic: real corporate FP&A forecasting happens quarterly/annually, not daily.

## Data quality and verification

Every figure is logged with its source document and, where relevant, its exact quoted text, in `data/raw/SOURCES.md`. Two independent arithmetic checks were run before treating the extraction as reliable: (1) the 2025 segment table's external sales sum exactly to Group total consolidated sales; (2) the derived 2023 and 2024 quarterly figures sum exactly back to the audited annual totals. One known figure-level discrepancy (9M/2024 sales cited as both EUR 1,692m and EUR 1,689m across two different reports) is disclosed rather than silently resolved.

## Original handoff (for reference)

The original project brief, written before this pivot, specified a synthetic-data approach. Preserved in the project's claude.ai Project docs and superseded by the decisions above.

## Decision 6: Forecast method — iterating past the first attempt

First implementation was Holt's linear trend (level + trend only), matching the original "keep it simple" brief. Fitting it via SSE minimization degenerated to a near-straight line (alpha and beta both collapsed to their lower bound), which missed something the data actually shows: Q4 total consolidated sales is lower than Q3 in every single year in the series (2023, 2024, 2025), consistently. That's a real, specific pattern — Fielmann is an eyewear/hearing-care retailer, so it doesn't get the Q4 gift-retail bump a typical retailer would — not noise to smooth away.

Upgraded to Holt-Winters additive (level + trend + quarterly seasonal component), still implemented directly with `numpy`/`scipy` rather than a forecasting library, so the model stays inspectable and explainable. In-sample MAPE improved from 3.4% to 2.6%, and the resulting forecast correctly shows Q4/2026 below Q3/2026, matching the historical pattern. This is a good example to walk through in an interview: not "I called a library," but "I tried the simplest thing, checked whether it captured what the data actually does, and upgraded one component when it didn't."

## Decision 7: Build environment could not reach the internet for installs or APIs

The sandboxed environment this project was built in (both the cloud build sandbox and the user's own connected-folder shell) has a network policy that blocks outbound access to package registries (PyPI) and to most external APIs, including Groq's. This meant `statsmodels`, `streamlit`, and the `groq` SDK could not be installed or tested end-to-end during the build.

Handled this by: (1) implementing the forecast model with only `numpy`/`scipy`/`pandas`, all already available, so it could be fully executed and verified during development rather than only written and hoped to work; (2) writing the Groq integration with the plain `requests` library against Groq's documented OpenAI-compatible endpoint rather than its SDK, and confirming the code fails only at the network layer (a clean `ProxyError`/403), not from a bug, by running it against the blocked network and reading the actual error; (3) syntax-checking the Streamlit app and its data-wrangling logic without being able to render it, since `streamlit` itself couldn't be installed in the sandbox. The honest limitation — Streamlit itself was not run end-to-end during the build — is stated plainly in the README rather than implied to be tested, so the first real run on the user's own machine is the true first test.

## Decision 8: .env key naming

The `.env` file was created with the variable name `GROQ_API` rather than the more conventional `GROQ_API_KEY`. Rather than requiring a rename, `src/narrative.py` accepts either name, so the existing `.env` works without modification.

## Decision 9: Groq model swap

`llama-3.3-70b-versatile` (the model named in the original brief) returned a 404 from Groq's API against the actual key in use, even though Groq's own docs still listed it as current - documentation and actual account access don't always agree. Rather than guess a replacement, queried Groq's `/models` endpoint directly with the real key to get the exact list of models it can access, which returned `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, and `qwen/qwen3.8-27b` as the available chat-capable models. Switched to `openai/gpt-oss-120b` (the largest general-purpose one, best suited to a structured-data-to-prose summarization task). The model is now configurable via a `GROQ_MODEL` env var rather than hardcoded, specifically so this class of change doesn't require a code edit next time a model gets retired.

## Decision 10: Final local fixes to get the app running end-to-end

Three more issues surfaced once the app was actually run locally (outside the sandbox that built it, which is the first place it could be):

1. **Truncated narrative output.** `gpt-oss-120b` spends part of its token budget on internal reasoning before the visible answer, so the original `max_tokens: 300` cut the response off mid-sentence. Raised to 1500.
2. **Streamlit deprecation warning.** `use_container_width=True` is deprecated in current Streamlit in favor of `width="stretch"`; updated `app.py` accordingly.
3. **Stale API key in the running Streamlit server.** Streamlit caches environment/module state across reruns within a session, so a `.env` edit doesn't take effect until the server is restarted, not just the page refreshed.

Confirmed end-to-end: the live app now produces the Holt-Winters forecast, the Groq narrative, the plan-vs-actual table and the sector comparison correctly.
