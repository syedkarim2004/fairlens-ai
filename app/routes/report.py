from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.state.audit_history import audit_store, calculate_fairness_grade
from app.services.pdf_generator import generate_audit_pdf

router = APIRouter()

@router.get("/{audit_id}")
def download_report_by_id(audit_id: str):
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail=f"Audit '{audit_id}' not found")
    try:
        pdf_bytes = generate_audit_pdf(audit_store[audit_id])
        pdf_bytes.seek(0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    fname = audit_store[audit_id]["filename"].replace(".csv","").replace(" ","_")
    return StreamingResponse(
        pdf_bytes, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=fairlens_{fname}_{audit_id}.pdf"}
    )

@router.post("/generate")
async def generate_report_direct(body: dict):
    audit_result = body.get("audit_result")
    filename = body.get("filename", "dataset.csv")
    domain = body.get("domain", "general")
    if not audit_result:
        raise HTTPException(status_code=400, detail="audit_result is required")
        
    # Handle both new deterministic and old schemas
    if "attributes" in audit_result and "summary" in audit_result:
        # New deterministic
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
        status = "FAIL" if audit_result.get("summary", {}).get("overall_risk", "LOW") == "HIGH" else "PASS"
        ai_exp = audit_result.get("summary", {}).get("deep_analysis", {}).get("overview", "AI explanation unavailable.")
        total_rows = audit_result.get("metadata", {}).get("rows", 0)
        target_column = audit_result.get("metadata", {}).get("target_column", "")
        summary_text = audit_result.get("summary", {}).get("deep_analysis", {}).get("overview", "")
    else:
        # Old
        bias_results = audit_result.get("bias_results", {})
        status = audit_result.get("status", "UNKNOWN")
        ai_exp = audit_result.get("gemini_explanation", audit_result.get("ai_explanation", "AI explanation unavailable."))
        total_rows = audit_result.get("total_rows", 0)
        target_column = audit_result.get("target_column", "")
        summary_text = audit_result.get("summary", "")

    audit_record = {
        "audit_id": "direct",
        "filename": filename,
        "domain": domain,
        "fairness_grade": calculate_fairness_grade(bias_results),
        "biases_caught": sum(1 for v in bias_results.values() if isinstance(v, dict) and v.get("is_biased", False)),
        "total_attributes": len(bias_results),
        "status": status,
        "bias_results": bias_results,
        "ai_explanation": ai_exp,
        "summary": summary_text,
        "total_rows": total_rows,
        "target_column": target_column,
        "created_at": "N/A",
        "full_result": audit_result
    }
    
    try:
        pdf_bytes = generate_audit_pdf(audit_record)
        pdf_bytes.seek(0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
        
    s_fname = filename.replace(".csv","").replace(" ","_")
    return StreamingResponse(
        pdf_bytes, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=fairlens_report_{s_fname}.pdf"}
    )
