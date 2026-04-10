"""
FairLens AI — AutoLens Detector (Enhanced)
-------------------------------------------
Provides rich dataset preview, column statistics, and intelligent
suggestions for sensitive columns, target columns, and data domain.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known Pattern Lists
# ---------------------------------------------------------------------------
SENSITIVE_PATTERNS = [
    "gender", "sex", "race", "ethnicity", "age", "nationality",
    "religion", "disability", "marital_status", "marital", "pregnancy",
    "veteran", "sexual_orientation", "native", "color", "origin",
]

TARGET_PATTERNS = [
    "approved", "hired", "admitted", "outcome", "label", "target",
    "class", "decision", "income", "loan", "default", "churn",
    "fraud", "selected", "passed", "status", "result", "prediction",
]

DOMAIN_SIGNALS = {
    "hiring": [
        "hired", "applicant", "resume", "interview", "salary", "position",
        "job", "employee", "candidate", "experience", "qualification",
    ],
    "credit": [
        "loan", "credit", "debt", "interest", "mortgage", "default",
        "payment", "balance", "amount", "bank", "financial",
    ],
    "insurance": [
        "claim", "premium", "policy", "coverage", "insured", "deductible",
        "beneficiary", "underwriting",
    ],
    "education": [
        "student", "grade", "gpa", "enrolled", "admitted", "school",
        "university", "degree", "course", "exam", "score", "academic",
    ],
    "healthcare": [
        "patient", "diagnosis", "treatment", "hospital", "medical",
        "health", "clinical", "disease", "doctor", "prescription",
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_dataset_preview(df: pd.DataFrame, filename: str = "dataset") -> Dict[str, Any]:
    """
    Generate a comprehensive dataset preview including statistics and suggestions.
    """
    columns = list(df.columns)
    dtypes = {col: str(df[col].dtype) for col in columns}
    preview_rows = df.head(10).replace({np.nan: None}).to_dict(orient="records")

    statistics = compute_column_statistics(df)
    suggested_sensitive = suggest_sensitive_columns(df)
    suggested_target = suggest_target_column(df)
    suggested_domain = suggest_domain(df)

    return {
        "file_id": None,  # Caller should fill this in
        "filename": filename,
        "total_rows": len(df),
        "total_columns": len(columns),
        "columns": columns,
        "dtypes": dtypes,
        "preview_rows": preview_rows,
        "statistics": statistics,
        "suggested_sensitive_columns": suggested_sensitive,
        "suggested_target_column": suggested_target,
        "suggested_domain": suggested_domain,
    }


def compute_column_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute per-column statistics.

    - Numeric columns: mean, median, std, min, max, null_count, null_percent, unique_count
    - Categorical columns: value_counts (top 10), null_count, null_percent, unique_count
    """
    stats: Dict[str, Any] = {}

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_percent = round(null_count / len(df) * 100, 2) if len(df) > 0 else 0.0
        unique_count = int(df[col].nunique())

        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].dropna()
            stats[col] = {
                "type": "numeric",
                "mean": round(float(series.mean()), 4) if len(series) > 0 else None,
                "median": round(float(series.median()), 4) if len(series) > 0 else None,
                "std": round(float(series.std()), 4) if len(series) > 0 else None,
                "min": _safe_json_value(series.min()) if len(series) > 0 else None,
                "max": _safe_json_value(series.max()) if len(series) > 0 else None,
                "null_count": null_count,
                "null_percent": null_percent,
                "unique_count": unique_count,
            }
        else:
            vc = df[col].value_counts().head(10)
            stats[col] = {
                "type": "categorical",
                "value_counts": {str(k): int(v) for k, v in vc.items()},
                "null_count": null_count,
                "null_percent": null_percent,
                "unique_count": unique_count,
            }

    return stats


def suggest_sensitive_columns(df: pd.DataFrame) -> List[str]:
    """
    Pattern-match column names against known sensitive attribute names.
    """
    suggestions = []
    for col in df.columns:
        lower = col.lower().replace("_", "").replace("-", "").replace(" ", "")
        for pattern in SENSITIVE_PATTERNS:
            clean_pattern = pattern.replace("_", "")
            if clean_pattern in lower:
                suggestions.append(col)
                break
    return suggestions


def suggest_target_column(df: pd.DataFrame) -> Optional[str]:
    """
    Pattern-match column names against known target/outcome column names.
    Prefers binary columns.
    """
    candidates = []
    for col in df.columns:
        lower = col.lower().replace("_", "").replace("-", "").replace(" ", "")
        for pattern in TARGET_PATTERNS:
            clean_pattern = pattern.replace("_", "")
            if clean_pattern in lower:
                # Score: binary columns get bonus
                score = 1
                if df[col].nunique() <= 5:
                    score += 2
                if df[col].nunique() == 2:
                    score += 3
                candidates.append((col, score))
                break

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    # Fallback: last column
    return df.columns[-1] if len(df.columns) > 0 else None


def suggest_domain(df: pd.DataFrame) -> str:
    """
    Infer the dataset domain from column names and sample values.
    Returns one of: hiring, credit, insurance, education, healthcare, general.
    """
    # Collect all text signals from column names and a sample of string values
    signals = []
    for col in df.columns:
        signals.append(col.lower())

    # Sample a few string values from categorical columns
    for col in df.select_dtypes(include=["object"]).columns[:5]:
        sample_vals = df[col].dropna().head(20).astype(str).str.lower().tolist()
        signals.extend(sample_vals)

    all_text = " ".join(signals)

    # Score each domain
    domain_scores: Dict[str, int] = {}
    for domain, keywords in DOMAIN_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in all_text)
        domain_scores[domain] = score

    if not domain_scores:
        return "general"

    best_domain = max(domain_scores, key=domain_scores.get)
    if domain_scores[best_domain] >= 2:
        return best_domain

    return "general"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_json_value(val):
    """Convert numpy types to JSON-safe Python types."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, 4)
    return val
