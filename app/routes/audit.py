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
from app.services import fairness_engine, gemini_service, debiasing, industry_templates
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

class DebiasRequest(BaseModel):
    """Request body for POST /api/debias."""
    file_id: str = Field(..., description="The dataset file_id")
    target_column: str = Field(..., description="The target column")
    sensitive_column: str = Field(..., description="The sensitive column to debias")
    method: str = Field(default="smote", description="Debiasing method: smote, reweighting, or threshold")

class IntersectionalRequest(BaseModel):
    file_id: str = Field(...)
    target_column: str = Field(...)
    sensitive_columns: List[str] = Field(...)
    positive_label: Any = Field(default=1)

class CounterfactualRequest(BaseModel):
    file_id: str = Field(...)
    target_column: str = Field(...)
    sensitive_column: str = Field(...)
    row_index: int = Field(default=0)
    positive_label: Any = Field(default=1)

class CounterfactualBatchRequest(BaseModel):
    file_id: str = Field(...)
    target_column: str = Field(...)
    sensitive_column: str = Field(...)
    positive_label: Any = Field(default=1)
    sample_size: int = Field(default=20)

class TemplateDetectRequest(BaseModel):
    file_id: str = Field(...)



# ---------------------------------------------------------------------------
# POST /api/generate-test-data
# ---------------------------------------------------------------------------

@router.post("/generate-test-data", summary="Generate a synthetic biased hiring dataset")
async def generate_test_data() -> Dict[str, Any]:
    """
    Generate a 500-row synthetic hiring dataset with intentional bias.
    Target is 'decision' with values 'approved' or 'rejected'.
    """
    rng = np.random.default_rng(seed=42)

    n = 500
    genders = rng.choice(["male", "female"], size=n, p=[0.5, 0.5])
    income = rng.integers(30000, 150000, size=n)
    credit_score = rng.integers(300, 850, size=n)

    # Inject gender bias: men 70% approval, women 30% approval
    decision = np.array([
        ("approved" if rng.random() < (0.70 if g == "male" else 0.30) else "rejected")
        for g in genders
    ])

    df = pd.DataFrame({
        "gender": genders.tolist(),
        "income": income.tolist(),
        "credit_score": credit_score.tolist(),
        "decision": decision.tolist(),
    })

    file_id = uuid.uuid4().hex[:8]
    file_store[file_id] = df

    return {
        "file_id": file_id,
        "rows": len(df),
        "columns": list(df.columns),
        "target_column": "decision",
        "message": f"Dataset generated with file_id '{file_id}'. Target: 'decision' (approved/rejected)."
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
    # Enforce target_column to be 'decision'
    target_column = "decision"
    all_required_cols = [target_column] + request.sensitive_columns
    validate_columns_exist(df, all_required_cols)

    # --- Run the core fairness audit ---
    logger.info(
        "Starting audit — file_id=%s, target=%s, sensitive=%s",
        request.file_id,
        target_column,
        request.sensitive_columns,
    )

    bias_results = fairness_engine.run_full_audit(
        df=df,
        target_col=target_column,
        sensitive_cols=request.sensitive_columns,
        positive_label="approved",
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

# ---------------------------------------------------------------------------
# POST /api/audit/full
# ---------------------------------------------------------------------------

@router.post("/audit/full", summary="Run a full fairness audit with all available analysis modules")
async def run_full_audit_endpoint(request: AuditRequest) -> Dict[str, Any]:
    if request.file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found.")

    target_column = "decision"
    df = file_store[request.file_id]
    validate_columns_exist(df, [target_column] + request.sensitive_columns)
    
    # Auto-detect industry context
    industry_config = industry_templates.auto_configure_audit(df)
    
    # 1. Basic Audit
    basic_results = fairness_engine.run_full_audit(df, target_column, request.sensitive_columns, "approved")
    
    # Calculate fairness grade
    fairness_grade = fairness_engine.calculate_fairness_grade(basic_results)
    
    # Intersectional Analysis (if multiple sensitive columns)
    intersectional_analysis = {}
    if len(request.sensitive_columns) > 1:
        intersectional_analysis = fairness_engine.run_intersectional_analysis(df, target_column, request.sensitive_columns, "approved")

    # 2. AIF360
    aif360_metrics = {}
    for col in request.sensitive_columns:
        aif360_metrics[col] = fairness_engine.run_aif360_audit(df, target_column, col, 1) # Internal numeric mapping
        
    # 3. SHAP
    shap_analysis = fairness_engine.run_shap_analysis(df, target_column, request.sensitive_columns)
    
    # 4. Proxy Detection
    proxy_columns = fairness_engine.detect_proxy_columns(df, request.sensitive_columns)
    
    # 5. Gemini Explanation (basic summary)
    gemini_explanation = gemini_service.get_bias_explanation(
        basic_results, 
        fairness_grade=fairness_grade,
        industry_context=industry_config.get("detected_industry", "general"),
        legal_framework=industry_config.get("legal_framework", "")
    )
    
    # Derive high-level status
    biased_cols = [col for col, m in basic_results.items() if isinstance(m, dict) and m.get("is_biased")]
    status = "FAIL" if biased_cols else "PASS"

    report = {
        "file_id": request.file_id,
        "status": status,
        "total_rows": len(df),
        "target_column": request.target_column,
        "sensitive_columns": request.sensitive_columns,
        "fairness_grade": fairness_grade,
        "industry_detected": industry_config.get("detected_industry", "general"),
        "legal_framework": industry_config.get("legal_framework", ""),
        "intersectional_analysis": intersectional_analysis,
        "bias_results": basic_results,
        "aif360_metrics": aif360_metrics,
        "shap_analysis": shap_analysis,
        "proxy_columns": proxy_columns,
        "gemini_explanation": gemini_explanation,
        "summary": f"Completed deep audit for {len(request.sensitive_columns)} attributes. Overall grade: {fairness_grade.get('grade')}.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    audit_store[request.file_id] = report
    return report

# ---------------------------------------------------------------------------
# POST /api/debias
# ---------------------------------------------------------------------------

@router.post("/debias", summary="Debias dataset using SMOTE, reweighting, or threshold")
async def apply_debiasing(request: DebiasRequest) -> Dict[str, Any]:
    if request.file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found.")
        
    df = file_store[request.file_id]
    result = debiasing.run_debiasing_pipeline(df, request.target_column, request.sensitive_column, request.method)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    if "fixed_dataset" in result and request.method != "threshold":
        fixed_df = pd.DataFrame(result["fixed_dataset"])
        new_file_id = uuid.uuid4().hex[:8]
        file_store[new_file_id] = fixed_df
        result["new_file_id"] = new_file_id
        
        del result["fixed_dataset"]
    elif request.method == "threshold":
        del result["fixed_dataset"]
        
    return result

# ---------------------------------------------------------------------------
# GET /api/audit/{file_id}/shap
# ---------------------------------------------------------------------------

@router.get("/audit/{file_id}/shap", summary="Get cached SHAP values")
async def get_shap_report(file_id: str) -> Dict[str, Any]:
    if file_id not in audit_store or "shap_analysis" not in audit_store[file_id]:
         raise HTTPException(status_code=404, detail="No SHAP report found for file.")
    return {"shap_analysis": audit_store[file_id]["shap_analysis"]}


# ---------------------------------------------------------------------------
# New Feature Endpoints
# ---------------------------------------------------------------------------

@router.post("/audit/intersectional", summary="Run intersectional bias analysis")
async def run_intersectional(request: IntersectionalRequest) -> Dict[str, Any]:
    if request.file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found.")
        
    df = file_store[request.file_id]
    validate_columns_exist(df, [request.target_column] + request.sensitive_columns)
    
    if len(request.sensitive_columns) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 sensitive columns")
        
    results = fairness_engine.run_intersectional_analysis(
        df, request.target_column, request.sensitive_columns, request.positive_label
    )
    
    most_disadvantaged = None
    most_advantaged = None
    
    if results:
        # Results are sorted by disparate impact ascending
        groups = list(results.keys())
        most_disadvantaged = groups[0]
        most_advantaged = groups[-1]
        
        # Build prompt for explanation
        prompt = f"Explain the intersectional bias finding: The most disadvantaged group is {most_disadvantaged} with Disparate Impact {results[most_disadvantaged]['disparate_impact']} and positive rate {results[most_disadvantaged]['positive_rate']}. The most advantaged group is {most_advantaged} with Disparate Impact {results[most_advantaged]['disparate_impact']} and positive rate {results[most_advantaged]['positive_rate']}."
        try:
            from groq import Groq
            import os
            client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            explanation = response.choices[0].message.content
        except Exception:
            explanation = "Explanation unavailable."
    else:
        explanation = "No valid intersectional groups found."
        
    return {
        "file_id": request.file_id,
        "intersectional_results": results,
        "most_disadvantaged_group": most_disadvantaged,
        "most_advantaged_group": most_advantaged,
        "groq_explanation": explanation,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/audit/counterfactual", summary="Run counterfactual analysis for a row")
async def run_counterfactual_single(request: CounterfactualRequest) -> Dict[str, Any]:
    if request.file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found.")
        
    df = file_store[request.file_id]
    validate_columns_exist(df, [request.target_column, request.sensitive_column])
    
    return fairness_engine.run_counterfactual(
        df, request.target_column, request.sensitive_column, request.row_index, request.positive_label
    )


@router.post("/audit/counterfactual/batch", summary="Run counterfactual analysis for a sample of rows")
async def run_counterfactual_batch(request: CounterfactualBatchRequest) -> Dict[str, Any]:
    if request.file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found.")
        
    df = file_store[request.file_id]
    validate_columns_exist(df, [request.target_column, request.sensitive_column])
    
    sample_size = min(request.sample_size, len(df))
    # Select random indices
    rng = np.random.default_rng()
    indices = rng.choice(len(df), size=sample_size, replace=False).tolist()
    
    affected_rows = []
    total_diff = 0.0
    
    for idx in indices:
        res = fairness_engine.run_counterfactual(
            df, request.target_column, request.sensitive_column, idx, request.positive_label
        )
        if "error" not in res:
            if res.get("outcome_changed", False):
                affected_rows.append(idx)
            total_diff += abs(res.get("probability_difference", 0.0))
            
    discrimination_rate = len(affected_rows) / sample_size if sample_size > 0 else 0
    avg_diff = total_diff / sample_size if sample_size > 0 else 0
    
    interp = f"Out of {sample_size} random rows, changing the sensitive attribute altered the model's decision for {len(affected_rows)} people ({discrimination_rate*100:.1f}%). On average, the predicted probability changed by {avg_diff*100:.1f}%."
    
    return {
        "discrimination_rate": discrimination_rate,
        "affected_rows": affected_rows,
        "average_probability_difference": avg_diff,
        "interpretation": interp
    }


@router.get("/templates", summary="List available industry templates")
async def list_templates() -> Dict[str, Any]:
    return {
        key: {"name": t["name"], "description": t["description"]} 
        for key, t in industry_templates.TEMPLATES.items()
    }


@router.post("/templates/detect", summary="Auto-configure audit based on dataset")
async def detect_template(request: TemplateDetectRequest) -> Dict[str, Any]:
    if request.file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found.")
        
    df = file_store[request.file_id]
    return industry_templates.auto_configure_audit(df)
