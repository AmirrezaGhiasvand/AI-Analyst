"""
Chart data contract.

Deliberately library-agnostic — NOT Plotly's trace/layout format. This
is a plain "wide" data shape that maps directly onto how Recharts (the
frontend's charting library) actually consumes data: a `data` array of
row objects, plus the key name(s) to plot from each row.

Example (simple bar/line/area/pie):
    {"chart_type": "bar", "title": "...", "x_key": "x", "series_keys": ["y"],
     "data": [{"x": "Engineering", "y": 91500.0}, {"x": "Sales", "y": 60000.0}]}

Example (grouped/multi-series bar or multi-line):
    {"chart_type": "bar", "title": "...", "x_key": "x", "series_keys": ["2023", "2024"],
     "data": [{"x": "Q1", "2023": 100, "2024": 120}, {"x": "Q2", "2023": 110, "2024": 130}]}

Example (scatter):
    {"chart_type": "scatter", "title": "...", "x_key": "x", "series_keys": ["y"],
     "data": [{"x": 5.2, "y": 91500.0}, {"x": 3.1, "y": 60000.0}]}

This same structure is what report_service.py converts into a Plotly
figure for static PDF export — Plotly is purely an internal PDF-rendering
detail now, never exposed to the frontend.
"""

from typing import Optional, Any
from pydantic import BaseModel


class ChartSpec(BaseModel):
    chart_type: str  # "bar" | "line" | "area" | "pie" | "scatter" | "histogram"
    title: str
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_key: str  # the field name in each `data` row to use as the category/x-axis
    series_keys: list[str]  # field name(s) in each `data` row to plot as value(s)
    data: list[dict[str, Any]]