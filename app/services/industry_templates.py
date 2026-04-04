"""
FairLens AI — Industry Templates
---------------------------------
Provides predefined templates for different industries to auto-configure audits.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

TEMPLATES = {
    "hiring": {
        "name": "Hiring & Recruitment",
        "description": "For analyzing job application and hiring datasets",
        "typical_target": "hired",
        "typical_target_aliases": ["hired", "selected", "approved", "offer", "decision"],
        "sensitive_columns": ["gender", "age", "race", "ethnicity", "nationality"],
        "sensitive_aliases": {
            "gender": ["gender", "sex", "g"],
            "age": ["age", "dob", "birth_year"],
            "race": ["race", "ethnicity", "nationality", "origin"]
        },
        "key_metrics": ["disparate_impact", "statistical_parity"],
        "legal_framework": "EEOC 80% Rule (US), Equality Act (UK)",
        "risk_note": "Hiring bias is legally actionable under EEOC guidelines"
    },
    "lending": {
        "name": "Loan & Credit Decisions",
        "description": "For analyzing loan approval and credit scoring datasets",
        "typical_target": "approved",
        "typical_target_aliases": ["approved", "loan_granted", "credit_approved", "decision"],
        "sensitive_columns": ["race", "gender", "age", "zip_code", "nationality"],
        "sensitive_aliases": {
            "race": ["race", "ethnicity"],
            "gender": ["gender", "sex"],
            "age": ["age"],
            "zip_code": ["zip", "zipcode", "postal_code", "area_code"]
        },
        "key_metrics": ["disparate_impact", "equalized_odds"],
        "legal_framework": "Equal Credit Opportunity Act (ECOA), Fair Housing Act",
        "risk_note": "Lending bias violates ECOA and can result in major penalties"
    },
    "healthcare": {
        "name": "Healthcare & Medical",
        "description": "For analyzing treatment recommendations and medical decisions",
        "typical_target": "treatment_approved",
        "typical_target_aliases": ["treatment", "diagnosis", "approved", "recommended", "decision"],
        "sensitive_columns": ["race", "gender", "age", "insurance_type", "income"],
        "sensitive_aliases": {
            "race": ["race", "ethnicity"],
            "gender": ["gender", "sex"],
            "age": ["age"],
            "insurance": ["insurance", "insurance_type", "coverage"]
        },
        "key_metrics": ["equalized_odds", "calibration"],
        "legal_framework": "ACA Section 1557, Civil Rights Act Title VI",
        "risk_note": "Healthcare bias can result in differential treatment and patient harm"
    },
    "criminal_justice": {
        "name": "Criminal Justice",
        "description": "For analyzing bail, sentencing, and risk assessment datasets",
        "typical_target": "high_risk",
        "typical_target_aliases": ["risk", "recidivism", "bail_denied", "high_risk", "decision"],
        "sensitive_columns": ["race", "age", "gender", "zip_code"],
        "sensitive_aliases": {
            "race": ["race", "ethnicity"],
            "gender": ["gender", "sex"],
            "age": ["age"]
        },
        "key_metrics": ["false_positive_rate_parity", "disparate_impact"],
        "legal_framework": "Equal Protection Clause, Civil Rights Act",
        "risk_note": "Risk assessment bias can lead to unjust incarceration"
    },
    "education": {
        "name": "Education & Admissions",
        "description": "For analyzing college admissions and scholarship datasets",
        "typical_target": "admitted",
        "typical_target_aliases": ["admitted", "accepted", "approved", "selected", "decision"],
        "sensitive_columns": ["race", "gender", "age", "income", "zip_code"],
        "sensitive_aliases": {
            "race": ["race", "ethnicity"],
            "gender": ["gender", "sex"],
            "income": ["income", "family_income", "household_income"]
        },
        "key_metrics": ["disparate_impact", "demographic_parity"],
        "legal_framework": "Title IX, Civil Rights Act Title VI",
        "risk_note": "Admissions bias perpetuates generational inequality"
    }
}

GENERAL_TEMPLATE = {
    "name": "General Dataset",
    "description": "General audit configuration",
    "typical_target": "target",
    "typical_target_aliases": ["decision", "target", "outcome", "label"],
    "sensitive_columns": ["gender", "race", "age"],
    "sensitive_aliases": {
        "gender": ["gender", "sex"],
        "age": ["age"],
        "race": ["race", "ethnicity"]
    },
    "key_metrics": ["disparate_impact", "statistical_parity"],
    "legal_framework": "General algorithmic fairness principles",
    "risk_note": "Ensure compliance with applicable local regulations."
}


def detect_industry(df: pd.DataFrame) -> str:
    """Detect the most likely industry based on column names."""
    df_cols = set([c.lower() for c in df.columns])
    
    best_match = "general"
    max_score = 0
    
    for industry_key, template in TEMPLATES.items():
        score = 0
        # Check target aliases
        target_aliases = set(template.get("typical_target_aliases", []))
        if df_cols.intersection(target_aliases):
            score += 2
            
        # Check sensitive aliases
        for sens_key, sens_aliases in template.get("sensitive_aliases", {}).items():
            if df_cols.intersection(set(sens_aliases)):
                score += 1
                
        if score > max_score:
            max_score = score
            best_match = industry_key
            
    # If score is very low, it might just be a generic decision dataset
    if max_score > 0:
        return best_match
    return "general"


def get_template(industry: str) -> Dict[str, Any]:
    """Return the template for the given industry."""
    return TEMPLATES.get(industry, GENERAL_TEMPLATE)


def auto_configure_audit(df: pd.DataFrame, industry: Optional[str] = None) -> Dict[str, Any]:
    """Auto-configure audit settings based on industry and dataset columns."""
    if not industry or industry == "auto":
        industry = detect_industry(df)
        
    template = get_template(industry)
    df_cols = [c.lower() for c in df.columns]
    
    # Suggest target column
    suggested_target = None
    for alias in template.get("typical_target_aliases", []):
        if alias in df_cols:
            # Find the original case name
            for orig_col in df.columns:
                if orig_col.lower() == alias:
                    suggested_target = orig_col
                    break
        if suggested_target:
            break
            
    # Suggest sensitive columns
    suggested_sensitive = []
    for sens_key, aliases in template.get("sensitive_aliases", {}).items():
        for alias in aliases:
            if alias in df_cols:
                # Find original
                for orig_col in df.columns:
                    if orig_col.lower() == alias and orig_col not in suggested_sensitive:
                        suggested_sensitive.append(orig_col)
                    
    return {
        "detected_industry": industry,
        "template": template,
        "suggested_target_column": suggested_target,
        "suggested_sensitive_columns": suggested_sensitive,
        "legal_framework": template.get("legal_framework", GENERAL_TEMPLATE["legal_framework"]),
        "risk_note": template.get("risk_note", GENERAL_TEMPLATE["risk_note"])
    }
