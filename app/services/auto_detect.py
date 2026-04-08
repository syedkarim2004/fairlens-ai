"""
FairLens AI — Auto-Detection Engine
-----------------------------------
Intelligently identifies target columns, positive labels, and sensitive attributes
to provide a zero-configuration auditing experience.
"""

import logging
from typing import Any, Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# --- Configuration Roots ---
SENSITIVE_ROOTS = ["gender", "sex", "race", "ethnicity", "religion", "caste", "age", "marital", "disability", "nationality"]
TARGET_ROOTS = ["hired", "approved", "decision", "outcome", "target", "label", "status", "default", "fraud", "churn", "selected", "pass"]
POSITIVE_ROOTS = ["approved", "hired", "yes", "pass", "1", "selected", "admitted", "success"]

def auto_detect_columns(df: pd.DataFrame) -> Dict[str, Any]:
    try:
        return _auto_detect_logic(df)
    except Exception as e:
        logger.error(f"Critical failure in auto-detection engine: {e}")
        # Return ultra-safe fallback
        return {
            "target_column": list(df.columns)[-1],
            "positive_value": 1,
            "sensitive_attributes": [],
            "confidence_score": 0.0,
            "error_msg": str(e)
        }

def _auto_detect_logic(df: pd.DataFrame) -> Dict[str, Any]:
    df_cols = list(df.columns)
    df_sample = df.head(10000) # Sample for efficiency
    
    detected_target = None
    detected_positive = 1
    detected_sensitive = []
    
    # --- 1. Target Column Detection ---
    target_candidates = []
    for col in df_cols:
        lower_col = col.lower()
        unique_vals = df_sample[col].dropna().unique()
        
        # Candidate score based on name
        name_score = 0
        if any(root in lower_col for root in TARGET_ROOTS):
            name_score += 2
            
        # Candidate score based on binary-ness
        if len(unique_vals) == 2:
            name_score += 3
            
        if name_score > 0:
            # Distribution balance score (0 to 1, where 1 is perfectly balanced)
            counts = df_sample[col].value_counts(normalize=True)
            if not counts.empty:
                balance = 1.0 - abs(counts.iloc[0] - 0.5) * 2
                target_candidates.append({
                    "col": col, 
                    "score": name_score + balance,
                    "unique_vals": unique_vals
                })
            
    if target_candidates:
        best_target = max(target_candidates, key=lambda x: x["score"])
        detected_target = best_target["col"]
        unique_vals = best_target["unique_vals"]
    else:
        detected_target = df_cols[-1]
        unique_vals = df_sample[detected_target].dropna().unique()
        
    # --- 2. Positive Label Detection ---
    if pd.api.types.is_numeric_dtype(df[detected_target]):
        if 1 in unique_vals:
            detected_positive = 1
        elif len(unique_vals) > 0:
            detected_positive = int(unique_vals[0])
        else:
            detected_positive = 1
    else:
        # Check for positive roots in unique values
        found_pos = None
        for val in unique_vals:
            str_val = str(val).lower()
            if any(root in str_val for root in POSITIVE_ROOTS):
                found_pos = val
                break
        
        if found_pos is not None:
            detected_positive = found_pos
        else:
            # Fallback to most frequent or just the first one
            detected_positive = unique_vals[0] if len(unique_vals) > 0 else "unknown"

    # --- 3. Sensitive Attributes Detection ---
    for col in df_cols:
        if col == detected_target:
            continue
            
        lower_col = col.lower()
        unique_vals = df_sample[col].dropna().unique()
        
        # Name heuristic
        is_sensitive_name = any(root in lower_col for root in SENSITIVE_ROOTS)
        
        # Cardinality check: typically sensitive attributes are categorical with low cardinality
        is_low_cardinality = len(unique_vals) >= 2 and len(unique_vals) <= 10
        is_categorical = not pd.api.types.is_numeric_dtype(df[col]) or is_low_cardinality
        
        if is_sensitive_name or (is_categorical and is_low_cardinality):
            detected_sensitive.append(col)
            
    # --- 4. Confidence Score ---
    score = 0.5
    if detected_target in df_cols: score += 0.2
    if len(detected_sensitive) > 0: score += 0.2
    if len(detected_sensitive) > 2: score += 0.1 # High diversity
    
    logger.info(f"[AutoDetect] Target: {detected_target}, Positive: {detected_positive}, Sensitive: {detected_sensitive}")
    
    return {
        "target_column": detected_target,
        "positive_value": detected_positive,
        "sensitive_attributes": detected_sensitive,
        "confidence_score": min(score, 1.0)
    }
