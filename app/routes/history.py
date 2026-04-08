"""
FairLens AI — Audit History Routes
------------------------------------
In-memory audit history per user.
Replace with Firestore / database in production.
"""

from fastapi import APIRouter, Depends
from app.routes.auth import get_current_user
import datetime

router = APIRouter()

# In-memory store: {user_id: [audit_record, ...]}
audit_history: dict = {}


def save_audit_to_history(user_id: str, audit_data: dict):
    """Call this from the audit route after a successful audit."""
    if user_id not in audit_history:
        audit_history[user_id] = []

    record = {
        "audit_id": audit_data.get("file_id", "unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "dataset_name": audit_data.get("dataset_name", "Unknown Dataset"),
        "sensitive_attrs": audit_data.get("sensitive_columns", []),
        "overall_grade": audit_data.get("overall_fairness_grade", "N/A"),
        "risk_score": audit_data.get("overall_risk_score", 0),
        "biased_attrs": audit_data.get("biased_attrs", 0),
    }
    audit_history[user_id].insert(0, record)  # newest first
    audit_history[user_id] = audit_history[user_id][:50]  # keep last 50


@router.get("/audits")
async def get_audit_history(user=Depends(get_current_user)):
    """Return the current user's audit history."""
    user_id = user["sub"]
    audits = audit_history.get(user_id, [])
    return {"audits": audits, "total": len(audits)}


@router.delete("/audits/{audit_id}")
async def delete_audit(audit_id: str, user=Depends(get_current_user)):
    """Delete a specific audit record by audit_id."""
    user_id = user["sub"]
    if user_id in audit_history:
        audit_history[user_id] = [
            a for a in audit_history[user_id] if a["audit_id"] != audit_id
        ]
    return {"deleted": True}
