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
        print("[gemini_service] GROQ_API_KEY is empty or placeholder — skipping Groq call.")
        logger.warning("GROQ_API_KEY is not set. Returning fallback explanation.")
        return "Explanation unavailable."

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
# Internal Helpers
# ---------------------------------------------------------------------------

def _build_prompt(audit_results: Dict[str, Any], fairness_grade: Dict[str, Any] = None, industry_context: str = "general", legal_framework: str = "General algorithmic fairness principles") -> str:
    """
    Build a structured prompt from audit results for the Groq API.
    """
    columns_summary = []
    for col, metrics in audit_results.items():
        if isinstance(metrics, dict) and 'status' in metrics and metrics['status'] == 'error':
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

    prompt = f"""You are a fairness and responsible AI expert. Analyze the following algorithmic bias audit results and provide a clear, actionable, plain-English explanation suitable for a non-technical business audience.

INDUSTRY CONTEXT: {industry_context.upper()}
LEGAL FRAMEWORK: {legal_framework}
{grade_text}
AUDIT RESULTS:
{columns_text}

Your response should:
1. Briefly explain what Disparate Impact Ratio and Statistical Parity Difference mean in plain English (1–2 sentences each).
2. For each attribute, describe whether bias was detected, how severe it is, and what it means in practice context of the {industry_context} industry.
3. Provide 2–3 concrete, actionable recommendations to reduce the detected bias, ensuring they adhere to the {legal_framework}.
4. Refer to the Overall Fairness Grade in your summary.
5. Use a professional but approachable tone — avoid jargon where possible.
6. Keep the total response under 400 words.

Provide the explanation below:"""

    return prompt
