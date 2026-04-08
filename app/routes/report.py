"""
FairLens AI — Report Routes
-----------------------------
PDF report generation using reportlab.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


from app.routes.audit import audit_store
from datetime import datetime

class ReportRequest(BaseModel):
    audit_data: dict
    dataset_name: str = "Dataset"


@router.get("/v2/generate/{file_id}")
async def generate_pdf_by_id(file_id: str):
    """Generate a PDF report by retrieving cached audit data."""
    if file_id not in audit_store:
        raise HTTPException(
            status_code=404, 
            detail=f"No audit report found for file_id '{file_id}'. Please run an audit first."
        )
    
    report_data = audit_store[file_id]
    
    # Adapt report_data to what the internal generator expects
    # (The existing logic uses several top-level keys)
    request = ReportRequest(
        audit_data=report_data,
        dataset_name=report_data.get("dataset_name", "Dataset")
    )
    return await generate_pdf_report(request)


@router.post("/generate")
async def generate_pdf_report(request: ReportRequest):
    """Generate a high-end 4-page enterprise PDF bias audit report."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_CENTER

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
        
        # Consistent Colors
        google_blue = HexColor("#1A73E8")
        dark_blue = HexColor("#041E49")
        surface_gray = HexColor("#F8F9FA")
        
        audit = request.audit_data
        grade = audit.get("overall_fairness_grade", "N/A")
        risk_score = audit.get("overall_risk_score", 0)

        # ----------------------------------------------------------------------
        # PAGE 1: COVER
        # ----------------------------------------------------------------------
        story.append(Spacer(1, 40 * mm))
        
        # Logo Text
        logo_style = ParagraphStyle(
            "Logo", 
            fontSize=36, 
            fontName="Helvetica-Bold", 
            textColor=google_blue,
            alignment=TA_CENTER
        )
        story.append(Paragraph("FairLens AI", logo_style))
        story.append(Spacer(1, 10 * mm))
        
        title_style = ParagraphStyle(
            "TitleMain", 
            fontSize=18, 
            textColor=dark_blue,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        story.append(Paragraph("Enterprise Bias Audit Report", title_style))
        
        # Big Grade Box
        grade_color = google_blue
        if grade == "F": grade_color = HexColor("#D93025") # Google Red
        elif grade == "A": grade_color = HexColor("#1E8E3E") # Google Green
        
        grade_box_data = [[grade]]
        gt = Table(grade_box_data, colWidths=[40 * mm], rowHeights=[40 * mm])
        gt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), grade_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 72),
        ]))
        story.append(gt)
        story.append(Spacer(1, 10 * mm))
        
        story.append(Paragraph(f"OVERALL FAIRNESS GRADE", ParagraphStyle("GradeLabel", fontSize=12, alignment=TA_CENTER)))
        story.append(Spacer(1, 40 * mm))
        
        # Metadata
        meta_style = ParagraphStyle("Meta", fontSize=10, textColor=HexColor("#5f6368"), alignment=TA_CENTER)
        story.append(Paragraph(f"Dataset: {request.dataset_name}", meta_style))
        story.append(Paragraph(f"Audit Date: 2026-04-07", meta_style))
        story.append(Paragraph(f"System: FairLens Autonomous Engine v2.0", meta_style))
        
        story.append(PageBreak())

        # ----------------------------------------------------------------------
        # PAGE 2: EXECUTIVE SUMMARY
        # ----------------------------------------------------------------------
        h1_style = ParagraphStyle("H1", fontSize=24, fontName="Helvetica-Bold", textColor=google_blue, spaceAfter=20)
        story.append(Paragraph("Executive Summary", h1_style))
        
        summary_text = audit.get("summary", "No summary available.")
        story.append(Paragraph(summary_text, ParagraphStyle("Summary", fontSize=12, leading=16, spaceAfter=15)))
        
        narrative = (
            "This report provides a comprehensive analysis of algorithmic fairness across sensitive attributes. "
            "Our autonomous engine has evaluated Disparate Impact, Statistical Parity, and feature contribution (SHAP). "
            "The findings indicate the level of bias present in the automated decision-making processes reflected in this dataset."
        )
        story.append(Paragraph(narrative, ParagraphStyle("Body", fontSize=11, leading=14, spaceAfter=10)))
        
        # Risk levels
        risk_data = [
            ["Observation", "Verdict"],
            ["Total Sensitive Attributes Audited", str(audit.get("total_sensitive_attrs", 0))],
            ["Biased Attributes Detected", str(audit.get("biased_attrs", 0))],
            ["Risk Concentration Score", f"{risk_score}/100"],
        ]
        rt = Table(risk_data, colWidths=[100 * mm, 60 * mm])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), google_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dadce0")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), surface_gray),
        ]))
        story.append(rt)
        
        story.append(PageBreak())

        # ----------------------------------------------------------------------
        # PAGE 3: DETAILED METRICS
        # ----------------------------------------------------------------------
        story.append(Paragraph("Detailed Bias Metrics", h1_style))
        
        results = audit.get("results", {})
        for attr, metrics in results.items():
            story.append(Paragraph(f"Attribute: {attr.upper()}", ParagraphStyle("AttrH", fontSize=14, fontName="Helvetica-Bold", textColor=dark_blue, spaceBefore=10, spaceAfter=5)))
            
            attr_data = [
                ["Metric", "Value", "Status"],
                ["Disparate Impact Ratio", f"{metrics.get('disparate_impact_ratio', 0):.4f}", "FAIL" if metrics.get("is_biased") else "PASS"],
                ["Statistical Parity Diff", f"{metrics.get('statistical_parity_difference', 0):.4f}", "-"],
                ["Risk Level", metrics.get("risk_level", "N/A"), "-"],
            ]
            
            at = Table(attr_data, colWidths=[80 * mm, 40 * mm, 40 * mm])
            at.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), dark_blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.2, HexColor("#ccc")),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('TEXTCOLOR', (2, 1), (2, 1), HexColor("#D93025") if metrics.get("is_biased") else HexColor("#1E8E3E")),
            ]))
            story.append(at)
            story.append(Spacer(1, 5 * mm))
            
        story.append(PageBreak())

        # ----------------------------------------------------------------------
        # PAGE 4: RECOMMENDATIONS
        # ----------------------------------------------------------------------
        story.append(Paragraph("Remediation Roadmap", h1_style))
        
        recs = [
            ("<b>1. Data Augmentation</b>", "Increase representation of minority groups to balance the Disparate Impact Ratio."),
            ("<b>2. Pre-processing</b>", "Apply 'Reweighing' or 'Disparate Impact Remover' algorithms to the training data."),
            ("<b>3. Transparent Auditing</b>", "Continue using SHAP Attribution to monitor high-importance proxy variables."),
            ("<b>4. Policy Adjustment</b>", "Adjust outcome thresholds for groups identified as 'High Risk'."),
            ("<b>5. Human-in-the-Loop</b>", "Introduce manual review for edge cases in the detected biased segments.")
        ]
        
        for title, desc in recs:
            story.append(Paragraph(title, ParagraphStyle("RecT", fontSize=12, spaceBefore=10)))
            story.append(Paragraph(desc, ParagraphStyle("RecD", fontSize=10, leftIndent=5, spaceAfter=5)))

        story.append(Spacer(1, 60 * mm))
        story.append(Paragraph("CONFIDENTIAL | FairLens AI Audit Report", ParagraphStyle("Footer", fontSize=8, textColor=HexColor("#70757a"), alignment=TA_CENTER)))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=fairlens_{grade}_report.pdf"},
        )

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

