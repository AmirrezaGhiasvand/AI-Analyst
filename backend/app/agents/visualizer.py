"""
Visualizer agent.

Takes the Analyst's already-computed, already-safe result and decides
whether a chart adds value, and if so, what type. The LLM only makes
that small decision (chart type + title) — the actual chart is built by
OUR OWN plotting code from the real data, never by LLM-generated
plotting code. This keeps plotting logic reliable and testable, and
matches the earlier decision to keep the sandbox free of extra libraries.

v1 scope: handles two result shapes coming out of the sandbox —
(1) a dict of category -> numeric value (e.g. from a Series/.to_dict()),
and (2) a list of records that all share exactly two keys, one numeric
and one not (e.g. from groupby().size().reset_index()) — this second
shape is extremely common since it's the natural pandas pattern for
"count/aggregate then produce a table". Both get normalized into the
same label->value mapping before charting. Anything more complex (3+
columns, mixed shapes) is not charted in v1.
"""

import json

import plotly.graph_objects as go

from app.agents.state import AgentState
from app.services.llm_client import get_llm_client

SYSTEM_PROMPT = """You decide whether a computed result should be shown \
as a chart, and if so, what type. Respond with ONLY a JSON object, no \
markdown fences, in exactly this shape:

{"should_visualize": true or false, "chart_type": "bar" or "line" or "pie" or null, "title": "<short chart title or null>"}

Use "bar" for comparing values across categories (the most common case). \
Use "line" only if the categories represent a clear time/sequence order. \
Use "pie" only for a small number of categories (<=6) showing parts of a whole. \
Set should_visualize=false for results that don't meaningfully benefit \
from a chart (e.g. only 2-3 near-identical values, or the question \
didn't ask for a comparison).
"""


def _is_numeric_field(records: list[dict], key: str) -> bool:
    return all(
        isinstance(r.get(key), (int, float)) and not isinstance(r.get(key), bool)
        for r in records
    )


def _extract_chartable_data(result) -> dict | None:
    """
    Normalizes either supported result shape into one label->value dict,
    or returns None if the result isn't chartable. Doing this narrowing
    with explicit isinstance checks (not a separate boolean-returning
    helper) keeps the type checker able to track what `result` actually is.
    """
    if isinstance(result, dict) and len(result) >= 2:
        if all(
            isinstance(v, (int, float)) and not isinstance(v, bool)
            for v in result.values()
        ):
            return result
        return None

    if (
        isinstance(result, list)
        and len(result) >= 2
        and all(isinstance(r, dict) for r in result)
    ):
        keys = set(result[0].keys())
        if len(keys) != 2 or not all(set(r.keys()) == keys for r in result):
            return None

        key_a, key_b = tuple(keys)
        a_numeric, b_numeric = (
            _is_numeric_field(result, key_a),
            _is_numeric_field(result, key_b),
        )

        if a_numeric and not b_numeric:
            label_key, value_key = key_b, key_a
        elif b_numeric and not a_numeric:
            label_key, value_key = key_a, key_b
        else:
            # Both or neither numeric — no clear label/value split, skip.
            return None

        return {str(r[label_key]): r[value_key] for r in result}

    return None


def _build_figure(chart_type: str, title: str, data: dict) -> str:
    """Builds the actual Plotly figure from real data using our own
    trusted code. Returns the figure as a JSON string — this same JSON
    spec is what the frontend renders interactively via Plotly.js, and
    what a static image export (for PDF reports) will be generated from
    later via kaleido."""
    labels = list(data.keys())
    values = list(data.values())

    if chart_type == "pie":
        trace = go.Pie(labels=labels, values=values)
    elif chart_type == "line":
        trace = go.Scatter(x=labels, y=values, mode="lines+markers")
    else:  # default to bar for "bar" or any unrecognized type
        trace = go.Bar(x=labels, y=values)

    figure = go.Figure(data=[trace], layout={"title": title})
    figure_json = figure.to_json()
    if figure_json is None:
        # Plotly's to_json() is typed as possibly returning None, though a
        # valid figure never actually triggers this in practice. Raising
        # here converts it into the same "charting failed" path that
        # visualize() already handles gracefully (falls back to no chart).
        raise ValueError("Plotly figure serialization returned None")
    return figure_json


def visualize(state: AgentState) -> dict:
    result = state.get("execution_result")

    chart_data = _extract_chartable_data(result)
    if chart_data is None:
        return {"chart_json": None}

    client = get_llm_client()
    sample_keys = list(chart_data.keys())[:10]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question: {state['question']}\n"
                f"Result categories: {sample_keys}\n"
                f"Number of categories: {len(chart_data)}"
            ),
        },
    ]

    raw_response = client.chat(messages, temperature=0.1)

    try:
        cleaned = (
            raw_response.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        decision = json.loads(cleaned)
    except json.JSONDecodeError:
        # If the decision can't be parsed, fail safe into "no chart"
        # rather than guessing or crashing — a missing chart is a minor
        # degradation, not a broken response.
        return {"chart_json": None}

    if not decision.get("should_visualize"):
        return {"chart_json": None}

    chart_type = decision.get("chart_type") or "bar"
    title = decision.get("title") or state["question"]

    try:
        chart_json = _build_figure(chart_type, title, chart_data)
    except Exception:
        # Charting is an enhancement on top of an already-valid answer —
        # a plotting bug shouldn't take down a response that otherwise
        # succeeded.
        return {"chart_json": None}

    return {"chart_json": chart_json}
