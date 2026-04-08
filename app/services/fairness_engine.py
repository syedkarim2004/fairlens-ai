"""
FairLens AI — Fairness Engine
-------------------------------
Core statistical fairness metrics:
  - Disparate Impact Ratio (80% rule)
  - Statistical Parity Difference
  - Risk Level classification
  - Full audit orchestration
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual Metric Functions
# ---------------------------------------------------------------------------

def calculate_fairness_grade(audit_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate an overall fairness grade (A-F) based on audit metrics."""
    scores = []
    per_attribute = {}
    
    for col, metrics in audit_results.items():
        if metrics.get("status") == "insufficient data" or "status" in metrics and metrics["status"] == "error":
            continue
            
        col_score = 0
        
        # Scoring DI
        dir_val = metrics.get("disparate_impact_ratio", 1.0)
        if 0.95 <= dir_val <= 1.05:
            di_score = 100
        elif 0.85 <= dir_val <= 1.15:
            di_score = 80
        elif 0.80 <= dir_val <= 1.25:
            di_score = 60
        else:
            di_score = 0
            
        # Scoring SPD
        spd_val = abs(metrics.get("statistical_parity_difference", 0.0))
        if spd_val < 0.05:
            spd_score = 100
        elif spd_val < 0.10:
            spd_score = 80
        elif spd_val < 0.15:
            spd_score = 60
        else:
            spd_score = 20
            
        # Scoring Risk
        risk = metrics.get("risk_level", "LOW")
        if risk == "LOW":
            risk_score = 100
        elif risk == "MEDIUM":
            risk_score = 60
        else:
            risk_score = 0
            
        # Overall column score
        col_score = (di_score + spd_score + risk_score) / 3.0
        scores.append(col_score)
        
        # Grade mapping for column
        if col_score >= 90: grade = "A"
        elif col_score >= 80: grade = "B"
        elif col_score >= 70: grade = "C"
        elif col_score >= 60: grade = "D"
        else: grade = "F"
            
        per_attribute[col] = {"score": round(col_score), "grade": grade}

    if not scores:
        return {
            "overall_score": 0,
            "grade": "N/A",
            "grade_description": "Insufficient data to grade.",
            "per_attribute": {},
            "recommendation": "Check your dataset and sensitive attributes."
        }

    overall_score = round(sum(scores) / len(scores))
    if overall_score >= 90:
        grade = "A"
        desc = "Excellent fairness metrics. Minimal bias detected."
    elif overall_score >= 80:
        grade = "B"
        desc = "Good fairness metrics. Slight deviations detected."
    elif overall_score >= 70:
        grade = "C"
        desc = "Moderate bias detected. Action recommended."
    elif overall_score >= 60:
        grade = "D"
        desc = "Significant bias detected. Remediation needed."
    else:
        grade = "F"
        desc = "Critical bias levels detected. Immediate action required."

    # Recommendation heuristic
    failing_cols = [c for c, d in per_attribute.items() if d["grade"] in ["D", "F"]]
    monitor_cols = [c for c, d in per_attribute.items() if d["grade"] in ["B", "C"]]
    
    recommendation = []
    if failing_cols:
        recommendation.append(f"Immediate action needed for: {', '.join(failing_cols)}.")
    if monitor_cols:
        recommendation.append(f"Monitor: {', '.join(monitor_cols)}.")
    if not recommendation:
        recommendation.append("Maintain current practices.")

    return {
        "overall_score": overall_score,
        "grade": grade,
        "grade_description": desc,
        "per_attribute": per_attribute,
        "recommendation": " ".join(recommendation)
    }
def _binarize_target(df: pd.DataFrame, col: str, pos_label: Any = 1) -> pd.Series:
    """
    Standardizes a target column into 1 (positive) and 0 (negative).
    Handles:
    - String literals (approved/yes/true)
    - Boolean values
    - Continuous numeric values (medians split if not binary)
    """
    series = df[col]
    
    # 1. Check if numeric continuous (more than 2 unique values)
    if pd.api.types.is_numeric_dtype(series) and series.nunique() > 2:
        median = series.median()
        logger.info(f"Numeric target '{col}' identified. Applying median-split binarization (median: {median}).")
        return (series >= median).astype(int)
    
    # 2. Standard string/binary mapping
    pos_val = str(pos_label).lower().strip()
    
    def is_positive(x):
        if pd.isna(x): return 0
        s = str(x).lower().strip()
        if s == pos_val: return 1
        if s in ["1", "1.0", "true", "yes", "approved", "hired", "accepted", "selected", "passed"]: return 1
        return 0
        
    return series.apply(is_positive)

def calculate_disparate_impact(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    positive_label: Any = 1,
) -> Dict[str, Any]:
    """
    Calculate the Disparate Impact Ratio (DIR) and group rates.
    """
    try:
        # 0. Harden Column Matching (Case Insensitivity)
        actual_cols = {c.lower(): c for c in df.columns}
        if target_col.lower() in actual_cols:
            target_col = actual_cols[target_col.lower()]
        if sensitive_col.lower() in actual_cols:
            sensitive_col = actual_cols[sensitive_col.lower()]

        temp_df = df.copy()

        # 1. Map target_col to binary (0/1) using unified helper
        temp_df['target_binary'] = _binarize_target(temp_df, target_col, positive_label)
        target_col = 'target_binary'

        # 2. Group by the sensitive attribute
        # Drop NAs in sensitive_col for grouping
        valid_df = temp_df.dropna(subset=[sensitive_col])
        
        if valid_df.empty:
            return {
                "status": "error",
                "message": f"No valid data for sensitive attribute '{sensitive_col}' after removing nulls.",
                "disparate_impact_ratio": 1.0,
                "group_rates": {}
            }

        # Check for weights (from Reweighing mitigation)
        weights_col = 'weights' if 'weights' in valid_df.columns else None
        if weights_col:
            logger.info(f"📊 Applying weighted analysis for '{sensitive_col}' using column '{weights_col}'")
        
        if weights_col:
            # Weighted mean = sum(values * weights) / sum(weights)
            def weighted_mean(group):
                return (group[target_col] * group[weights_col]).sum() / group[weights_col].sum()
            
            group_stats = valid_df.groupby(sensitive_col).apply(weighted_mean).rename('mean')
            group_counts = valid_df.groupby(sensitive_col).size().rename('count')
            group_stats = pd.concat([group_stats, group_counts], axis=1)
        else:
            group_stats = valid_df.groupby(sensitive_col)[target_col].agg(['mean', 'count'])
        
        if len(group_stats) < 2:
            return {
                "status": "insufficient_data",
                "message": f"Only one unique group found in '{sensitive_col}': {list(group_stats.index)}",
                "disparate_impact_ratio": 1.0,
                "group_rates": {str(k): float(v) for k, v in group_stats['mean'].to_dict().items()}
            }

        # 3. Deterministic Baseline Selection (Highest Count)
        baseline_group = str(valid_df[sensitive_col].value_counts().index[0])
        
        if weights_col:
            rates = group_stats['mean']
        else:
            rates = valid_df.groupby(sensitive_col)[target_col].mean()
            
        counts = valid_df[sensitive_col].value_counts()
        
        baseline_rate = float(rates[baseline_group])
        
        # Minority group is the one with lowest rate (for DIR min/max logic)
        minority_group = str(rates.idxmin())
        minority_rate = float(rates.min())
        
        # DIR = minority / baseline
        # Fixed Rule: If baseline_rate is 0, DIR is 0 (as instructed)
        dir_ratio = (minority_rate / baseline_rate) if baseline_rate > 0 else 0.0
        
        # SPD = baseline - minority
        spd_value = baseline_rate - minority_rate
        
        # JSON Safety
        if np.isnan(dir_ratio) or np.isinf(dir_ratio):
            dir_ratio = 0.0

        return {
            "status": "success",
            "baseline_group": baseline_group,
            "minority_group": minority_group,
            "baseline_rate": round(baseline_rate, 4),
            "minority_rate": round(minority_rate, 4),
            "disparate_impact_ratio": round(float(dir_ratio), 4),
            "group_rates": {str(k): round(float(v), 4) for k, v in rates.items()},
            "sample_sizes": {str(k): int(v) for k, v in counts.items()}
        }
    except Exception as e:
        logger.error(f"Error in calculate_disparate_impact for {sensitive_col}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "disparate_impact_ratio": 1.0,
            "group_rates": {}
        }


def calculate_statistical_parity(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    positive_label: int = 1,
) -> float:
    """
    Calculate the Statistical Parity Difference (SPD) for a sensitive column.

    SPD = (positive rate for minority group) - (positive rate for baseline group)

    A value of 0 means perfect parity. Negative values indicate disadvantage
    for the minority group.

    Args:
        df: Dataset as a pandas DataFrame.
        target_col: Name of the binary outcome/target column.
        sensitive_col: Name of the sensitive/protected attribute column.
        positive_label: The label value considered "positive" (default: 1).

    Returns:
        Statistical parity difference as a float, rounded to 4 decimal places.
    """
    value_counts = df[sensitive_col].value_counts()
    baseline_group = value_counts.index[0]
    minority_group = value_counts.index[-1]

    # 0. Harden Column Matching (Case Insensitivity)
    actual_cols = {c.lower(): c for c in df.columns}
    if target_col.lower() in actual_cols:
        target_col = actual_cols[target_col.lower()]
    if sensitive_col.lower() in actual_cols:
        sensitive_col = actual_cols[sensitive_col.lower()]

    # 1. Ensure target column is binary (1/0) using standardized logic
    target_series = _binarize_target(df, target_col, positive_label)

    baseline_df_target = target_series[df[sensitive_col] == baseline_group]
    minority_df_target = target_series[df[sensitive_col] == minority_group]

    # Support for Weights (Reweighing mitigation)
    weights_col = 'weights' if 'weights' in df.columns else None

    if weights_col:
        baseline_weights = df[df[sensitive_col] == baseline_group][weights_col]
        minority_weights = df[df[sensitive_col] == minority_group][weights_col]
        
        baseline_rate = (
            (baseline_df_target * baseline_weights).sum() / baseline_weights.sum()
            if baseline_weights.sum() > 0
            else 0.0
        )
        minority_rate = (
            (minority_df_target * minority_weights).sum() / minority_weights.sum()
            if minority_weights.sum() > 0
            else 0.0
        )
    else:
        baseline_rate = (
            baseline_df_target.sum() / len(baseline_df_target)
            if len(baseline_df_target) > 0
            else 0.0
        )
        minority_rate = (
            minority_df_target.sum() / len(minority_df_target)
            if len(minority_df_target) > 0
            else 0.0
        )

    return round(minority_rate - baseline_rate, 4)


def get_risk_level(disparate_impact_ratio: float) -> str:
    """
    Classify the bias risk level based on the Disparate Impact Ratio.

    Uses the 80% (four-fifths) rule applied symmetrically in both directions:
      - Extreme bias (either direction): DIR < 0.6 or DIR > 1/0.6 ≈ 1.67  → HIGH
      - Moderate bias:                  DIR 0.6–0.8 or DIR 1.25–1.67      → MEDIUM
      - Acceptable:                     DIR 0.8–1.25                       → LOW

    Args:
        disparate_impact_ratio: The calculated DIR value.

    Returns:
        One of "HIGH", "MEDIUM", or "LOW".
    """
    if disparate_impact_ratio < 0.6 or disparate_impact_ratio > (1 / 0.6):
        return "HIGH"
    elif disparate_impact_ratio < 0.8 or disparate_impact_ratio > (1 / 0.8):
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# Advanced Analytics (AIF360, SHAP, Proxies, Intersectional, Counterfactual)
# ---------------------------------------------------------------------------

def run_intersectional_analysis(
    df: pd.DataFrame, 
    target_col: str, 
    sensitive_cols: List[str], 
    positive_label: Any = 1
) -> Dict[str, Any]:
    """Run intersectional bias detection across all combinations of sensitive attributes."""
    if len(sensitive_cols) < 2:
        return {}
        
    temp_df = df.copy()
    
    # Map target
    if temp_df[target_col].dtype == 'object' or isinstance(positive_label, str):
        pos_str = str(positive_label).lower()
        temp_df[target_col] = temp_df[target_col].astype(str).str.lower().apply(
            lambda x: 1 if x == pos_str or x == "approved" else 0
        )
        
    overall_mean = temp_df[target_col].mean()
    if overall_mean == 0:
        return {}

    # Create intersection group column
    def make_group_name(row):
        return "_".join([str(row[c]) for c in sensitive_cols])
        
    temp_df['intersectional_group'] = temp_df.apply(make_group_name, axis=1)
    
    group_stats = temp_df.groupby('intersectional_group')[target_col].agg(['mean', 'count'])
    
    # Filter small groups dynamically based on dataset size
    # For small datasets, we allow smaller groups (min 2)
    min_group_size = 2 if len(temp_df) < 50 else 5
    valid_groups = group_stats[group_stats['count'] >= min_group_size]
    
    if valid_groups.empty:
        # Emergency: just pick the largest group if everything is filtered
        valid_groups = group_stats.nlargest(1, 'count')
        if valid_groups.empty:
            return {}
        
    results = {}
    for group, row in valid_groups.iterrows():
        pos_rate = float(row['mean'])
        size = int(row['count'])
        di = pos_rate / overall_mean if overall_mean > 0 else 1.0
        
        # Risk assessment for this group against overall mean
        if di < 0.6 or di > 1.67: risk = "HIGH"
        elif di < 0.8 or di > 1.25: risk = "MEDIUM"
        else: risk = "LOW"
        
        pct_rate = round(pos_rate * 100, 1)
        pct_overall = round(overall_mean * 100, 1)
        
        results[group] = {
            "size": size,
            "positive_rate": round(pos_rate, 4),
            "disparate_impact": round(di, 4),
            "risk_level": risk,
            "interpretation": f"This group gets positive outcomes {pct_rate}% of the time vs {pct_overall}% overall."
        }
        
    # Sort by disparate_impact ascending (most disadvantaged first)
    sorted_results = dict(sorted(results.items(), key=lambda item: item[1]['disparate_impact']))
    return sorted_results


def run_counterfactual(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    row_index: int,
    positive_label: Any = 1
) -> Dict[str, Any]:
    """Run counterfactual analysis for a single row by flipping its sensitive attribute."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder
        
        if row_index >= len(df) or row_index < 0:
            return {"error": "Row index out of bounds"}
            
        temp_df = df.copy()
        encoders = {}
        
        # Encode target
        if temp_df[target_col].dtype == 'object' or isinstance(positive_label, str):
            pos_str = str(positive_label).lower()
            temp_df[target_col] = temp_df[target_col].astype(str).str.lower().apply(
                lambda x: 1 if x == pos_str or x == "approved" else 0
            )
            
        # Encode categorical features
        for col in temp_df.columns:
            if col != target_col and not pd.api.types.is_numeric_dtype(temp_df[col]):
                le = LabelEncoder()
                # Create a copy as string, fill missing
                col_data = temp_df[col].fillna("missing").astype(str)
                temp_df[col] = le.fit_transform(col_data)
                encoders[col] = le
                
        # Train simple model
        X = temp_df.drop(columns=[target_col])
        y = temp_df[target_col]
        
        clf = LogisticRegression(max_iter=1000, random_state=42)
        clf.fit(X, y)
        
        # Base row
        row_original = X.iloc[[row_index]].copy()
        orig_sens_encoded = row_original[sensitive_col].iloc[0]
        
        if sensitive_col in encoders:
            le = encoders[sensitive_col]
            classes = list(le.classes_)
            orig_sens_val = str(df.iloc[row_index][sensitive_col])
            
            # Find a different class to flip to
            flip_val = classes[1] if str(classes[0]) == orig_sens_val and len(classes) > 1 else classes[0]
            flip_encoded = int(le.transform([flip_val])[0])
        else:
            # Numeric flipping (e.g. 0 to 1, or just flip sign if it's something else - simple heuristic)
            orig_sens_val = orig_sens_encoded
            flip_encoded = 1 if orig_sens_encoded == 0 else 0
            flip_val = flip_encoded

        row_flipped = row_original.copy()
        row_flipped[sensitive_col] = flip_encoded
        
        # Predict
        prob_orig = float(clf.predict_proba(row_original)[0][1])
        prob_flip = float(clf.predict_proba(row_flipped)[0][1])
        
        pred_orig = int(clf.predict(row_original)[0])
        pred_flip = int(clf.predict(row_flipped)[0])
        
        diff = round(prob_flip - prob_orig, 4)
        outcome_changed = pred_orig != pred_flip
        
        interp = (f"This person would likely have been {'APPROVED' if pred_flip == 1 else 'REJECTED'} "
                  f"if their {sensitive_col} was '{flip_val}' instead of '{orig_sens_val}'. "
                  f"Probability changed by {diff*100:.1f}%.")
                  
        return {
            "row_index": row_index,
            "original": {
                "sensitive_value": orig_sens_val,
                "predicted_outcome": pred_orig,
                "probability": round(prob_orig, 4),
                "label": "APPROVED" if pred_orig == 1 else "REJECTED"
            },
            "counterfactual": {
                "sensitive_value": flip_val,
                "predicted_outcome": pred_flip,
                "probability": round(prob_flip, 4),
                "label": "APPROVED" if pred_flip == 1 else "REJECTED"
            },
            "outcome_changed": bool(outcome_changed),
            "probability_difference": float(diff),
            "discrimination_detected": bool(outcome_changed),
            "interpretation": interp
        }
        
    except Exception as e:
        logger.error(f"Counterfactual analysis failed: {e}")
        return {"error": str(e)}
# ---------------------------------------------------------------------------

def run_aif360_audit(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    positive_label: int = 1
) -> Dict[str, Any]:
    """
    Compute AIF360 metrics. Silent fallback to manual if aif360 is missing.
    """
    try:
        from aif360.datasets import BinaryLabelDataset
        from aif360.metrics import BinaryLabelDatasetMetric
        from sklearn.preprocessing import LabelEncoder
        
        temp_df = df.copy()
        
        le_target = LabelEncoder()
        temp_df[target_col] = le_target.fit_transform(temp_df[target_col].astype(str)) if temp_df[target_col].dtype == 'object' else temp_df[target_col]
        encoded_pos_label = positive_label
        if hasattr(le_target, 'classes_') and str(positive_label) in le_target.classes_:
            encoded_pos_label = int(np.where(le_target.classes_ == str(positive_label))[0][0])
            
        temp_df[sensitive_col] = LabelEncoder().fit_transform(temp_df[sensitive_col].astype(str))
        
        for col in temp_df.columns:
            if temp_df[col].dtype == 'object':
                temp_df[col] = LabelEncoder().fit_transform(temp_df[col].astype(str))

        groups = temp_df[sensitive_col].unique()
        privileged_groups = [{sensitive_col: groups[0]}]
        unprivileged_groups = [{sensitive_col: v} for v in groups[1:]] if len(groups) > 1 else [{sensitive_col: groups[0]}]

        bld = BinaryLabelDataset(favorable_label=encoded_pos_label,
                                 unfavorable_label=0 if encoded_pos_label == 1 else 1,
                                 df=temp_df,
                                 label_names=[target_col],
                                 protected_attribute_names=[sensitive_col])
                                 
        metric = BinaryLabelDatasetMetric(bld, 
                                          unprivileged_groups=unprivileged_groups,
                                          privileged_groups=privileged_groups)
                                          
        return {
            "mean_difference": float(metric.mean_difference()),
            "disparate_impact": float(metric.disparate_impact()),
            "consistency": float(metric.consistency()[0])
        }
    except Exception as e:
        logger.warning(f"AIF360 calculation failed: {e}. Falling back to basic metrics.")
        return {
            "mean_difference": None,
            "disparate_impact": None,
            "consistency": None,
            "error": str(e)
        }

def calculate_shap_importance(df: pd.DataFrame, target_col: str, sensitive_cols: List[str], positive_label: Any = 1) -> List[Dict[str, Any]]:
    """
    Train a lightweight Random Forest and use SHAP to attribute bias.
    Requirement: 
    - Flag sensitive_cols with is_sensitive: true
    - Handle < 50 rows gracefully (return uniform)
    - Return detailed list with contribution_pct
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
        import shap
        
        if len(df) < 50:
            # Handle small datasets gracefully with uniform importance
            cols = [c for c in df.columns if c != target_col]
            val = round(1.0 / len(cols), 4) if cols else 0
            return [{"feature": c, "shap_value": val, "is_sensitive": c in sensitive_cols, "contribution_pct": round(val * 100, 2)} for c in cols]

        temp_df = df.copy()
        
        # 1. Prepare target
        if temp_df[target_col].dtype == 'object' or isinstance(positive_label, str):
            pos_str = str(positive_label).lower()
            temp_df[target_col] = temp_df[target_col].astype(str).str.lower().apply(
                lambda x: 1 if x == pos_str or x == "approved" else 0
            )

        # 2. Encode features
        for col in temp_df.columns:
            if col != target_col:
                if temp_df[col].dtype == 'object' or not pd.api.types.is_numeric_dtype(temp_df[col]):
                    temp_df[col] = LabelEncoder().fit_transform(temp_df[col].astype(str))
                else:
                    temp_df[col] = temp_df[col].fillna(0)

        X = temp_df.drop(columns=[target_col])
        y = temp_df[target_col]
        
        # 3. Train RF
        clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        clf.fit(X, y)
        
        # 4. SHAP Explanation
        explainer = shap.TreeExplainer(clf)
        # Use a background sample if dataset is large, but here we can use X
        shap_values = explainer.shap_values(X)
        
        # Handle different SHAP output formats (binary vs multi-class array)
        if isinstance(shap_values, list):
            # Binary class 1
            vals = np.abs(shap_values[1]).mean(axis=0)
        elif len(shap_values.shape) == 3:
            vals = np.abs(shap_values[:, :, 1]).mean(axis=0)
        else:
            vals = np.abs(shap_values).mean(axis=0)

        # 5. Build results
        total_importance = np.sum(vals) if np.sum(vals) > 0 else 1.0
        results = []
        for i, col in enumerate(X.columns):
            score = float(vals[i])
            results.append({
                "feature": col,
                "shap_value": round(score, 6),
                "is_sensitive": col in sensitive_cols,
                "contribution_pct": round((score / total_importance) * 100, 2)
            })
            
        # Sort by importance
        results.sort(key=lambda x: x["shap_value"], reverse=True)
        return results[:10] # Return top 10

    except Exception as e:
        logger.error(f"SHAP attribution failed: {e}")
        return []


def detect_proxy_columns(df: pd.DataFrame, sensitive_cols: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Calculate Mutual Information to detect proxy variables for sensitive columns.
    """
    try:
        from sklearn.feature_selection import mutual_info_classif
        from sklearn.preprocessing import LabelEncoder
        
        temp_df = df.copy()
        for col in temp_df.columns:
            if temp_df[col].dtype == 'object':
                temp_df[col] = LabelEncoder().fit_transform(temp_df[col].astype(str))
                
        proxies = {}
        for sensitive_col in sensitive_cols:
            if sensitive_col not in temp_df.columns:
                continue
                
            y_sensitive = temp_df[sensitive_col]
            X_candidates = temp_df.drop(columns=sensitive_cols + [target_col] if 'target_col' in locals() else sensitive_cols, errors='ignore')
            
            if X_candidates.empty:
                continue
                
            mi_scores = mutual_info_classif(X_candidates, y_sensitive, random_state=42)
            
            for col_name, score in zip(X_candidates.columns, mi_scores):
                if score > 0.05:
                    if col_name not in proxies:
                        proxies[col_name] = {}
                    proxies[col_name][sensitive_col] = float(score)
                    
        return proxies
    except Exception as e:
        logger.error(f"Proxy detection failed: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Full Audit Orchestration
# ---------------------------------------------------------------------------

def _safe_float(val, fallback=0.0):
    """Return val as float, replacing NaN/Inf with fallback."""
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return fallback
        return f
    except (TypeError, ValueError):
        return fallback


def run_full_audit(
    df: pd.DataFrame,
    target_col: str,
    sensitive_cols: List[str],
    positive_label: Any = 1,
) -> Dict[str, Any]:
    """
    Run a comprehensive fairness audit across all sensitive columns.
    Hardened to ensure it never crashes due to a single bad column.
    """
    if df is None or df.empty:
         return {"error": "Empty dataframe provided", "status": "error", "results": {}}

    # 1. Harden Target Column selection (Case Insensitivity)
    actual_cols = {c.lower(): c for c in df.columns}
    if target_col.lower() in actual_cols:
        target_col = actual_cols[target_col.lower()]

    per_attr_results: Dict[str, Any] = {}
    biased_count = 0
    total_attrs = len(sensitive_cols)

    for col in sensitive_cols:
        try:
            # 2. Harden Sensitive Column selection
            actual_col = col
            if col.lower() in actual_cols:
                actual_col = actual_cols[col.lower()]
            else:
                logger.warning(f"Column '{col}' not in DF — skipping.")
                per_attr_results[col] = {"status": "error", "message": f"Column '{col}' not found."}
                continue

            # Core Metric Calculation
            dir_res = calculate_disparate_impact(df, target_col, actual_col, positive_label)
            
            if dir_res.get("status") == "error":
                per_attr_results[col] = {"status": "error", "message": dir_res.get("message")}
                continue

            if dir_res.get("status") == "insufficient_data":
                 per_attr_results[col] = {
                    "status": "insufficient_data",
                    "message": dir_res.get("message"),
                    "disparate_impact_ratio": 1.0,
                    "risk_level": "LOW",
                    "is_biased": False
                 }
                 continue

            dir_ratio = _safe_float(dir_res["disparate_impact_ratio"])
            baseline_rate = _safe_float(dir_res["baseline_rate"])
            minority_rate = _safe_float(dir_res["minority_rate"])

            # Use robust SPD calculation
            spd = calculate_statistical_parity(df, target_col, actual_col, positive_label)

            risk = get_risk_level(dir_ratio)
            is_biased = dir_ratio < 0.8
            if is_biased: biased_count += 1

            per_attr_results[col] = {
                "status": "success",
                "attribute": actual_col,
                "disparate_impact_ratio": round(float(dir_ratio), 4),
                "statistical_parity_difference": round(float(spd), 4),
                "risk_level": risk,
                "is_biased": bool(is_biased),
                "baseline_group": dir_res["baseline_group"],
                "minority_group": dir_res["minority_group"],
                "baseline_positive_rate": round(float(baseline_rate), 4),
                "minority_positive_rate": round(float(minority_rate), 4),
                "sample_sizes": dir_res["sample_sizes"]
            }

        except Exception as e:
            logger.error(f"Failed to audit attribute '{col}': {e}")
            per_attr_results[col] = {"status": "error", "message": f"Processing failed: {str(e)}"}

    # Calculate Overall Score (Average DIR of success attributes)
    valid_dirs = [res["disparate_impact_ratio"] for res in per_attr_results.values() if res.get("status") == "success"]
    overall_score = np.mean(valid_dirs) if valid_dirs else 1.0
    
    # Calculate Grade
    grade_data = calculate_fairness_grade(per_attr_results)
    overall_fairness_grade = grade_data.get("grade", "N/A")
    
    # Summary sentence
    summary = (
        f"Audited {total_attrs} sensitive attribute(s). "
        f"{biased_count} found biased (DIR < 0.8). "
        f"Overall grade: {overall_fairness_grade}."
    )

    return {
        "status": "success",
        "results": per_attr_results,
        "overall_score": round(float(overall_score), 4),
        "overall_fairness_grade": overall_fairness_grade, # New Alias
        "grade": overall_fairness_grade,
        "grade_details": grade_data,
        "total_attributes": total_attrs,
        "total_sensitive_attrs": total_attrs, # New Alias
        "biased_attributes": biased_count,
        "biased_attrs": biased_count, # New Alias
        "summary": summary,
        "timestamp": pd.Timestamp.now().isoformat()
    }



# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def get_deterministic_interpretation(
    col: str,
    dir_ratio: float,
    risk: str
) -> str:
    """Build a fixed, non-random explanation based on metrics."""
    if risk == "LOW":
        return f"'{col}' shows minimal bias with a Disparate Impact Ratio of {dir_ratio:.2f}, which is above the 0.8 threshold."
    elif risk == "MEDIUM":
        return f"'{col}' shows moderate bias (DIR: {dir_ratio:.2f}). Consider monitoring outcomes for this group."
    else:
        return f"'{col}' shows high bias because DIR is below 0.8 (Value: {dir_ratio:.2f}). Remediation required."

def get_gemma_deep_insights(
    attribute: str,
    dir_val: float,
    spd_val: float,
    risk_label: str
) -> Dict[str, Any]:
    """
    Generate deterministic, metrics-driven 'Deep Insights' (Gemma replacement).
    Reflects priority rules: Severe (DIR < 0.5) > High (DIR < 0.8) > Medium > Low.
    """
    # 1. Determine Insight & Severity
    if dir_val < 0.5:
        insight = "Severe bias detected. The disadvantaged group receives significantly fewer positive outcomes."
        severity = "HIGH"
        status = "SEVERE"
    elif dir_val < 0.8:
        insight = "Significant bias detected. One group is clearly disadvantaged."
        severity = "HIGH"
        status = "HIGH"
    elif risk_label == "MEDIUM":
        insight = "Moderate bias detected. Some disparity exists between groups."
        severity = "MEDIUM"
        status = "MEDIUM"
    else:
        insight = "Minimal bias detected. Outcomes are nearly equal across groups."
        severity = "LOW"
        status = "LOW"

    # 2. Determine Reason based on SPD
    if spd_val > 0.2:
        reason = f"DIR is {dir_val:.2f} and SPD is {spd_val:.2f}, indicating large disparity."
    elif spd_val < 0.05:
        reason = f"DIR is {dir_val:.2f} and SPD is {spd_val:.2f}, indicating minimal disparity."
    else:
        reason = f"DIR is {dir_val:.2f} and SPD is {spd_val:.2f}, indicating moderate performance gaps."

    return {
        "attribute": attribute,
        "insight": insight,
        "reason": reason,
        "severity": severity,
        "status": status
    }

def generate_aggregated_summary(insights: List[Dict[str, Any]]) -> str:
    """Generate final high-level summary from a list of structured insights."""
    if not insights:
        return "No attributes were analyzed. Audit inconclusive."
        
    high_count = sum(1 for i in insights if i["severity"] == "HIGH")
    
    if high_count >= 2:
        return "The system shows high bias across multiple attributes. Immediate intervention is required."
    elif high_count == 1:
        return "Significant bias detected in a primary attribute. Review of the decision logic is recommended."
    else:
        return "The system appears fair with minimal bias across the analyzed traits."
