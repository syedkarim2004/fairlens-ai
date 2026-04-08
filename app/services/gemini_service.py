"""
FairLens AI — Groq AI Explanation Service
---------------------------------------------
Uses Groq's llama-3.3-70b-versatile model to generate
plain-English bias explanations from audit results. Gracefully degrades
if the API key is missing or the call fails.

SDK: groq
"""

import os
import logging
from typing import Any, Dict

from dotenv import load_dotenv

from app.services.gemma_service import get_gemma_analysis

# ---------------------------------------------------------------------------
# Load .env — must happen before we read any env vars.
# load_dotenv() is idempotent; safe to call multiple times.
# ---------------------------------------------------------------------------
load_dotenv()

# Read the key once at module load so we can log its status immediately.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Startup diagnostic — confirms key is present without exposing the value.
print(f"Groq key loaded: {len(GROQ_API_KEY) if GROQ_API_KEY else 0} chars")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_bias_explanation(audit_results: Dict[str, Any], fairness_grade: Dict[str, Any] = None, industry_context: str = "general", legal_framework: str = "General algorithmic fairness principles") -> str:
    """
    Generate a plain-English bias explanation using Groq llama-3.3-70b-versatile.

    Uses the groq SDK:
        from groq import Groq
        client = Groq(api_key=...)
        response = client.chat.completions.create(model=..., messages=..., max_tokens=...)
        return response.choices[0].message.content

    Args:
        audit_results: The dict returned by fairness_engine.run_full_audit().
        fairness_grade: Fairness grade dict
        industry_context: Detected industry
        legal_framework: Applicable legal framework

    Returns:
        A plain-English explanation string from Groq, or a fallback message
        if the API key is not set or the API call fails.
    """
    # Re-read at call-time: picks up any changes since module import
    # (e.g. if .env was fixed and server hot-reloaded).
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    print(f"[gemini_service] get_bias_explanation called — key chars: {len(api_key)}")

    if not api_key or api_key == "your_groq_api_key_here":
        print("[gemini_service] GROQ_API_KEY is empty — Fallback triggered")
        logger.warning("GROQ_API_KEY is not set. Returning fallback explanation.")
        return "Explanation unavailable."
    
    print("Using Groq (Llama 3.3)...")
    logger.info("Using Groq for fast analysis")

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        prompt = _build_prompt(audit_results, fairness_grade, industry_context, legal_framework)

        print(f"[gemini_service] Calling Groq API with model=llama-3.3-70b-versatile ...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        
        content = response.choices[0].message.content
        explanation = content.strip() if content else ""
        print(f"[gemini_service] Groq response received ({len(explanation)} chars).")
        logger.info("Groq explanation generated successfully (%d chars).", len(explanation))
        return explanation

    except ImportError as e:
        print(f"[gemini_service] ImportError — groq not installed: {e}")
        logger.error("groq package is not installed. Run: pip install groq")
        return "Explanation unavailable."

    except Exception as e:
        # Print the full exception so it appears in the uvicorn console.
        print(f"Groq error: {e}")
        logger.error("Groq API call failed: %s", e)
        return "Explanation unavailable."


# ---------------------------------------------------------------------------
# Gemma Integration (Secondary Engine)
# ---------------------------------------------------------------------------

def get_gemma4_analysis(audit_results: Dict[str, Any]) -> str:
    """
    Uses Gemma via Ollama for deeper bias analysis.
    Falls back to Groq if Ollama fails.
    """
    prompt = _build_gemma4_prompt(audit_results)
    gemma_response = get_gemma_analysis(prompt)

    if gemma_response:
        return gemma_response

    print("Gemma failed — falling back to Groq")
    return get_bias_explanation(audit_results)


def get_dual_analysis(audit_results: Dict[str, Any]) -> Dict[str, str]:
    """
    Runs BOTH Groq and Gemma and returns both explanations.
    """
    groq_result = get_bias_explanation(audit_results)
    gemma_result = get_gemma4_analysis(audit_results)

    return {
        "groq_explanation": groq_result,
        "gemma4_explanation": gemma_result,
        "primary": "groq",
        "secondary": "gemma"
    }


def get_best_available_explanation(audit_results: Dict[str, Any]) -> Dict[str, str]:
    """
    Attempts to get the best possible explanation.
    Order: Gemma -> Groq -> Rule-based
    """
    try:
        gemma = get_gemma4_analysis(audit_results)
        if gemma and "Unavailable" not in gemma and len(gemma) > 50:
            return {"engine": "gemma", "text": gemma}
    except Exception as e:
        logger.error("Gemma final attempt failed: %s", e)

    try:
        groq = get_bias_explanation(audit_results)
        if groq and "unavailable" not in groq.lower() and len(groq) > 50:
            return {"engine": "groq", "text": groq}
    except Exception as e:
        logger.error("Groq final attempt failed: %s", e)

    # Final Rule-based fallback
    biased_cols = [col for col, m in audit_results.items() if isinstance(m, dict) and m.get("is_biased")]
    if biased_cols:
        text = f"The system has detected potential bias in the following attributes: {', '.join(biased_cols)}. " \
               f"Disparate impact ratios for these groups are below the 0.8 threshold, indicating that certain groups " \
               f"are receiving positive outcomes at a significantly lower rate than others. We recommend reviewing " \
               f"the data collection process and considering resampling or reweighting techniques to mitigate this imbalance."
    else:
        text = "The fairness audit found no major bias issues. All analyzed attributes fall within acceptable ranges " \
               "for statistical parity and disparate impact (DIR ≥ 0.8). The model appears to be treating demographic " \
               "groups equitably based on the provided dataset."
               
    return {
        "engine": "rule_based",
        "text": text
    }


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _build_prompt(audit_results: Dict[str, Any], fairness_grade: Dict[str, Any] = None, industry_context: str = "general", legal_framework: str = "General algorithmic fairness principles") -> str:
    """
    Build a structured prompt from audit results for the Groq API.
    """
    # Extract per-attribute results if we received the full audit wrapper
    per_attr = audit_results
    if isinstance(audit_results, dict) and "results" in audit_results:
        per_attr = audit_results["results"]

    columns_summary = []
    for col, metrics in per_attr.items():
        if not isinstance(metrics, dict):
            continue
        if 'status' in metrics and metrics['status'] == 'error':
            continue
            
        columns_summary.append(
            f"""
Attribute: {col}
  - Baseline group: '{metrics.get('baseline_group')}' → positive rate: {metrics.get('baseline_positive_rate', 0):.2%}
  - Minority group: '{metrics.get('minority_group')}' → positive rate: {metrics.get('minority_positive_rate', 0):.2%}
  - Disparate Impact Ratio (DIR): {metrics.get('disparate_impact_ratio', 0):.4f}  (threshold: 0.8 – 1.25)
  - Statistical Parity Difference (SPD): {metrics.get('statistical_parity_difference', 0):.4f}  (ideal = 0)
  - Risk Level: {metrics.get('risk_level', 'UNKNOWN')}
  - Biased: {metrics.get('is_biased', False)}
"""
        )

    columns_text = "\n".join(columns_summary)
    
    grade_text = ""
    if fairness_grade:
        grade_text = f"""
FAIRNESS GRADE:
Overall Score: {fairness_grade.get('overall_score', 'N/A')}
Grade: {fairness_grade.get('grade', 'N/A')}
Description: {fairness_grade.get('grade_description', 'N/A')}
"""

    prompt = f"""You are a senior algorithmic fairness auditor. Provide a PRODUCTION-GRADE, STRICTLY DATA-DRIVEN analysis of the audit results below.

AUDIT CONTEXT:
Industry: {industry_context.upper()}
Legal Framework: {legal_framework}

{grade_text}

AUDIT DATA (REAL METRICS):
{columns_text}

STRICT ANALYSIS REQUIREMENTS:
1. NO GENERIC FILLER: Do not use phrases like "critical need for improvement" unless backed by specific numbers.
2. CITATION: You MUST cite the exact Disparate Impact Ratio (DIR) and Statistical Parity Difference (SPD) for every attribute.
3. IDENTIFY DISADVANTAGE: Explicitly state which minority group is being disadvantaged compared to the baseline.
4. LOGICAL REASONING: Explain exactly what the DIR means for each attribute (e.g., "The 'race' attribute shows a DIR of 0.58, indicating the minority group receives positive outcomes at 58% the rate of the baseline group").
5. TONE: Professional, objective, and data-centric.
6. LENGTH: Under 400 words.

Your data-driven report:"""

    return prompt

def _build_gemma4_prompt(audit_results: dict) -> str:
    return f"""
You are an expert AI fairness auditor.

Analyze the following bias audit results deeply and technically.

Your tasks:
1. Identify the ROOT CAUSE of bias (data imbalance, proxy variables, sampling bias, etc.)
2. Suggest SPECIFIC technical fixes:
   - resampling strategies (oversampling/undersampling)
   - feature selection or removal
   - fairness-aware ML techniques
3. Estimate LEGAL RISK LEVEL (LOW / MEDIUM / HIGH) with justification
4. Provide a STEP-BY-STEP remediation plan
5. Compare bias severity to industry standards (e.g., disparate impact thresholds)

Constraints:
- Be precise and technical
- Avoid generic explanations
- Maximum 600 words

Audit Results:
{audit_results}
"""
