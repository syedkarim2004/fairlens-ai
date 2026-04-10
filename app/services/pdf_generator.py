import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
# 'point' is not a valid import from reportlab.lib.units
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

def generate_audit_pdf(audit_record: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    story = []

    # Colors
    google_blue = HexColor("#1a73e8")
    gray = HexColor("#808080")
    light_blue = HexColor("#e8f0fe")
    white_bg = HexColor("#ffffff")
    alt_bg = HexColor("#f8f9fa")
    
    green = HexColor("#1E8E3E")
    yellow = HexColor("#F9AB00")
    red = HexColor("#D93025")

    def get_color_for_grade(grade):
        if grade in ("A", "B+", "B"): return green
        if grade == "C": return yellow
        return red

    def get_color_for_risk(risk):
        risk = str(risk).upper()
        if risk == "HIGH": return red
        if risk == "MEDIUM": return yellow
        return green

    # Page 1 - Header
    story.append(Paragraph("FairLens AI", ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=24, textColor=google_blue)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Algorithmic Bias Audit Report", ParagraphStyle("SubTitle", fontName="Helvetica", fontSize=16, textColor=gray)))
    story.append(Spacer(1, 10))
    story.append(Table([[""]], colWidths=[doc.width], style=[('LINEBELOW', (0,0), (-1,-1), 1, black)]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Generated date: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}", ParagraphStyle("Date", fontName="Helvetica", fontSize=10, textColor=gray)))
    story.append(Spacer(1, 30))

    # Section 1 - Executive Summary
    story.append(Paragraph("Executive Summary", ParagraphStyle("ExecSumm", fontName="Helvetica-Bold", fontSize=14, textColor=google_blue)))
    story.append(Spacer(1, 10))

    status_color = green if audit_record.get("status") == "PASS" else red
    grade = str(audit_record.get("fairness_grade", "N/A"))
    
    exec_data = [
        ["Dataset:", str(audit_record.get("filename", "N/A"))],
        ["Domain:", str(audit_record.get("domain", "general")).title()],
        ["Total Rows Analyzed:", str(audit_record.get("total_rows", 0))],
        ["Attributes Audited:", str(audit_record.get("total_attributes", 0))],
        ["Overall Status:", Paragraph(str(audit_record.get("status", "UNKNOWN")), ParagraphStyle("St", fontName="Helvetica-Bold", textColor=status_color))],
        ["Fairness Grade:", Paragraph(grade, ParagraphStyle("Grade", fontName="Helvetica-Bold", fontSize=36, textColor=get_color_for_grade(grade)))],
        ["Audit Date:", str(audit_record.get("created_at", "N/A"))[:10] if audit_record.get("created_at") != "N/A" else "N/A"]
    ]
    
    exec_table = Table(exec_data, colWidths=[150, 300])
    exec_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 15))
    story.append(Paragraph(str(audit_record.get("summary", "")), styles["Normal"]))
    story.append(Spacer(1, 30))

    # Section 2 - Attribute Analysis
    story.append(Paragraph("Attribute Analysis", ParagraphStyle("Attr", fontName="Helvetica-Bold", fontSize=14, textColor=google_blue)))
    story.append(Spacer(1, 10))

    bias_results = audit_record.get("bias_results", {})
    if not bias_results:
        story.append(Paragraph("No attribute analysis available.", styles["Normal"]))
    else:
        for attr_name, metrics in bias_results.items():
            if not isinstance(metrics, dict): continue
            
            story.append(Paragraph(str(attr_name), ParagraphStyle("SubAttr", fontName="Helvetica-Bold", fontSize=12)))
            story.append(Spacer(1, 5))
            
            dir_val = metrics.get('disparate_impact_ratio', 1.0)
            spd_val = metrics.get('statistical_parity_difference', 0.0)
            risk = metrics.get('risk_level', 'LOW')
            is_biased = metrics.get('is_biased', False)

            dir_color = green if dir_val >= 0.8 else (yellow if dir_val >= 0.6 else red)
            spd_color = green if abs(spd_val) <= 0.1 else (yellow if abs(spd_val) <= 0.2 else red)
            risk_color = get_color_for_risk(risk)
            bias_color = red if is_biased else green
            
            base_rate = metrics.get('baseline_positive_rate', 0.0)
            min_rate = metrics.get('minority_positive_rate', 0.0)

            attr_data = [
                ["Metric", "Value", "Status"],
                ["Disparate Impact Ratio", f"{dir_val:.4f}", Paragraph(" ", ParagraphStyle("box", backColor=dir_color))],
                ["Statistical Parity Difference", f"{spd_val:.4f}", Paragraph(" ", ParagraphStyle("box", backColor=spd_color))],
                ["Risk Level", str(risk).upper(), Paragraph(str(risk).upper(), ParagraphStyle("rbox", textColor=risk_color, fontName="Helvetica-Bold"))],
                ["Baseline Group", str(metrics.get("baseline_group", "N/A")), ""],
                ["Minority Group", str(metrics.get("minority_group", "N/A")), ""],
                ["Baseline Positive Rate", f"{base_rate:.1%}", ""],
                ["Minority Positive Rate", f"{min_rate:.1%}", ""],
                ["Bias Detected", "Yes" if is_biased else "No", Paragraph("Yes" if is_biased else "No", ParagraphStyle("bbox", textColor=bias_color, fontName="Helvetica-Bold"))],
            ]
            
            at = Table(attr_data, colWidths=[200, 150, 100])
            at.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), alt_bg),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, gray),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(at)
            story.append(Spacer(1, 15))

    # Section 3 - Group Comparison
    story.append(Paragraph("Group Comparison", ParagraphStyle("Grp", fontName="Helvetica-Bold", fontSize=14, textColor=google_blue)))
    story.append(Spacer(1, 10))

    if bias_results:
        grp_data = [["Attribute", "Baseline Group", "Baseline Rate", "Minority Group", "Minority Rate", "Gap"]]
        row_colors = []
        for i, (attr_name, metrics) in enumerate(bias_results.items()):
            if not isinstance(metrics, dict): continue
            
            brate = metrics.get('baseline_positive_rate', 0.0)
            mrate = metrics.get('minority_positive_rate', 0.0)
            gap = mrate - brate
            gap_str = f"+{gap:.1%}" if gap > 0 else f"{gap:.1%}"
            
            grp_data.append([
                str(attr_name),
                str(metrics.get("baseline_group", "N/A")),
                f"{brate:.1%}",
                str(metrics.get("minority_group", "N/A")),
                f"{mrate:.1%}",
                gap_str
            ])
            row_colors.append(white_bg if i % 2 == 0 else alt_bg)
            
        grp_table = Table(grp_data, colWidths=[80, 80, 70, 80, 70, 70])
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), google_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, gray),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
        ]
        for idx, col in enumerate(row_colors, start=1):
            t_style.append(('BACKGROUND', (0, idx), (-1, idx), col))
            
        grp_table.setStyle(TableStyle(t_style))
        story.append(grp_table)
    else:
        story.append(Paragraph("No data available for group comparison.", styles["Normal"]))

    story.append(Spacer(1, 30))

    # Section 4 - AI-Generated Insights
    story.append(Paragraph("AI-Generated Insights", ParagraphStyle("AIH", fontName="Helvetica-Bold", fontSize=14, textColor=google_blue)))
    story.append(Paragraph("Powered by Groq AI", ParagraphStyle("AIP", fontName="Helvetica", fontSize=8, textColor=gray)))
    story.append(Spacer(1, 10))
    
    ai_text = str(audit_record.get("ai_explanation", "No AI insight provided."))
    story.append(Table([[Paragraph(ai_text, styles["Normal"])]], colWidths=[doc.width], style=[
        ('BACKGROUND', (0,0), (-1,-1), light_blue),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(Spacer(1, 30))

    # Section 5 - Regulatory Context
    story.append(Paragraph("Regulatory Context", ParagraphStyle("Reg", fontName="Helvetica-Bold", fontSize=14, textColor=google_blue)))
    story.append(Spacer(1, 10))
    
    domain = str(audit_record.get("domain", "general")).lower()
    reg_texts = {
        "hiring": "Under EEOC guidelines and the 80% (four-fifths) rule, a selection rate for a protected group less than 80% of the rate for the group with the highest selection rate is considered evidence of adverse impact. Threshold: DIR ≥ 0.80",
        "credit": "Under the Equal Credit Opportunity Act (ECOA) and Fair Housing Act, lenders must ensure credit decisions do not disparately impact protected classes. Threshold: DIR ≥ 0.80, SPD ≤ 0.10",
        "insurance": "Insurance regulators require that underwriting and rating criteria not serve as proxies for protected characteristics. Stricter threshold applies. Threshold: DIR ≥ 0.85",
        "education": "Title VI of the Civil Rights Act prohibits discrimination in educational programs. Threshold: DIR ≥ 0.75",
        "healthcare": "Section 1557 of the ACA prohibits discrimination in healthcare. Very strict threshold applies. Threshold: DIR ≥ 0.90",
        "general": "General algorithmic fairness best practices recommend the 80% rule as a baseline. Threshold: DIR ≥ 0.80",
    }
    story.append(Paragraph(reg_texts.get(domain, reg_texts["general"]), styles["Normal"]))
    story.append(Spacer(1, 30))

    # Section 6 - Recommendations
    story.append(Paragraph("Recommendations", ParagraphStyle("Rec", fontName="Helvetica-Bold", fontSize=14, textColor=google_blue)))
    story.append(Spacer(1, 10))
    
    has_bias = False
    for attr_name, metrics in bias_results.items():
        if not isinstance(metrics, dict): continue
        dir_val = metrics.get('disparate_impact_ratio', 1.0)
        risk = str(metrics.get("risk_level", "LOW")).upper()
        
        if risk == "HIGH":
            has_bias = True
            story.append(Paragraph(f"🔴 Immediately review and audit {attr_name} selection criteria. Consider removing or transforming this feature as it shows severe disparate impact (DIR: {dir_val:.2f}).", styles["Normal"]))
            story.append(Spacer(1, 5))
        elif risk == "MEDIUM":
            has_bias = True
            story.append(Paragraph(f"🟡 Monitor {attr_name} distributions quarterly and implement fairness constraints. Current DIR of {dir_val:.2f} approaches but does not meet the fairness threshold.", styles["Normal"]))
            story.append(Spacer(1, 5))
        else:
            story.append(Paragraph(f"🟢 {attr_name} is within acceptable fairness bounds (DIR: {dir_val:.2f}). Continue monitoring.", styles["Normal"]))
            story.append(Spacer(1, 5))
            
    if not has_bias and bias_results:
        story.append(Spacer(1, 5))
        story.append(Paragraph("✅ Overall: This dataset passes fairness thresholds. Recommend periodic re-auditing as data distributions change.", styles["Normal"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(gray)
        canvas.drawString(72, 36, "Generated by FairLens AI | Google Solution Challenge 2026 | Confidential")
        canvas.drawRightString(doc.pagesize[0] - 72, 36, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer
