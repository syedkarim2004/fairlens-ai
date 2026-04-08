"""
FairLens AI — Deterministic Audit Routes
----------------------------
Orchestrate fully reproducible fairness audits and mitigations.
No randomness, no LLM variation, no sampling.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.routes.upload import file_store
import traceback
from app.services import fairness_engine, debiasing, industry_templates, autonomous_config
from app.utils.validator import validate_columns_exist, validate_audit_readiness, is_column_valid, normalize_dataset_deterministic
from app.utils.reproducibility import setup_determinism

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level Audit Store
# ---------------------------------------------------------------------------
audit_store: Dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class AuditRequest(BaseModel):
    file_id: str = Field(..., description="The unique file ID")
    target_column: Optional[str] = None
    sensitive_columns: Optional[List[str]] = None
    positive_label: Any = None

class TemplateDetectRequest(BaseModel):
    file_id: str = Field(...)

class MitigationRequest(BaseModel):
    file_id: str
    method: str
    target_column: str
    sensitive_attribute: str

class MitigationResponse(BaseModel):
    mitigation_applied: str
    before: Dict[str, float]
    after: Dict[str, float]
    improvement: str
    mitigated_file_id: str

# ---------------------------------------------------------------------------
# Primary Audit Endpoint (Zero-Click / Deterministic)
# ---------------------------------------------------------------------------

@router.post("/audit/run", summary="Run a fully deterministic autonomous audit")
async def run_autonomous_audit(request: AuditRequest) -> Dict[str, Any]:
    """
    The main production endpoint for running fairness audits.
    Guarantees 100% reproducibility. Same CSV -> Same JSON.
    """
    setup_determinism(seed=42)

    try:
        file_id = request.file_id
        if file_id not in file_store:
            raise HTTPException(status_code=404, detail=f"File ID '{file_id}' not found.")

        file_entry = file_store[file_id]
        df_raw = file_entry["df"] if isinstance(file_entry, dict) else file_entry
        
        config = autonomous_config.analyze_dataset(df_raw)
        
        target_col = request.target_column or config["target_column"]
        sensitive_cols = request.sensitive_columns or config["sensitive_attributes"]
        pos_label = request.positive_label if request.positive_label is not None else config["positive_value"]

        df = normalize_dataset_deterministic(df_raw, target_col)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Dataset is empty after deterministic preprocessing.")

        audit_output = fairness_engine.run_full_audit(df, target_col, sensitive_cols, pos_label)
        
        if audit_output.get("status") == "error":
            raise HTTPException(status_code=400, detail=audit_output.get("message", "Audit engine failure."))

        attributes_list = []
        sorted_attr_names = sorted(audit_output["results"].keys())
        
        for attr in sorted_attr_names:
            data = audit_output["results"][attr]
            if data.get("status") == "success":
                deep_insight = fairness_engine.get_gemma_deep_insights(
                    attr, data["disparate_impact_ratio"], data["statistical_parity_difference"], data["risk_level"]
                )
                
                attributes_list.append({
                    "name": attr,
                    "risk": data["risk_level"],
                    "dir": data["disparate_impact_ratio"],
                    "spd": data["statistical_parity_difference"],
                    "baseline_group": data.get("baseline_group"),
                    "minority_group": data.get("minority_group"),
                    "baseline_rate": data.get("baseline_positive_rate"),
                    "minority_rate": data.get("minority_positive_rate"),
                    "sample_sizes": data.get("sample_sizes"),
                    "deep_insight": deep_insight,
                    "interpretation": fairness_engine.get_deterministic_interpretation(
                        attr, data["disparate_impact_ratio"], data["risk_level"]
                    )
                })

        score = audit_output.get("overall_score", 0)
        overall_grade = audit_output.get("grade", "N/A")
        
        risk_level = "LOW"
        if score < 60: risk_level = "HIGH"
        elif score < 80: risk_level = "MEDIUM"

        all_deep_insights = [a["deep_insight"] for a in attributes_list]
        aggregated_summary = fairness_engine.generate_aggregated_summary(all_deep_insights)

        final_response = {
            "summary": {
                "overall_risk": risk_level,
                "overall_grade": overall_grade,
                "score": int(score),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "deep_analysis": {
                    "overview": aggregated_summary
                }
            },
            "attributes": attributes_list,
            "metrics": audit_output["results"], # Store raw metrics for mitigation lookup
            "metadata": {
                "file_id": file_id,
                "target_column": target_col,
                "positive_outcome": pos_label,
                "rows": len(df),
                "cols": len(df.columns)
            }
        }
        
        audit_store[file_id] = final_response
        return final_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit failure: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal audit failure: {str(e)}")

# ---------------------------------------------------------------------------
# Mitigation Endpoint
# ---------------------------------------------------------------------------

@router.post("/audit/mitigate", response_model=MitigationResponse)
async def apply_mitigation(request: MitigationRequest) -> MitigationResponse:
    """
    Apply real dataset transformations and re-calculate metrics for a specific sensitive attribute.
    """
    setup_determinism(seed=42)

    try:
        # 1. Verify File
        file_entry = file_store.get(request.file_id)
        if not file_entry:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        
        # 2. Get Baseline metrics
        if request.file_id not in audit_store:
             raise HTTPException(status_code=400, detail="Please run a standard audit first.")
        
        baseline = audit_store[request.file_id]
        attr_metrics = baseline["metrics"].get(request.sensitive_attribute)
        if not attr_metrics or attr_metrics.get("status") != "success":
            raise HTTPException(status_code=400, detail=f"No valid baseline for attribute {request.sensitive_attribute}")
        
        before_stats = {
            "DIR": attr_metrics["disparate_impact_ratio"],
            "SPD": attr_metrics["statistical_parity_difference"]
        }

        # 3. Apply Mitigation Transformation
        df_raw = file_entry["df"]
        mitigated_df = debiasing.run_mitigation_pipeline(
            df_raw, 
            request.method, 
            request.target_column, 
            request.sensitive_attribute
        )

        # 4. Re-calculate Audit on Mitigated Data
        # We run the full audit logic but focus on the delta for the requested attribute
        new_audit = fairness_engine.run_full_audit(
            mitigated_df, 
            request.target_column, 
            [request.sensitive_attribute],
            baseline["metadata"]["positive_outcome"]
        )

        if new_audit["status"] != "success":
            raise HTTPException(status_code=500, detail="Fairness engine failed on mitigated data.")
            
        attr_after = new_audit["results"].get(request.sensitive_attribute)
        if not attr_after or attr_after.get("status") != "success":
             raise HTTPException(status_code=500, detail="Could not calculate post-mitigation metrics.")

        after_stats = {
            "DIR": attr_after["disparate_impact_ratio"],
            "SPD": attr_after["statistical_parity_difference"]
        }

        # 5. Calculate Improvement
        # Delta toward 1.0 (DIR)
        dir_before = before_stats["DIR"]
        dir_after = after_stats["DIR"]
        
        # Professional Improvement Calculation
        improvement_val = 0.0
        if dir_before < 1.0:
            improvement_val = max(0, (dir_after - dir_before) / (1.0 - dir_before)) * 100
        elif dir_before > 1.0:
            improvement_val = max(0, (dir_before - dir_after) / (dir_before - 1.0)) * 100
            
        # Store Mitigated Artifact
        mitigated_file_id = f"mitigated_{uuid.uuid4().hex[:6]}"
        file_store[mitigated_file_id] = {
            "df": mitigated_df,
            "filename": f"mitigated_{file_entry['filename']}"
        }

        return MitigationResponse(
            mitigation_applied=request.method,
            before=before_stats,
            after=after_stats,
            improvement=f"+{improvement_val:.1f}%",
            mitigated_file_id=mitigated_file_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mitigation failure: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# Support Endpoints
# ---------------------------------------------------------------------------

@router.post("/audit", summary="Alias for /audit/run")
async def run_audit_alias(request: AuditRequest) -> Dict[str, Any]:
    return await run_autonomous_audit(request)

@router.post("/audit/full", summary="Alias for /audit/run (used by frontend)")
async def run_audit_full_alias(request: AuditRequest) -> Dict[str, Any]:
    return await run_autonomous_audit(request)

@router.get("/audit/{file_id}/report", summary="Retrieve a cached report")
async def get_audit_report(file_id: str) -> Dict[str, Any]:
    if file_id not in audit_store:
        raise HTTPException(status_code=404, detail=f"No report found for {file_id}.")
    return audit_store[file_id]

@router.post("/templates/detect", summary="Deterministic parameter detection")
async def detect_template(request: TemplateDetectRequest) -> Dict[str, Any]:
    file_entry = file_store.get(request.file_id)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found.")
    df = file_entry["df"] if isinstance(file_entry, dict) else file_entry
    return autonomous_config.analyze_dataset(df)

@router.post("/generate-test-data", summary="Deterministic synthetic data")
async def generate_test_data() -> Dict[str, Any]:
    """Deterministic version of test data generation."""
    setup_determinism(seed=42)
    rng = np.random.default_rng(seed=42)
    n = 500
    genders = rng.choice(["male", "female"], size=n)
    decision = np.array([
        ("approved" if rng.random() < (0.75 if g == "male" else 0.40) else "rejected")
        for g in genders
    ])
    df = pd.DataFrame({"gender": genders, "decision": decision})
    file_id = uuid.uuid4().hex[:8]
    file_store[file_id] = {"df": df, "filename": "deterministic_test_mig.csv"}
    return {"file_id": file_id, "message": "Deterministic test data generated."}

@router.get("/audit/download/{file_id}", summary="Download mitigated dataset")
async def download_mitigated(file_id: str):
    """
    Returns the mitigated dataframe as a downloadable CSV.
    """
    if file_id not in file_store:
        raise HTTPException(status_code=404, detail="Mitigated file not found or expired.")
    
    entry = file_store[file_id]
    df = entry["df"]
    filename = entry["filename"]
    
    # Ensure .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
        
    from fastapi.responses import StreamingResponse
    import io
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response
