import json

from app.agents.state import AgentState, DatasetContext
from app.services.llm_client import get_llm_client

SYSTEM_PROMPT = """You are the planning agent for a data analytics assistant.

Given a user's question and information about their available datasets, \
decide how to answer it. Respond with ONLY a JSON object, no markdown \
fences, no explanation outside the JSON, in exactly this shape:

{"route": "direct" or "analyze" or "report", "target_dataset_id": "<id or null>", "direct_answer": "<text or null>"}

Rules:
- Use "report" when the user explicitly asks for a report, summary \
document, PDF, or export of the analysis (e.g. "generate a report", \
"can I get a PDF of this", "export this session", "summarize this as a \
document"). Put a brief, friendly confirmation in "direct_answer" (e.g. \
"I've prepared your report — you can download it below.") and set \
"target_dataset_id" to null. Do not use this route for anything else.
- Use "direct" for anything that does NOT require running code against \
the actual data. This covers THREE kinds of questions:
  1. Dataset metadata (e.g. "what columns does this have", "how many rows").
  2. Greetings, small talk, thanks, or questions about what you can help \
with (e.g. "hi", "what can you do?"). Give a brief, warm, genuinely \
helpful reply. If datasets are listed below, mention 1-2 concrete example \
questions using their REAL column names, so the reply feels grounded \
rather than generic. If NO datasets are listed below, do NOT invent \
example questions about data that doesn't exist — instead, tell the user \
to upload a dataset to get started.
  3. Anything else answerable without computation — general questions, \
clarifications, or requests you can respond to directly.
  Put your reply in "direct_answer" and set "target_dataset_id" to null. \
Never leave "direct_answer" empty — always give a real, helpful response.
- Use "analyze" ONLY for questions requiring computation on the actual \
data: aggregations, filters, averages, comparisons, trends, counts of \
specific values, etc. Set "target_dataset_id" to the id of the most \
relevant dataset from the list below, and set "direct_answer" to null.
- If multiple datasets seem relevant to an "analyze" question, pick the \
single most relevant one based on the question's wording — the Analyst \
agent will only see that one dataset's data. Don't ask for clarification; \
make the best reasonable choice.
- Use the conversation history below for context on follow-up questions \
(e.g. "now break that down by region" refers back to the previous answer).
"""


def _format_dataset_context(dataset_context: list[DatasetContext]) -> str:
    lines = []
    for ds in dataset_context:
        col_summary = ", ".join(f"{name} ({info['kind']})" for name, info in ds["columns"].items())
        lines.append(f"- Dataset id={ds['id']}, filename={ds['filename']}, rows={ds['row_count']}, columns=[{col_summary}]")
    return "\n".join(lines) if lines else "(no ready datasets in this project)"


def plan(state: AgentState) -> dict:
    client = get_llm_client()
    dataset_summary = _format_dataset_context(state["dataset_context"])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(state["conversation_history"])
    messages.append({"role": "user", "content": f"Available datasets:\n{dataset_summary}\n\nQuestion: {state['question']}"})

    raw_response = client.chat(messages, temperature=0.1)

    try:
        cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        decision = json.loads(cleaned)
        route = decision.get("route")
        if route not in ("direct", "analyze", "report"):
            raise ValueError(f"Unexpected route value: {route}")
    except (json.JSONDecodeError, ValueError):
        return {
            "route": "direct", "target_dataset_id": None,
            "final_answer": "I had trouble understanding how to approach that question. Could you rephrase it?",
        }

    if route in ("direct", "report"):
        fallback = (
            "I'm not sure how to answer that directly — try asking about "
            "your data, like requesting an average, a breakdown by category, "
            "or a comparison across columns."
        )
        return {"route": route, "target_dataset_id": None, "final_answer": decision.get("direct_answer") or fallback}
    else:
        return {"route": "analyze", "target_dataset_id": decision.get("target_dataset_id")}