import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# --- Deterministic Priority Keywords ---
STRICT_TARGET_KEYWORDS = ["target", "label", "outcome", "approved", "hired", "admitted"]
STRICT_SENSITIVE_KEYWORDS = ["gender", "sex", "race", "caste", "age", "income", "education"]

def analyze_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform a fully deterministic audit configuration from a dataset.
    Follows strict priority rules with alphabetical tie-breaking.
    """
    if df is None or df.empty:
        return {}

    # 1. Normalize Columns (Alphabetical Sorting for Tie-breaking)
    all_columns = sorted(list(df.columns))
    
    # 2. Identify Feature Types
    feature_types = {}
    for col in all_columns:
        unique_count = df[col].nunique()
        if unique_count == 2:
            feature_types[col] = "binary"
        elif pd.api.types.is_numeric_dtype(df[col]):
            feature_types[col] = "numerical"
        else:
            feature_types[col] = "categorical"

    # 3. Identify Target Column (Strict Priority)
    target_column = None
    
    # Priority 1: Keyword Match (Alphabetical Tie-break)
    target_candidates = [
        col for col in all_columns 
        if any(kw in col.lower() for kw in STRICT_TARGET_KEYWORDS)
    ]
    if target_candidates:
        target_column = sorted(target_candidates)[0]
    
    # Priority 2: Binary Columns (Alphabetical Tie-break)
    if not target_column:
        binary_candidates = [col for col in all_columns if feature_types[col] == "binary"]
        if binary_candidates:
            target_column = sorted(binary_candidates)[0]
            
    # Priority 3: First Column Alphabetically
    if not target_column:
        target_column = all_columns[0]

    # 4. Identify Sensitive Attributes (Strict Priority)
    sensitive_attributes = []
    
    # Priority 1: Keyword Match
    for col in all_columns:
        if col == target_column:
            continue
        if any(kw in col.lower() for kw in STRICT_SENSITIVE_KEYWORDS):
            sensitive_attributes.append(col)
            
    # Sort final list alphabetically for consistency
    sensitive_attributes = sorted(list(set(sensitive_attributes)))

    # 5. Determine Positive Outcome (Favorable Class)
    # Fixed Rule: 1 > "Yes" > "Approved" > "Hired" > Last alphabetically
    positive_value = 1
    target_series = df[target_column].dropna()
    
    if not target_series.empty:
        unique_vals = sorted(list(target_series.unique()), key=lambda x: str(x))
        val_strs = [str(v).lower() for v in unique_vals]
        
        if "1" in val_strs: positive_value = unique_vals[val_strs.index("1")]
        elif 1 in unique_vals: positive_value = 1
        elif "yes" in val_strs: positive_value = unique_vals[val_strs.index("yes")]
        elif "approved" in val_strs: positive_value = unique_vals[val_strs.index("approved")]
        elif "hired" in val_strs: positive_value = unique_vals[val_strs.index("hired")]
        else:
            # Fallback to last alphabetically
            positive_value = unique_vals[-1]

    # 6. Confidence Score (Deterministic)
    # 1.0 if target is keyword-matched, 0.5 otherwise
    has_target_kw = any(kw in target_column.lower() for kw in STRICT_TARGET_KEYWORDS)
    confidence_score = 1.0 if has_target_kw else 0.5

    # 7. Generate Deterministic Summary
    summary = f"Audit targets '{target_column}' outcome based on {len(sensitive_attributes)} sensitive traits: {', '.join(sensitive_attributes)}."

    return {
        "target_column": target_column,
        "positive_value": str(positive_value),
        "sensitive_attributes": sensitive_attributes,
        "feature_types": feature_types,
        "confidence_score": confidence_score,
        "deterministic_summary": summary
    }
