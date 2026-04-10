from fastapi import APIRouter, HTTPException
from app.state.audit_history import audit_store, get_dashboard_stats

router = APIRouter()

@router.get("/dashboard/stats")
def get_stats():
    return get_dashboard_stats()

@router.get("/dashboard/audits")
def get_recent_audits(limit: int = 10):
    audits = sorted(audit_store.values(), key=lambda x: x["created_at"], reverse=True)[:limit]
    return {
        "audits": [{
            "audit_id": a["audit_id"],
            "filename": a["filename"],
            "domain": a["domain"],
            "fairness_grade": a["fairness_grade"],
            "biases_caught": a["biases_caught"],
            "total_attributes": a["total_attributes"],
            "status": a["status"],
            "created_at": a["created_at"],
            "owner": "Me"
        } for a in audits],
        "total": len(audit_store)
    }

@router.get("/dashboard/audits/{audit_id}")
def get_audit_detail(audit_id: str):
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit_store[audit_id]
