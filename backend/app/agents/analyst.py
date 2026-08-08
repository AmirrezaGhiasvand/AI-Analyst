"""
Analyst agent.

Generates pandas code to answer the question, runs it in the sandbox
(never trusting the LLM's own claims about numbers), and then explains
the REAL computed result in natural language. This is what makes answers
grounded rather than hallucinated — the LLM never gets to just assert a
number; it has to compute it first.

Includes one retry: if generated code fails in the sandbox, the error
is fed back to the LLM for a second attempt before giving up.
"""

from app.agents.state import AgentState
from app.sandbox.executor import execute_code, SandboxExecutionError
from app.services.llm_client import get_llm_client

MAX_CODE_ATTEMPTS = 2

CODE_GEN_SYSTEM_PROMPT = """You are a data analyst agent. Write Python \
pandas code to answer the user's question using a dataframe called `df`.

Rules:
- Assign your final answer to a variable named `result`. This is the \
only thing read back — nothing else you compute is visible unless \
assigned to `result`.
- Only use `pd` (pandas) and `np` (numpy) — no other imports, no file \
or network access, no plotting.
- `result` should be a plain value, dict, list, or a small \
DataFrame/Series — not a huge unfiltered dump of the whole dataset.
- Respond with ONLY the Python code, no markdown fences, no explanation.
"""

EXPLAIN_SYSTEM_PROMPT = """You are a data analyst explaining a computed \
result to a user in plain language. You will be given the user's \
question and the ACTUAL computed result (real data, not a guess).

Rules:
- Base your answer strictly on the given result — do not invent numbers \
not present in it.
- Write in plain prose sentences only. Do NOT use markdown formatting: \
no tables, no pipe characters, no asterisks for bold/italic, no bullet \
lists, no headers. The output is displayed as plain text, so markdown \
syntax would show up as literal stray characters instead of formatting.
- Be explanatory, not just terse: state the direct answer first, then \
briefly explain what it means in context — e.g. which value is higher, \
by how much, or what stands out — in 1-3 sentences total.
- Do not mention code, pandas, or the fact that code was executed.
"""


def _format_columns(columns: dict) -> str:
    return ", ".join(f"{name} ({info['kind']})" for name, info in columns.items())


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # drop opening fence (with optional language tag)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return cleaned.strip()


def analyze(state: AgentState) -> dict:
    client = get_llm_client()

    target = next(
        (ds for ds in state["dataset_context"] if ds["id"] == state["target_dataset_id"]),
        None,
    )
    if target is None:
        return {
            "final_answer": "I couldn't find the dataset needed to answer that question.",
            "analysis_error": "target_dataset_id not found in dataset_context",
        }

    column_summary = _format_columns(target["columns"])
    code_messages = [
        {"role": "system", "content": CODE_GEN_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Dataframe columns: {column_summary}\n"
                f"Row count: {target['row_count']}\n\n"
                f"Question: {state['question']}"
            ),
        },
    ]

    last_error = None
    result = None
    generated_code = None

    for attempt in range(MAX_CODE_ATTEMPTS):
        if attempt > 0:
            # Feed the previous error back so the model can correct itself
            # — this is the "error recovery" step, not a blind retry.
            code_messages.append(
                {
                    "role": "user",
                    "content": (
                        f"That code failed with this error:\n{last_error}\n"
                        "Please fix it and respond with only the corrected code."
                    ),
                }
            )

        raw_code = client.chat(code_messages, temperature=0.1)
        generated_code = _strip_code_fences(raw_code)
        code_messages.append({"role": "assistant", "content": raw_code})

        try:
            result = execute_code(generated_code, target["storage_path"], target["file_type"])
            last_error = None
            break
        except SandboxExecutionError as e:
            last_error = str(e)

    if last_error is not None:
        # Both attempts failed — be honest about it rather than fabricating
        # an answer. This is the grounded-analysis guarantee in practice.
        return {
            "generated_code": generated_code,
            "analysis_error": last_error,
            "final_answer": (
                "I wasn't able to compute an answer to that — the analysis "
                f"failed with: {last_error}"
            ),
        }

    explain_messages = [
        {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Question: {state['question']}\n\nComputed result: {result}",
        },
    ]
    final_answer = client.chat(explain_messages, temperature=0.3)

    return {
        "generated_code": generated_code,
        "execution_result": result,
        "final_answer": final_answer,
    }