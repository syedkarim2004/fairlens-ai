import io
import datetime
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    )
except ImportError:
    # This will be caught at runtime if reportlab is missing
    pass

from app.routes.auth import get_current_user
from app.routes.audit import audit_store  # Fallback store

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Firestore Helper
# ---------------------------------------------------------------------------
def fetch_audit_from_firestore(audit_id: str):
    """
    Attempt to fetch audit from Firestore. Fallback to in-memory store.
    """
    try:
        import firebase_admin
        from firebase_admin import firestore
        
        if firebase_admin._apps:
            db = firestore.client()
            doc_ref = db.collection("audits").document(audit_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
    except Exception as e:
        logger.warning(f"Firestore fetch failed for {audit_id}: {e}. Falling back to in-memory store.")
    
    # Fallback to in-memory audit_store
    return audit_store.get(audit_id)


@router.post("/generate/{audit_id}")
async def generate_advanced_report(audit_id: str, user=Depends(get_current_user)):
    """
    Generate an advanced 5-page PDF report for a given audit_id.
    """
    audit_data = fetch_audit_from_firestore(audit_id)
    if not audit_data:
        raise HTTPException(status_code=404, detail="Audit report not found.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Custom Styles
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=26, textColor=colors.HexColor("#0f172a"), spaceAfter=12
    )
    h2_style = ParagraphStyle(
        "SectionHead", parent=styles["Heading2"], fontSize=18, textColor=colors.HexColor("#1e293b"), spaceBefore=10, spaceAfter=10
    )
    body_style = styles["Normal"]
    body_style.fontSize = 11
    body_style.leading = 14

    # --- PAGE 1: COVER ---
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("FairLens AI", title_style))
    story.append(Paragraph("Bias Audit & Fairness Certification", 
                ParagraphStyle("Sub", parent=styles["Normal"], fontSize=14, textColor=colors.HexColor("#64748b"), alignment=1, spaceAfter=30)))
    
    story.append(Spacer(1, 10 * mm))
    
    dataset_name = audit_data.get("filename") or audit_data.get("dataset_name") or "Unnamed Dataset"
    audit_date = audit_data.get("timestamp") or datetime.datetime.now().isoformat()
    if "T" in audit_date: audit_date = audit_date.split("T")[0]

    story.append(Paragraph(f"<b>Dataset:</b> {dataset_name}", body_style))
    story.append(Paragraph(f"<b>Audit Date:</b> {audit_date}", body_style))
    
    story.append(Spacer(1, 20 * mm))
    
    # Big Grade Circle
    grade = audit_data.get("overall_fairness_grade") or audit_data.get("fairness_grade", {}).get("grade", "N/A")
    grade_colors = {"A": "#10b981", "B": "#84cc16", "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"}
    grade_color = grade_colors.get(grade, "#475569")
    
    story.append(Paragraph("Overall Fairness Grade", ParagraphStyle("GradeLabel", parent=styles["Normal"], fontSize=12, textColor=colors.HexColor("#64748b"), alignment=1)))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(f"<font size='80' color='{grade_color}'><b>{grade}</b></font>", ParagraphStyle("Grade", alignment=1)))
    
    story.append(PageBreak())

    # --- PAGE 2: EXECUTIVE SUMMARY ---
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Spacer(1, 5 * mm))
    
    # Para 1: Structured Overview
    story.append(Paragraph(
        "This report provides a comprehensive analysis of algorithmic fairness and disparate impact for the audited dataset. "
        "FairLens AI utilizes industry-standard metrics (Disparate Impact Ratio, Statistical Parity Difference) alongside "
        "advanced SHAP-based feature attribution to identify hidden bias patterns and proxy variables that may lead to discriminatory outcomes.",
        body_style
    ))
    story.append(Spacer(1, 6 * mm))
    
    # Para 2: Summary of Findings
    biased_count = len([k for k, v in audit_data.get("bias_results", {}).items() if v.get("is_biased")])
    total_count = len(audit_data.get("sensitive_columns", []))
    findings = (
        f"Upon auditing {total_count} sensitive attributes, significant bias was detected in {biased_count} column(s). "
        f"The overall risk score was calculated at {audit_data.get('overall_risk_score', 0)}/100, indicating a "
        f"{'high' if grade in ['D', 'F'] else 'moderate' if grade == 'C' else 'low'} probability of regulatory non-compliance."
    )
    story.append(Paragraph(findings, body_style))
    story.append(Spacer(1, 6 * mm))
    
    # Para 3: Implications
    story.append(Paragraph(
        "Bias in automated decision-making systems can lead to systemic inequality and significant legal or reputational risk. "
        "We recommend implementing the remediation steps outlined on page 4, specifically focusing on data re-weighting or "
        "threshold adjustment for the identified high-risk demographics.",
        body_style
    ))
    story.append(PageBreak())

    # --- PAGE 3: METRICS TABLE ---
    story.append(Paragraph("Detailed Fairness Metrics", h2_style))
    story.append(Spacer(1, 5 * mm))
    
    table_data = [["Attribute", "Disparate Impact", "Stat. Parity", "Eq. Opp.", "Risk"]]
    results = audit_data.get("bias_results", {})
    for attr, metrics in results.items():
        table_data.append([
            attr.upper(),
            f"{metrics.get('disparate_impact_ratio', 1.0):.3f}",
            f"{metrics.get('statistical_parity_difference', 0.0):.3f}",
            f"{metrics.get('equal_opportunity_difference', 0.0):.3f}",
            metrics.get("risk_level", "LOW")
        ])
    
    t = Table(table_data, colWidths=[40 * mm, 35 * mm, 35 * mm, 35 * mm, 25 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(PageBreak())

    # --- PAGE 4: RECOMMENDATIONS ---
    story.append(Paragraph("Remediation Recommendations", h2_style))
    story.append(Spacer(1, 5 * mm))
    
    recs = [
        "<b>1. Strategic Data Re-sampling:</b> Oversample groups that are currently disadvantaged to balance the training distribution.",
        "<b>2. Reweighing:</b> Apply sample weights to the minority group in the loss function to penalize discriminatory errors.",
        "<b>3. Multi-threshold Classification:</b> Implement demographic-specific thresholds to normalize the True Positive Rate across groups.",
        "<b>4. Fairness Regularization:</b> Add a fairness constraint to your model's objective function during the next training cycle.",
        "<b>5. Proxy Filtering:</b> Audit features with high Mutual Information to sensitive columns and consider removing them."
    ]
    
    for rec in recs:
        story.append(Paragraph(rec, ParagraphStyle("Rec", parent=body_style, spaceAfter=8)))
        story.append(Spacer(1, 4 * mm))
        
    story.append(PageBreak())

    # --- PAGE 5: AI INSIGHTS ---
    story.append(Paragraph("Autonomous AI Insights", h2_style))
    story.append(Spacer(1, 5 * mm))
    
    ai_text = audit_data.get("groq_explanation") or audit_data.get("gemini_explanation") or "No AI analysis available for this audit."
    # Truncate to first 500 words
    truncated_text = " ".join(ai_text.split()[:500]) + ("..." if len(ai_text.split()) > 500 else "")
    
    story.append(Paragraph(truncated_text, ParagraphStyle("AI", parent=body_style, leading=16)))
    
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("FairLens AI | Responsible AI Framework v1.0", 
                ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=1)))

    doc.build(story)
    buffer.seek(0)

    filename = f"fairlens_report_{audit_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
