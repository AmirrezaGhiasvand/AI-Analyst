"""
Planner agent.

Reads the user's question plus dataset metadata and conversation history,
then decides: does this need real computation (route to the Analyst),
or can it be answered directly from schema/metadata we already have
(e.g. "what columns does this have" doesn't need code execution)?
"""

import json

from app.agents.state import AgentState, DatasetContext
from app.services.llm_client import get_llm_client

SYSTEM_PROMPT = """You are the planning agent for a data analytics assistant.

Given a user's question and information about their available datasets, \
decide how to answer it. Respond with ONLY a JSON object, no markdown \
fences, no explanation outside the JSON, in exactly this shape:

{"route": "direct" or "analyze", "target_dataset_id": "<id or null>", "direct_answer": "<text or null>"}

Rules:
- Use "direct" ONLY when the question can be fully answered from the \
dataset metadata already provided below (e.g. "what columns does this \
have", "how many rows", "what datasets are in this project"). Put the \
answer in "direct_answer" and set "target_dataset_id" to null.
- Use "analyze" for anything requiring computation on the actual data: \
aggregations, filters, averages, comparisons, trends, counts of specific \
values, etc. Set "target_dataset_id" to the id of the most relevant \
dataset from the list below, and set "direct_answer" to null.
- If multiple datasets seem relevant, pick the single most relevant one \
— the Analyst agent will only see that one dataset's data.
"""


def _format_dataset_context(dataset_context: list[DatasetContext]) -> str:
    lines = []
    for ds in dataset_context:
        col_summary = ", ".join(
            f"{name} ({info['kind']})" for name, info in ds["columns"].items()
        )
        lines.append(
            f"- Dataset id={ds['id']}, filename={ds['filename']}, "
            f"rows={ds['row_count']}, columns=[{col_summary}]"
        )
    return "\n".join(lines) if lines else "(no ready datasets in this project)"


def plan(state: AgentState) -> dict:
    client = get_llm_client()

    dataset_summary = _format_dataset_context(state["dataset_context"])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Recent conversation gives the Planner context for follow-up
    # questions (e.g. "now break that down by region").
    messages.extend(state["conversation_history"])
    messages.append(
        {
            "role": "user",
            "content": f"Available datasets:\n{dataset_summary}\n\nQuestion: {state['question']}",
        }
    )

    raw_response = client.chat(messages, temperature=0.1)

    try:
        # Models sometimes wrap JSON in markdown fences despite instructions
        # not to — strip those defensively before parsing.
        cleaned = (
            raw_response.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        decision = json.loads(cleaned)
        route = decision.get("route")
        if route not in ("direct", "analyze"):
            raise ValueError(f"Unexpected route value: {route}")
    except (json.JSONDecodeError, ValueError):
        # If the Planner's output can't be parsed, fail safe into a
        # direct response asking the user to rephrase, rather than
        # crashing or guessing at a route.
        return {
            "route": "direct",
            "target_dataset_id": None,
            "final_answer": (
                "I had trouble understanding how to approach that question. "
                "Could you rephrase it?"
            ),
        }

    if route == "direct":
        return {
            "route": "direct",
            "target_dataset_id": None,
            "final_answer": decision.get("direct_answer")
            or "I don't have an answer for that.",
        }
    else:
        return {
            "route": "analyze",
            "target_dataset_id": decision.get("target_dataset_id"),
        }
