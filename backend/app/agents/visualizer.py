"""
Visualizer agent.

Normalizes the Analyst's computed result into a list of named-field
records, describes the available fields to the LLM, and asks it to pick
a chart type plus which field is the x-axis and which field(s) are the
plotted series. If the user's question explicitly names a chart type,
that request is honored over the LLM's own judgment.

The LLM only ever picks FIELD NAMES and a chart type — it never invents
data. Our own code extracts the real values for the chosen fields and
builds the final chart data. This keeps the "grounded, not hallucinated"
guarantee: a chart can only ever show numbers that were actually computed.

Output is a library-agnostic ChartSpec (see schemas/chart.py) — NOT
Plotly's format. This can be consumed directly by any frontend charting
library (e.g. Recharts) without translation, and is also what
report_service.py converts into a Plotly figure for static PDF export.
Plotly is purely an internal PDF-rendering detail now.
"""

import json
from typing import Optional, Any

import numpy as np

from app.agents.state import AgentState
from app.schemas.chart import ChartSpec
from app.services.llm_client import get_llm_client

SYSTEM_PROMPT = """You choose how to visualize a computed data result. \
You will be given the user's question and a description of the \
available fields (name, inferred type, and sample values).

Respond with ONLY a JSON object, no markdown fences, in exactly this shape:

{"chart_type": "bar" or "line" or "area" or "pie" or "scatter" or "histogram", \
"x_key": "<field name>", "series_keys": ["<field name>", ...], \
"title": "<short title>", "x_label": "<axis label or null>", "y_label": "<axis label or null>"}

Rules:
- IMPORTANT: if the user's question explicitly names a chart type (words \
like "bar chart", "pie chart", "scatter plot", "line graph", \
"histogram", "distribution"), you MUST use that type — do not override \
an explicit request with your own judgment, unless it is genuinely \
incompatible with the available fields.
- "bar": general category comparison (the default/safest choice when unsure).
- "line" or "area": use when x_key represents a clear sequence or time order.
- "pie": only for a small number of categories (<=6) representing parts of a whole.
- "scatter": requires TWO numeric fields (x_key and one numeric series_key) \
with no natural categorical grouping.
- "histogram": use when a field contains many individual raw numeric \
values (a distribution), not pre-aggregated categories. Set series_keys \
to the single field to compute a distribution over — the actual \
binning is done separately, you're only picking which field.
- series_keys can contain MULTIPLE field names only for grouped/multi- \
series bar or multi-line comparisons where that makes sense (e.g. \
comparing two numeric fields across the same categories). Otherwise \
use exactly one.
- x_key and all series_keys MUST be field names that actually appear in \
the field list given below — never invent a field name.
"""

_HISTOGRAM_BINS = 10


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _normalize_to_records(result) -> Optional[list[dict]]:
    """
    Converts any of the Analyst's possible result shapes into a list of
    named-field records, or None if there's nothing chartable at all
    (e.g. a single text string, or a list with no numeric content).
    """
    if isinstance(result, dict):
        numeric_items = {k: v for k, v in result.items() if _is_number(v)}
        if len(numeric_items) < 2:
            return None
        return [{"category": k, "value": v} for k, v in numeric_items.items()]

    if isinstance(result, list) and len(result) >= 2:
        if all(isinstance(r, dict) for r in result):
            has_numeric_field = any(
                _is_number(v) for r in result for v in r.values()
            )
            return result if has_numeric_field else None

        if all(_is_number(r) for r in result):
            return [{"value": v} for v in result]

    return None


def _describe_fields(records: list[dict]) -> dict[str, str]:
    """Infers a simple type (numeric/categorical) per field, from a
    sample of records, for describing to the LLM."""
    field_names: set[str] = set()
    for r in records[:50]:
        field_names.update(r.keys())

    field_types = {}
    for name in field_names:
        values = [r[name] for r in records if name in r and r[name] is not None]
        field_types[name] = "numeric" if values and all(_is_number(v) for v in values) else "categorical"
    return field_types


def _build_histogram_data(records: list[dict], field: str) -> list[dict]:
    """Bins raw numeric values into a bar-shaped distribution — done with
    real math here, not left to the LLM to approximate."""
    values = [r[field] for r in records if field in r and _is_number(r[field])]
    counts, edges = np.histogram(values, bins=_HISTOGRAM_BINS)
    return [
        {"range": f"{edges[i]:.1f}-{edges[i + 1]:.1f}", "count": int(counts[i])}
        for i in range(len(counts))
    ]


def visualize(state: AgentState) -> dict:
    result = state.get("execution_result")

    records = _normalize_to_records(result)
    if records is None:
        return {"chart_json": None}

    field_types = _describe_fields(records)

    client = get_llm_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question: {state['question']}\n"
                f"Available fields: {json.dumps(field_types)}\n"
                f"Sample records: {json.dumps(records[:5], default=str)}\n"
                f"Total records: {len(records)}"
            ),
        },
    ]

    raw_response = client.chat(messages, temperature=0.1)

    try:
        cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        decision = json.loads(cleaned)
        chart_type = decision["chart_type"]
        x_key = decision["x_key"]
        series_keys = decision["series_keys"]
        if not isinstance(series_keys, list) or not series_keys:
            raise ValueError("series_keys must be a non-empty list")
    except (json.JSONDecodeError, KeyError, ValueError):
        return {"chart_json": None}

    # Validate the LLM's field choices against what actually exists —
    # never trust field names it didn't verify against the real data.
    valid_fields = set(field_types.keys())
    if x_key not in valid_fields or not all(k in valid_fields for k in series_keys):
        return {"chart_json": None}

    title = decision.get("title") or state["question"]
    x_label = decision.get("x_label")
    y_label = decision.get("y_label")

    try:
        if chart_type == "histogram":
            data = _build_histogram_data(records, series_keys[0])
            chart = ChartSpec(
                chart_type="histogram", title=title, x_label=x_label, y_label=y_label or "Count",
                x_key="range", series_keys=["count"], data=data,
            )
        else:
            # Project only the chosen fields from the REAL records — the
            # LLM picked field names, but every value shown is the
            # actual computed data, never something the LLM generated.
            data = [
                {k: r.get(k) for k in [x_key, *series_keys] if k in r}
                for r in records
            ]
            chart = ChartSpec(
                chart_type=chart_type, title=title, x_label=x_label, y_label=y_label,
                x_key=x_key, series_keys=series_keys, data=data,
            )
    except Exception:
        # Any construction failure degrades to no chart — the text
        # answer already succeeded and shouldn't be blocked by this.
        return {"chart_json": None}

    return {"chart_json": chart.model_dump_json()}