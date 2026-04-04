"""
FairLens AI — Debiasing Service
--------------------------------
Provides methods for dataset remediation:
- SMOTE resampling
- Reweighting
- Threshold Calibration
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def apply_smote_resampling(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Use SMOTE from imblearn to balance the target class.
    We'll do a simple SMOTE on the whole dataset to fix target imbalance, 
    which often helps with disparate impact.
    """
    from imblearn.over_sampling import SMOTE
    from sklearn.preprocessing import LabelEncoder
    
    temp_df = df.copy()
    label_encoders = {}
    
    from pandas.api.types import is_numeric_dtype
    for col in temp_df.columns:
        if not is_numeric_dtype(temp_df[col]):
            le = LabelEncoder()
            temp_df[col] = le.fit_transform(temp_df[col].astype(str))
            label_encoders[col] = le
            
    X = temp_df.drop(columns=[target_col])
    y = temp_df[target_col]
    
    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X, y)
    
    resampled_df = pd.concat([X_res, y_res], axis=1)
    
    # Decode back for user readability
    for col, le in label_encoders.items():
        if col in resampled_df:
            # Only decode if we have classes for all indices
            # SMOTE can generate new interpolated points which for categorical are rounded,
            # but we just cast back to nearest int to decode.
            res_col_int = resampled_df[col].round().astype(int)
            resampled_df[col] = le.inverse_transform(res_col_int)
            
    return resampled_df

def apply_reweighting(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Calculate sample weights for each group to handle imbalance without creating synthetic points.
    We assign higher weights to underrepresented groups in the positive outcome.
    """
    temp_df = df.copy()
    
    # Calculate global target prob
    p_pos = (temp_df[target_col] == 1).mean()
    p_neg = 1.0 - p_pos
    
    weights = []
    
    for idx, row in temp_df.iterrows():
        sensitive_val = row[sensitive_col]
        target_val = row[target_col]
        
        # P(sensitive)
        p_sens = (temp_df[sensitive_col] == sensitive_val).mean()
        # P(sensitive and target)
        p_sens_target = ((temp_df[sensitive_col] == sensitive_val) & (temp_df[target_col] == target_val)).mean()
        
        # P(target) depending on outcome
        target_prob = p_pos if target_val == 1 else p_neg
        
        if p_sens_target == 0:
            weight = 1.0
        else:
            weight = (target_prob * p_sens) / p_sens_target
            
        weights.append(weight)
        
    temp_df['sample_weight'] = weights
    return temp_df

def apply_threshold_calibration(df: pd.DataFrame, target_col: str, sensitive_col: str, positive_label: int = 1) -> Dict[str, float]:
    """
    Train separate logistic regression per group to find optimal threshold.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score
    from sklearn.preprocessing import LabelEncoder
    
    temp_df = df.copy()
    label_encoders = {}
    
    from pandas.api.types import is_numeric_dtype
    for col in temp_df.columns:
        if not is_numeric_dtype(temp_df[col]):
            le = LabelEncoder()
            temp_df[col] = le.fit_transform(temp_df[col].astype(str))
            label_encoders[col] = le
            
    encoded_sensitive_col = sensitive_col
    
    groups = temp_df[encoded_sensitive_col].unique()
    thresholds = {}
    
    for group in groups:
        group_df = temp_df[temp_df[encoded_sensitive_col] == group]
        
        if len(group_df) < 5 or len(group_df[target_col].unique()) < 2:
            thresholds[str(group)] = 0.5
            continue
            
        X = group_df.drop(columns=[target_col])
        y = group_df[target_col]
        
        clf = LogisticRegression(max_iter=500, random_state=42)
        clf.fit(X, y)
        probs = clf.predict_proba(X)[:, 1]
        
        best_t, best_f1 = 0.5, 0.0
        for t in np.linspace(0.1, 0.9, 9):
            preds = (probs >= t).astype(int)
            score = f1_score(y, preds, pos_label=positive_label, zero_division=0)
            if score > best_f1:
                best_f1, best_t = score, t
                
        # decode the group label if it was encoded
        group_val = group
        if sensitive_col in label_encoders:
            group_val = label_encoders[sensitive_col].inverse_transform([int(group)])[0]
            
        thresholds[str(group_val)] = float(best_t)
        
    return thresholds

def run_debiasing_pipeline(df: pd.DataFrame, target_col: str, sensitive_col: str, method: str = "smote") -> Dict[str, Any]:
    """
    Accepts method: "smote", "reweighting", "threshold".
    """
    method = method.lower()
    original_rows = len(df)
    
    try:
        if method == "smote":
            fixed_df = apply_smote_resampling(df, target_col, sensitive_col)
        elif method == "reweighting":
            fixed_df = apply_reweighting(df, target_col, sensitive_col)
        elif method == "threshold":
            thresholds = apply_threshold_calibration(df, target_col, sensitive_col)
            return {"method": method, "original_rows": original_rows, "resampled_rows": original_rows, "thresholds": thresholds, "fixed_dataset": df.to_dict(orient="records")}
        else:
            raise ValueError(f"Unknown debiasing method: {method}")
            
        return {
            "method": method,
            "original_rows": original_rows,
            "resampled_rows": len(fixed_df),
            "fixed_dataset": fixed_df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Debiasing failed: {e}")
        return {
            "method": method,
            "error": str(e)
        }
