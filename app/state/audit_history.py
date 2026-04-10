"""
FairLens AI — Audit History State
----------------------------------
Single source of truth for all in-memory state: file_store + audit_store.
Other modules import from here to avoid dict duplication.
"""

from datetime import datetime
import uuid
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Central In-Memory Stores
# ---------------------------------------------------------------------------
# file_id -> {df, filename, rows, columns, uploaded_at, auto_config, ...}
file_store: Dict[str, Any] = {}

# audit_id -> full audit record (for dashboard / PDF)
audit_store: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Grading Helpers
# ---------------------------------------------------------------------------

def calculate_fairness_grade(bias_results: dict) -> str:
    """
    Compute a letter grade from a dict of per-attribute bias results.
    Works with both legacy schema (disparate_impact_ratio key)
    and new deterministic schema (dir key).
    """
    if not bias_results:
        return "N/A"

    dirs = []
    for v in bias_results.values():
        if isinstance(v, dict):
            d = v.get("disparate_impact_ratio") or v.get("dir") or 0
            if d > 0:
                dirs.append(d)

    if not dirs:
        return "N/A"

    avg = sum(dirs) / len(dirs)
    if avg >= 0.95:
        return "A"
    elif avg >= 0.90:
        return "B+"
    elif avg >= 0.85:
        return "B"
    elif avg >= 0.80:
        return "C"
    elif avg >= 0.70:
        return "D"
    else:
        return "F"


# ---------------------------------------------------------------------------
# Save / Query
# ---------------------------------------------------------------------------

def save_audit_record(
    file_id: str,
    filename: str,
    audit_result: dict,
    domain: str = "general",
) -> str:
    """
    Persist an audit result in audit_store. Returns a short audit_id.
    Handles both legacy heuristic schema and new deterministic schema.
    """
    audit_id = str(uuid.uuid4())[:8]

    # --- Detect schema: deterministic vs legacy ---
    if "attributes" in audit_result and "summary" in audit_result:
        # New deterministic schema
        attrs = audit_result.get("attributes", [])
        bias_results = {}
        for attr in attrs:
            bias_results[attr.get("name", "unknown")] = {
                "disparate_impact_ratio": attr.get("dir", 1.0),
                "statistical_parity_difference": attr.get("spd", 0.0),
                "risk_level": attr.get("risk", "LOW"),
                "is_biased": (attr.get("risk", "LOW") in ("HIGH", "MEDIUM")),
                "baseline_group": attr.get("baseline_group", ""),
                "minority_group": attr.get("minority_group", ""),
                "baseline_positive_rate": attr.get("baseline_rate", 0),
                "minority_positive_rate": attr.get("minority_rate", 0),
            }
        summary_block = audit_result.get("summary", {})
        status = "FAIL" if summary_block.get("overall_risk", "LOW") == "HIGH" else "PASS"
        grade = summary_block.get("overall_grade", calculate_fairness_grade(bias_results))
        ai_explanation = summary_block.get("deep_analysis", {}).get("overview", "")
        summary_text = summary_block.get("deep_analysis", {}).get("overview", "")
        total_rows = audit_result.get("metadata", {}).get("rows", 0)
        target_column = audit_result.get("metadata", {}).get("target_column", "")
    else:
        # Legacy heuristic schema
        bias_results = audit_result.get("bias_results", {})
        status = audit_result.get("status", "UNKNOWN")
        grade = calculate_fairness_grade(bias_results)
        ai_explanation = (
            audit_result.get("gemini_explanation")
            or audit_result.get("ai_explanation")
            or ""
        )
        summary_text = audit_result.get("summary", "")
        total_rows = audit_result.get("total_rows", 0)
        target_column = audit_result.get("target_column", "")

    biases_caught = sum(
        1
        for v in bias_results.values()
        if isinstance(v, dict) and v.get("is_biased", False)
    )

    audit_store[audit_id] = {
        "audit_id": audit_id,
        "file_id": file_id,
        "filename": filename or "unknown.csv",
        "domain": domain or "general",
        "status": status,
        "fairness_grade": grade,
        "biases_caught": biases_caught,
        "total_attributes": len(bias_results),
        "bias_results": bias_results,
        "ai_explanation": ai_explanation,
        "summary": summary_text,
        "total_rows": total_rows,
        "target_column": target_column,
        "created_at": datetime.utcnow().isoformat(),
        "full_result": audit_result,
    }
    return audit_id


def get_dashboard_stats() -> dict:
    """Return aggregate statistics for the dashboard cards."""
    total = len(audit_store)
    if total == 0:
        return {
            "total_audits": 0,
            "avg_fairness_grade": "N/A",
            "biases_caught": 0,
            "capacity_percent": 0,
        }

    grade_scores = {
        "A": 95,
        "B+": 90,
        "B": 85,
        "C": 75,
        "D": 65,
        "F": 50,
        "N/A": 0,
    }
    avg_score = (
        sum(grade_scores.get(a["fairness_grade"], 0) for a in audit_store.values())
        / total
    )
    if avg_score >= 93:
        avg_grade = "A"
    elif avg_score >= 88:
        avg_grade = "B+"
    elif avg_score >= 82:
        avg_grade = "B"
    elif avg_score >= 72:
        avg_grade = "C"
    elif avg_score >= 62:
        avg_grade = "D"
    else:
        avg_grade = "F"

    return {
        "total_audits": total,
        "avg_fairness_grade": avg_grade,
        "biases_caught": sum(a["biases_caught"] for a in audit_store.values()),
        "capacity_percent": min(int((total / 50) * 100), 100),
    }
