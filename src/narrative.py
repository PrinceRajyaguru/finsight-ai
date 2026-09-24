"""
FinSight AI - narrative.py

Turns the forecast + variance numbers into a short, plain-language executive
summary using a Groq-hosted chat model.

Why Groq: free API tier, no local GPU/model hosting needed, fast inference,
and an OpenAI-compatible chat completions endpoint - so this uses the
`requests` library directly against that endpoint rather than adding the
`groq` SDK as a dependency. One fewer thing to install, same result.

Model choice is configurable via the GROQ_MODEL env var (default below)
because Groq periodically deprecates/retires model IDs - if you get a 404
with "model_not_found" or similar, run:

    python -c "import requests,os;from dotenv import load_dotenv;load_dotenv();r=requests.get('https://api.groq.com/openai/v1/models',headers={'Authorization':f'Bearer '+(os.getenv(\"GROQ_API_KEY\") or os.getenv(\"GROQ_API\"))});print([m['id'] for m in r.json()['data']])"

to list the models actually available to your key, then set GROQ_MODEL in
.env to one of those IDs.

Why this prompt structure: the model is given only structured numbers (not
raw opinions) and instructed to write like a finance analyst, not a
marketing writer - short, specific about direction and magnitude, and
required to reference the sector benchmark so the narrative explains *why*
a number looks the way it does, not just what the number is.

Get a free key at https://console.groq.com, then put it in a .env file at
the project root as:
    GROQ_API_KEY=gsk_...
    GROQ_MODEL=openai/gpt-oss-120b   # optional, this is the default

Run directly for a quick check (needs GROQ_API_KEY set and network access):
    python src/narrative.py
"""
from __future__ import annotations

import json
import os

import requests
from dotenv import load_dotenv

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
DEFAULT_MODEL = "openai/gpt-oss-120b"


def _get_api_key() -> str:
    load_dotenv()
    # Accept either name: this project's .env was originally set up with
    # GROQ_API, the more common convention is GROQ_API_KEY - support both.
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API")
    if not key:
        raise RuntimeError(
            "No Groq API key found. Set GROQ_API_KEY (or GROQ_API) in a .env "
            "file at the project root. Get a free key at console.groq.com."
        )
    return key.strip()


def _get_model() -> str:
    load_dotenv()
    return os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip()


def list_available_models(timeout: int = 15) -> list[str]:
    """Diagnostic helper: returns the model IDs actually available to this API key."""
    api_key = _get_api_key()
    response = requests.get(
        GROQ_MODELS_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout
    )
    response.raise_for_status()
    return sorted(m["id"] for m in response.json().get("data", []))


def build_prompt(forecast_result: dict, sector_context: dict | None = None) -> str:
    lines = [
        "You are a finance analyst writing a short executive summary for a",
        "company's leadership. Use only the numbers given below - do not",
        "invent any figures. Write 3-5 sentences, plain language, no bullet",
        "points, no headers. State the forecast direction and magnitude,",
        "compare it to the prior-year same quarter, and if sector benchmark",
        "data is provided, explicitly compare the company's growth to the",
        "sector's growth to explain whether the company is gaining or losing",
        "ground. Do not use hedge words like 'may' or 'could' about the",
        "historical numbers themselves - they are actuals or a stated model",
        "forecast, not speculation. It is fine to caveat the forecast itself",
        "as model-based.",
        "",
        f"Model used: {forecast_result['model']}",
        f"Last actual quarter: {forecast_result['history_last_actual']['period']} "
        f"= EUR {forecast_result['history_last_actual']['value_eur_m']}m",
        "Forecast:",
    ]
    for row in forecast_result["forecast"]:
        lines.append(
            f"  {row['period']}: EUR {row['forecast_eur_m']}m "
            f"(prior-year same quarter: EUR {row['prior_year_same_quarter_eur_m']}m, "
            f"YoY growth: {row['yoy_growth_pct']}%)"
        )
    if sector_context:
        lines.append("")
        lines.append(
            f"Sector benchmark (German optical retail industry, ZVA, "
            f"{sector_context['year']}): {sector_context['growth_pct']}% revenue growth."
        )
    return "\n".join(lines)


def generate_narrative(
    forecast_result: dict, sector_context: dict | None = None, timeout: int = 30
) -> str:
    api_key = _get_api_key()
    model = _get_model()
    prompt = build_prompt(forecast_result, sector_context)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1500,  # gpt-oss spends part of the budget on reasoning tokens
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL, headers=headers, json=payload, timeout=timeout
    )
    if not response.ok:
        # Surface Groq's own error body (e.g. model_not_found / decommissioned)
        # instead of a generic "404 Client Error" with no context.
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(
            f"Groq API error {response.status_code} for model '{model}': {detail}"
        )
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    from forecast import forecast_next_quarters, load_quarterly_series

    df = load_quarterly_series()
    result = forecast_next_quarters(df, steps=2)
    print("Prompt sent to Groq:\n")
    print(build_prompt(result, sector_context={"year": 2025, "growth_pct": 0.6}))
    print("\n--- Calling Groq API ---\n")
    try:
        narrative = generate_narrative(result, sector_context={"year": 2025, "growth_pct": 0.6})
        print(narrative)
    except Exception as exc:  # noqa: BLE001
        print(f"Groq call failed: {exc}")
        print("\nTrying to list models available to this key...")
        try:
            models = list_available_models()
            print("Available models:")
            for m in models:
                print(" -", m)
        except Exception as exc2:  # noqa: BLE001
            print(f"Could not list models either: {exc2}")
