"""
Profiling service.

Reads a dataset's raw file from disk and extracts structural facts about
it: column names/types, row/column counts, null counts, and a small
preview sample. This is the "quick glance" step that runs once right
after upload, so later questions can use cheap stored metadata instead
of re-parsing the raw file every time.

Deliberately lightweight — deep stats (correlations, outliers, trends)
are NOT computed here. Those get computed on-demand later by the
Analyst agent, only when a question actually needs them.
"""

import json
import math

import numpy as np
import pandas as pd
from app.models.dataset import Dataset

# Only read a bounded number of rows for profiling. For very large files,
# reading the entire dataset just to infer types/nulls is wasteful — a
# large sample is statistically enough to describe the shape of the data.
PROFILE_SAMPLE_ROWS = 50_000
PREVIEW_ROWS = 5


class ProfilingError(Exception):
    """Raised when a file can't be read/profiled despite passing upload
    validation (e.g. a .csv extension on a file that isn't valid CSV)."""


def _load_dataframe(dataset: Dataset) -> pd.DataFrame:
    """Reads the dataset's file into a DataFrame based on its file_type."""
    path = dataset.storage_path
    try:
        if dataset.file_type == "csv":
            return pd.read_csv(path, nrows=PROFILE_SAMPLE_ROWS)
        elif dataset.file_type in ("xlsx", "xls"):
            return pd.read_excel(path, nrows=PROFILE_SAMPLE_ROWS)
        elif dataset.file_type == "json":
            return pd.read_json(path)
        elif dataset.file_type == "parquet":
            return pd.read_parquet(path)
        else:
            raise ProfilingError(
                f"No reader implemented for file type '{dataset.file_type}'"
            )
    except ProfilingError:
        raise
    except Exception as e:
        # pandas raises many different exception types depending on what's
        # wrong with the file (ParserError, ValueError, UnicodeDecodeError...).
        # We collapse them into one domain error with the original message,
        # since the caller only needs to know "profiling failed and why".
        raise ProfilingError(f"Failed to read file as {dataset.file_type}: {e}")


def _infer_column_kind(series: pd.Series) -> str:
    """
    Buckets a pandas dtype into a small set of human-meaningful categories.
    This is what the Planner agent will eventually read to decide, e.g.,
    'this is numeric, a groupby/aggregation makes sense here'.
    """
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # Heuristic: object columns with few unique values relative to row
    # count are likely categorical (e.g. "status": active/inactive),
    # rather than free-text.
    non_null = series.dropna()
    if len(non_null) > 0:
        unique_ratio = non_null.nunique() / len(non_null)
        if unique_ratio < 0.5:
            return "categorical"

    return "text"


def _safe_stat(value):
    """
    Converts numpy/pandas scalar stats into plain JSON-safe Python values.
    NaN isn't valid JSON, so it's converted to None.
    """
    if value is None:
        return None
    if isinstance(value, np.generic):  # numpy scalar (e.g. numpy.int64)
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _profile_column(series: pd.Series) -> dict:
    kind = _infer_column_kind(series)
    null_count = int(series.isna().sum())

    profile = {
        "kind": kind,
        "null_count": null_count,
        "unique_count": int(series.nunique(dropna=True)),
    }

    if kind == "numeric":
        desc = series.describe()
        profile["min"] = _safe_stat(desc.get("min"))
        profile["max"] = _safe_stat(desc.get("max"))
        profile["mean"] = _safe_stat(desc.get("mean"))
        profile["median"] = _safe_stat(series.median())
    elif kind == "categorical":
        top_values = series.value_counts(dropna=True).head(5)
        profile["top_values"] = {str(k): int(v) for k, v in top_values.items()}

    return profile


def profile_dataset(dataset: Dataset) -> dict:
    """
    Profiles a dataset and returns a JSON-serializable dict describing it.
    Raises ProfilingError if the file can't be read.
    """
    df = _load_dataframe(dataset)

    columns = {}
    for col_name in df.columns:
        columns[str(col_name)] = _profile_column(df[col_name])

    preview = json.loads(
        df.head(PREVIEW_ROWS).to_json(orient="records", date_format="iso")
    )

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns,
        "preview_rows": preview,
    }
