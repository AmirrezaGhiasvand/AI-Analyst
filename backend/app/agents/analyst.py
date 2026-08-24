from app.agents.state import AgentState
from app.sandbox.executor import execute_code, SandboxExecutionError
from app.services.llm_client import get_llm_client

MAX_CODE_ATTEMPTS = 2

CODE_GEN_SYSTEM_PROMPT = """You are a data analyst agent. Write Python \
pandas code to answer the user's question using a dataframe called `df`.

Rules:
- Assign your final answer to a variable named `result`.
- Only use `pd` (pandas) and `np` (numpy) — no other imports, no file or network access.
- Respond with ONLY the Python code, no markdown fences, no explanation.
"""

EXPLAIN_SYSTEM_PROMPT = """You are a data analyst explaining a computed \
result to a user in plain language. You will be given the user's \
question and the ACTUAL computed result (real data, not a guess).

Rules:
- Base your answer strictly on the given result — do not invent numbers not present in it.
- Write in plain prose sentences only. Do NOT use markdown formatting: \
no tables, no pipe characters, no asterisks for bold/italic, no bullet lists, no headers.
- Be explanatory, not just terse: state the direct answer first, then \
briefly explain what it means in context, in 1-3 sentences total.
- Do not mention code, pandas, or the fact that code was executed.
"""


def _format_columns(columns: dict) -> str:
    return ", ".join(f"{name} ({info['kind']})" for name, info in columns.items())


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return cleaned.strip()


def analyze(state: AgentState) -> dict:
    client = get_llm_client()
    target = next((ds for ds in state["dataset_context"] if ds["id"] == state["target_dataset_id"]), None)
    if target is None:
        return {"final_answer": "I couldn't find the dataset needed to answer that question.", "analysis_error": "target not found"}

    column_summary = _format_columns(target["columns"])
    code_messages = [
        {"role": "system", "content": CODE_GEN_SYSTEM_PROMPT},
        {"role": "user", "content": f"Dataframe columns: {column_summary}\nRow count: {target['row_count']}\n\nQuestion: {state['question']}"},
    ]

    last_error = None
    result = None
    generated_code = None

    for attempt in range(MAX_CODE_ATTEMPTS):
        if attempt > 0:
            code_messages.append({"role": "user", "content": f"That code failed with this error:\n{last_error}\nPlease fix it and respond with only the corrected code."})

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
        return {"generated_code": generated_code, "analysis_error": last_error, "final_answer": f"I wasn't able to compute an answer to that — the analysis failed with: {last_error}"}

    explain_messages = [
        {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {state['question']}\n\nComputed result: {result}"},
    ]
    final_answer = client.chat(explain_messages, temperature=0.3)

    return {"generated_code": generated_code, "execution_result": result, "final_answer": final_answer}