import json
import multiprocessing
import queue

import pandas as pd
import numpy as np

EXECUTION_TIMEOUT_SECONDS = 15

_ALLOWED_BUILTINS = {
    "len", "range", "sum", "min", "max", "sorted", "list", "dict", "set",
    "tuple", "str", "int", "float", "bool", "abs", "round", "enumerate",
    "zip", "map", "filter", "print",
}


class SandboxExecutionError(Exception):
    pass


def _load_dataframe_in_subprocess(file_path: str, file_type: str) -> pd.DataFrame:
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


def _run_in_subprocess(code: str, file_path: str, file_type: str, result_queue):
    try:
        df = _load_dataframe_in_subprocess(file_path, file_type)
        safe_builtins = {name: __builtins__[name] if isinstance(__builtins__, dict) else getattr(__builtins__, name)
                          for name in _ALLOWED_BUILTINS}
        exec_globals = {"__builtins__": safe_builtins, "pd": pd, "np": np, "df": df}
        exec_locals: dict = {}
        exec(code, exec_globals, exec_locals)
        result = exec_locals.get("result", None)

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
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_run_in_subprocess, args=(code, file_path, file_type, result_queue))
    process.start()
    process.join(timeout=EXECUTION_TIMEOUT_SECONDS)

    if process.is_alive():
        process.terminate()
        process.join()
        raise SandboxExecutionError(f"Code execution exceeded {EXECUTION_TIMEOUT_SECONDS}s timeout.")

    try:
        output = result_queue.get_nowait()
    except queue.Empty:
        raise SandboxExecutionError("Execution ended without producing a result.")

    if not output["success"]:
        raise SandboxExecutionError(output["error"])

    return output["result"]