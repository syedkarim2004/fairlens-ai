"""
FairLens AI — Audit Routes
----------------------------
Orchestrates fairness audits on uploaded datasets.
Computes disparate impact, statistical parity, and calls Gemini for explanation.

Endpoints:
  POST /api/audit                     — run a full bias audit
  POST /api/generate-test-data        — generate a synthetic biased hiring dataset
  GET  /api/audit/{file_id}/report    — retrieve a previously run audit report
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.routes.upload import file_store
from app.services import fairness_engine, gemini_service
from app.utils.validator import validate_columns_exist

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level Audit Store
# Maps file_id (str) → last audit report dict for that file.
# Populated after every successful POST /api/audit.
# ---------------------------------------------------------------------------
audit_store: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class AuditRequest(BaseModel):
    """Request body for POST /api/audit."""

    file_id: str = Field(
        ...,
        description="The 8-character file ID returned by the /api/upload or generate-test-data endpoint.",
        json_schema_extra={"example": "a1b2c3d4"},
    )
    target_column: str = Field(
        ...,
        description="Name of the binary outcome column to evaluate (e.g. 'hired').",
        json_schema_extra={"example": "hired"},
    )
    sensitive_columns: List[str] = Field(
        ...,
        description="List of protected attribute columns to audit (e.g. ['gender', 'age']).",
        json_schema_extra={"example": ["gender"]},
    )
    positive_label: int = Field(
        default=1,
        description="The value in target_column that represents a positive outcome.",
        json_schema_extra={"example": 1},
    )


# ---------------------------------------------------------------------------
# POST /api/generate-test-data
# ---------------------------------------------------------------------------

@router.post("/generate-test-data", summary="Generate a synthetic biased hiring dataset")
async def generate_test_data() -> Dict[str, Any]:
    """
    Generate a 500-row synthetic hiring dataset with intentional gender bias injected.

    Dataset columns:
      - age             : int, 22–55
      - gender          : 'male' | 'female'
      - education       : 'high_school' | 'bachelor' | 'master' | 'phd'
      - experience_years: int, 0–20
      - employment_gap  : int months, 0–24
      - hired           : 0 | 1  (binary outcome — biased by gender)

    Bias injected:
      - Men   hired at ~60% rate
      - Women hired at ~35% rate

    The dataset is stored in file_store so it can be used directly in POST /api/audit.

    Returns:
        file_id, row count, column list, and a bias_note describing the injected bias.
    """
    rng = np.random.default_rng(seed=42)  # Isolated RNG — not affected by global state

    n = 500
    genders = rng.choice(["male", "female"], size=n, p=[0.5, 0.5])
    ages = rng.integers(22, 56, size=n)
    educations = rng.choice(
        ["high_school", "bachelor", "master", "phd"],
        size=n,
        p=[0.2, 0.45, 0.25, 0.10],
    )
    experience_years = rng.integers(0, 21, size=n)
    employment_gap = rng.integers(0, 25, size=n)

    # Inject gender bias: men 60%, women 35%
    hired = np.array([
        int(rng.random() < (0.60 if g == "male" else 0.35))
        for g in genders
    ])

    df = pd.DataFrame({
        "age": ages.tolist(),
        "gender": genders.tolist(),
        "education": educations.tolist(),
        "experience_years": experience_years.tolist(),
        "employment_gap": employment_gap.tolist(),
        "hired": hired.tolist(),
    })

    # Store in the shared file_store
    file_id = uuid.uuid4().hex[:8]
    file_store[file_id] = df

    male_rate = round(df[df["gender"] == "male"]["hired"].mean() * 100, 1)
    female_rate = round(df[df["gender"] == "female"]["hired"].mean() * 100, 1)

    logger.info(
        "Test data generated — file_id=%s, male_hire_rate=%.1f%%, female_hire_rate=%.1f%%",
        file_id, male_rate, female_rate,
    )

    return {
        "file_id": file_id,
        "rows": len(df),
        "columns": list(df.columns),
        "bias_note": (
            f"Synthetic hiring dataset with intentional gender bias injected. "
            f"Men are hired at ~{male_rate}% while women are hired at ~{female_rate}%. "
            f"Use target_column='hired' and sensitive_columns=['gender'] in POST /api/audit "
            f"with this file_id to detect the bias."
        ),
        "message": (
            f"Test dataset generated and stored. "
            f"Use file_id '{file_id}' to run a fairness audit."
        ),
    }


# ---------------------------------------------------------------------------
# POST /api/audit
# ---------------------------------------------------------------------------

@router.post("/audit", summary="Run a fairness audit on an uploaded dataset")
async def run_audit(request: AuditRequest) -> Dict[str, Any]:
    """
    Run a complete bias detection audit on a previously uploaded CSV dataset.

    For each sensitive column the audit computes:
    - Disparate Impact Ratio (80% rule)
    - Statistical Parity Difference
    - Risk level (HIGH / MEDIUM / LOW)
    - Bias flag and plain-English interpretation

    Additionally, a Gemini-powered explanation is generated and a concise
    summary is returned. Results are saved to audit_store for later retrieval.

    Args:
        request: AuditRequest body with file_id, target_column, sensitive_columns,
                 and optional positive_label.

    Returns:
        Comprehensive audit report including per-column metrics, Gemini explanation,
        and a human-readable summary.
    """
    # --- Retrieve DataFrame from in-memory store ---
    if request.file_id not in file_store:
        raise HTTPException(
            status_code=404,
            detail=(
                f"File with id '{request.file_id}' not found. "
                "Please upload the dataset first via POST /api/upload, "
                "or generate one via POST /api/generate-test-data."
            ),
        )

    df = file_store[request.file_id]

    # --- Validate that all referenced columns exist ---
    all_required_cols = [request.target_column] + request.sensitive_columns
    validate_columns_exist(df, all_required_cols)

    # --- Validate target column is binary ---
    unique_labels = df[request.target_column].nunique()
    if unique_labels < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Target column '{request.target_column}' must have at least 2 unique values "
                f"(found: {unique_labels}). Ensure it is a binary classification column."
            ),
        )

    # --- Run the core fairness audit ---
    logger.info(
        "Starting audit — file_id=%s, target=%s, sensitive=%s",
        request.file_id,
        request.target_column,
        request.sensitive_columns,
    )

    bias_results = fairness_engine.run_full_audit(
        df=df,
        target_col=request.target_column,
        sensitive_cols=request.sensitive_columns,
        positive_label=request.positive_label,
    )

    # --- Get Gemini AI explanation ---
    gemini_explanation = gemini_service.get_bias_explanation(bias_results)

    # --- Build human-readable summary ---
    biased_cols = [col for col, m in bias_results.items() if m["is_biased"]]
    high_risk_cols = [
        col for col, m in bias_results.items() if m["risk_level"] == "HIGH"
    ]

    if not biased_cols:
        summary = (
            f"No significant bias detected across the {len(request.sensitive_columns)} "
            f"sensitive attribute(s) audited. The dataset appears to be within the "
            f"acceptable fairness threshold (Disparate Impact Ratio ≥ 0.8)."
        )
        status = "PASS"
    else:
        summary = (
            f"Bias detected in {len(biased_cols)} out of {len(request.sensitive_columns)} "
            f"sensitive attribute(s): {biased_cols}. "
            + (
                f"High-risk attributes requiring immediate attention: {high_risk_cols}. "
                if high_risk_cols
                else ""
            )
            + "Review the bias_results and Gemini explanation for detailed recommendations."
        )
        status = "FAIL"

    logger.info(
        "Audit complete — file_id=%s, status=%s, biased_cols=%s",
        request.file_id,
        status,
        biased_cols,
    )

    report = {
        "file_id": request.file_id,
        "status": status,
        "total_rows": len(df),
        "target_column": request.target_column,
        "sensitive_columns": request.sensitive_columns,
        "positive_label": request.positive_label,
        "bias_results": bias_results,
        "gemini_explanation": gemini_explanation,
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # --- Persist to audit_store for later retrieval ---
    audit_store[request.file_id] = report

    return report


# ---------------------------------------------------------------------------
# GET /api/audit/{file_id}/report
# ---------------------------------------------------------------------------

@router.get("/audit/{file_id}/report", summary="Retrieve a previously run audit report")
async def get_audit_report(file_id: str) -> Dict[str, Any]:
    """
    Retrieve the most recent audit report for a given file_id.

    Reports are stored in audit_store after every successful POST /api/audit call.
    This endpoint allows you to fetch the results without re-running the audit.

    Args:
        file_id: The 8-character file ID used in the original audit request.

    Returns:
        Full audit report including bias_results, gemini_explanation, summary,
        and the timestamp when the audit was run.
    """
    if file_id not in audit_store:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No audit report found for file_id '{file_id}'. "
                "Please run POST /api/audit first to generate a report."
            ),
        )

    return audit_store[file_id]
