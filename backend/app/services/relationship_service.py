"""
Relationship detection service.

Compares columns across every pair of ready datasets in a project and
scores how likely they represent the same real-world entity (e.g.
orders.customer_id <-> customers.id), using three signals:

1. Name similarity  — do the column names look alike?
2. Type compatibility — are the column kinds even comparable?
3. Value overlap    — do the actual values appear in both columns?
                       This is the strongest signal and the one that
                       catches relationships even when names don't match.

Runs after every upload, re-evaluating the whole project, since a newly
uploaded file might relate to ones already there.
"""

import difflib
import json
import re
from itertools import combinations

from app.models.dataset import Dataset
from app.models.relationship import DatasetRelationship
from app.services.profiling_service import load_dataframe
from sqlalchemy.orm import Session

# Only these column kinds are meaningful join candidates. Datetime and
# boolean columns are excluded — joining on "is this row from the same
# timestamp" or "both true/false" isn't a real relationship signal.
CANDIDATE_KINDS = {"numeric", "categorical", "text"}

# A relationship is only kept if actual data overlaps this much between
# the two columns — this is what prevents false positives from columns
# that merely have similar names but unrelated data.
MIN_VALUE_OVERLAP = 0.3
MIN_CONFIDENCE = 0.5

# Weights for combining signals into one confidence score. Value overlap
# is weighted higher since it's evidence from the actual data, not just
# a naming convention that could be coincidental.
NAME_WEIGHT = 0.3
OVERLAP_WEIGHT = 0.7


def _normalize_column_name(name: str) -> str:
    """
    Strips common id/key suffixes and non-alphanumeric characters so
    'customer_id' and 'CustomerID' normalize to the same comparable form.
    """
    normalized = re.sub(r"[^a-z0-9]", "", name.lower())
    for suffix in ("id", "key", "pk", "fk"):
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized or name.lower()


def _name_similarity(name_a: str, name_b: str) -> float:
    norm_a = _normalize_column_name(name_a)
    norm_b = _normalize_column_name(name_b)
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


def _column_value_sets(dataset: Dataset) -> dict[str, set[str]]:
    """
    Loads a dataset's file once and returns, per candidate column, the
    set of distinct values as strings — so a numeric ID in one file and
    the same ID stored as text in another file can still be compared.
    """
    df = load_dataframe(dataset)
    profile = json.loads(dataset.profile_json) if dataset.profile_json else {}
    columns_meta = profile.get("columns", {})

    value_sets = {}
    for col in df.columns:
        kind = columns_meta.get(str(col), {}).get("kind")
        if kind not in CANDIDATE_KINDS:
            continue
        values = df[col].dropna().astype(str).unique()
        value_sets[str(col)] = set(values)
    return value_sets


def _value_overlap(values_a: set[str], values_b: set[str]) -> float:
    if not values_a or not values_b:
        return 0.0
    intersection = len(values_a & values_b)
    # Divide by the smaller set: if a foreign key's values are a subset
    # of a lookup table's primary key values, that's a strong match even
    # though the lookup table itself has many values the FK never uses.
    smaller = min(len(values_a), len(values_b))
    return intersection / smaller


def detect_relationships(db: Session, project_id: str) -> list[DatasetRelationship]:
    """
    Detects relationships across all ready datasets in a project,
    replacing any previously detected relationships for those datasets.
    """
    datasets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id, Dataset.status == "ready")
        .all()
    )

    dataset_ids = [d.id for d in datasets]
    # Clear previous detections for this project's datasets before
    # re-detecting, so relationships stay current as new files are added
    # and don't accumulate stale duplicates over repeated uploads.
    if dataset_ids:
        db.query(DatasetRelationship).filter(
            DatasetRelationship.left_dataset_id.in_(dataset_ids)
        ).delete(synchronize_session=False)
        db.query(DatasetRelationship).filter(
            DatasetRelationship.right_dataset_id.in_(dataset_ids)
        ).delete(synchronize_session=False)

    if len(datasets) < 2:
        db.commit()
        return []

    # Load each dataset's column value sets once, not once per pair —
    # avoids re-reading the same file multiple times.
    value_sets_by_dataset = {d.id: _column_value_sets(d) for d in datasets}

    detected: list[DatasetRelationship] = []

    for dataset_a, dataset_b in combinations(datasets, 2):
        values_a = value_sets_by_dataset[dataset_a.id]
        values_b = value_sets_by_dataset[dataset_b.id]

        for col_a, set_a in values_a.items():
            for col_b, set_b in values_b.items():
                name_sim = _name_similarity(col_a, col_b)
                overlap = _value_overlap(set_a, set_b)
                confidence = NAME_WEIGHT * name_sim + OVERLAP_WEIGHT * overlap

                if overlap >= MIN_VALUE_OVERLAP and confidence >= MIN_CONFIDENCE:
                    detected.append(
                        DatasetRelationship(
                            left_dataset_id=dataset_a.id,
                            left_column=col_a,
                            right_dataset_id=dataset_b.id,
                            right_column=col_b,
                            confidence=round(confidence, 3),
                        )
                    )

    db.add_all(detected)
    db.commit()
    for rel in detected:
        db.refresh(rel)

    return detected
