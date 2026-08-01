"""
Sandboxed code execution.

Runs Analyst-agent-generated code in a separate subprocess, isolated
from the main FastAPI process, with:
- A timeout (kills runaway/infinite-loop code)
- Restricted builtins (no file system access, no imports beyond
  pandas/numpy, no subprocess/os access)
- The dataframe loaded fresh inside the subprocess from the dataset's
  storage_path — the generated code never sees a raw file path it could
  redirect elsewhere

This is "light but real" isolation — a subprocess boundary, not full
Docker/OS-level isolation. That's a deliberate scope decision: it stops
accidental damage and most malicious patterns without the operational
overhead of spinning up a container per query. See README for the
documented trade-off.
"""

import json
import multiprocessing
import queue

import numpy as np
import pandas as pd

EXECUTION_TIMEOUT_SECONDS = 15

# Only these names are available to generated code. Notably absent:
# os, subprocess, open, __import__, sys, socket — anything that could
# touch the filesystem, network, or spawn processes.
_ALLOWED_BUILTINS = {
    "len",
    "range",
    "sum",
    "min",
    "max",
    "sorted",
    "list",
    "dict",
    "set",
    "tuple",
    "str",
    "int",
    "float",
    "bool",
    "abs",
    "round",
    "enumerate",
    "zip",
    "map",
    "filter",
    "print",
}


class SandboxExecutionError(Exception):
    """Raised when sandboxed code fails, times out, or produces an
    unserializable result. Message is safe to show the user/agent."""


def _load_dataframe_in_subprocess(file_path: str, file_type: str) -> pd.DataFrame:
    """
    Mirrors profiling_service's reader logic. Duplicated (rather than
    imported) deliberately — keeping the subprocess's dependencies
    minimal and explicit makes it easier to reason about exactly what
    this isolated process can do.
    """
    if file_type == "csv":
        return pd.read_csv(file_path)
    elif file_type in ("xlsx", "xls"):
        return pd.read_excel(file_path)
    elif file_type == "json":
        return pd.read_json(file_path)
    elif file_type == "parquet":
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file type for execution: '{file_type}'")


def _run_in_subprocess(
    code: str, file_path: str, file_type: str, result_queue: multiprocessing.Queue
):
    """
    Runs INSIDE the child process. Loads the dataframe, executes the
    generated code with a restricted global namespace, and puts the
    result (or an error) on the queue to send back to the parent.
    """
    try:
        df = _load_dataframe_in_subprocess(file_path, file_type)

        safe_builtins = {
            name: __builtins__[name]
            if isinstance(__builtins__, dict)
            else getattr(__builtins__, name)
            for name in _ALLOWED_BUILTINS
        }

        exec_globals = {
            "__builtins__": safe_builtins,
            "pd": pd,
            "np": np,
            "df": df,
        }
        exec_locals: dict = {}

        exec(code, exec_globals, exec_locals)

        result = exec_locals.get("result", None)

        # Normalize common pandas/numpy return types into plain JSON-safe
        # Python values — the agent code shouldn't have to worry about
        # serialization, just assign to `result`.
        if isinstance(result, pd.DataFrame):
            result = json.loads(result.to_json(orient="records", date_format="iso"))
        elif isinstance(result, pd.Series):
            result = json.loads(result.to_json(date_format="iso"))
        elif isinstance(result, (np.integer, np.floating)):
            result = result.item()
        elif isinstance(result, np.ndarray):
            result = result.tolist()

        result_queue.put({"success": True, "result": result})
    except Exception as e:
        result_queue.put({"success": False, "error": f"{type(e).__name__}: {e}"})


def execute_code(code: str, file_path: str, file_type: str) -> dict:
    """
    Executes `code` against the dataset at `file_path` in an isolated
    subprocess. The code must assign its answer to a variable named
    `result` — that's the contract the Analyst agent's prompt enforces.

    Returns the result dict on success.
    Raises SandboxExecutionError on failure or timeout.
    """
    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_run_in_subprocess, args=(code, file_path, file_type, result_queue)
    )
    process.start()
    process.join(timeout=EXECUTION_TIMEOUT_SECONDS)

    if process.is_alive():
        process.terminate()
        process.join()
        raise SandboxExecutionError(
            f"Code execution exceeded {EXECUTION_TIMEOUT_SECONDS}s timeout."
        )

    try:
        output = result_queue.get_nowait()
    except queue.Empty:
        raise SandboxExecutionError(
            "Execution ended without producing a result (the process may have crashed)."
        )

    if not output["success"]:
        raise SandboxExecutionError(output["error"])

    return output["result"]
