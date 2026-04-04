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
# ---------------------------------------------------------------------------

def calculate_disparate_impact(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    positive_label: Any = 1,
) -> Dict[str, Any]:
    """
    Calculate the Disparate Impact Ratio (DIR) using the new formula:
    DIR = (lowest group approval rate) / (highest group approval rate)

    Args:
        df: Dataset as a pandas DataFrame.
        target_col: Name of the outcome/target column.
        sensitive_col: Name of the sensitive/protected attribute column.
        positive_label: The label value considered "positive" (e.g. 1 or "approved").

    Returns:
        A dict with group rates, disparate impact ratio, and identification of min/max groups.
    """
    temp_df = df.copy()

    # 1. Map target_col if it's string-based (e.g., "approved"/"rejected" -> 1/0)
    if temp_df[target_col].dtype == 'object' or isinstance(positive_label, str):
        # Convert everything to string for comparison to avoid type errors
        pos_str = str(positive_label).lower()
        temp_df[target_col] = temp_df[target_col].astype(str).str.lower().apply(
            lambda x: 1 if x == pos_str or x == "approved" else 0
        )
        logger.info(f"[Fairness] Mapped target column '{target_col}' to binary 1/0.")

    # 2. Group by the sensitive attribute and calculate approval rates
    group_stats = temp_df.groupby(sensitive_col)[target_col].agg(['mean', 'count'])
    
    if len(group_stats) < 2:
        logger.warning(f"[Fairness] Insufficient data for '{sensitive_col}'. Only one group found.")
        return {
            "status": "insufficient data",
            "disparate_impact_ratio": 1.0,
            "groups": group_stats['mean'].to_dict()
        }

    # 3. Compute Disparate Impact: min_rate / max_rate
    rates = group_stats['mean']
    
    # Print debug logs for each group
    for group, rate in rates.items():
        logger.info(f"Group '{group}' approval rate: {rate*100:.2f}% (n={group_stats.loc[group, 'count']})")
        print(f"DEBUG: Group '{group}' approval rate: {rate*100:.2f}%")

    min_rate = float(rates.min())
    max_rate = float(rates.max())
    
    # Avoid division by zero
    dir_ratio = round(min_rate / max_rate, 4) if max_rate > 0 else 1.0
    
    logger.info(f"[Fairness] Final DI Calculation: {min_rate:.4f} / {max_rate:.4f} = {dir_ratio:.4f}")
    print(f"DEBUG: Final DI Calculation: {min_rate:.4f} / {max_rate:.4f} = {dir_ratio:.4f}")

    return {
        "baseline_group": str(rates.idxmax()),
        "minority_group": str(rates.idxmin()),
        "baseline_rate": round(max_rate, 4),
        "minority_rate": round(min_rate, 4),
        "disparate_impact_ratio": dir_ratio,
        "group_rates": {str(k): round(float(v), 4) for k, v in rates.items()},
        "status": "success"
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

    baseline_df = df[df[sensitive_col] == baseline_group]
    minority_df = df[df[sensitive_col] == minority_group]

    baseline_rate = (
        (baseline_df[target_col] == positive_label).sum() / len(baseline_df)
        if len(baseline_df) > 0
        else 0.0
    )
    minority_rate = (
        (minority_df[target_col] == positive_label).sum() / len(minority_df)
        if len(minority_df) > 0
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
    
    # Filter small groups
    valid_groups = group_stats[group_stats['count'] >= 10]
    
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

def run_shap_analysis(df: pd.DataFrame, target_col: str, sensitive_cols: List[str]) -> Dict[str, float]:
    """
    Run SHAP analysis using a RandomForestClassifier to find top 5 features driving the outcome.
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
        import shap
        
        temp_df = df.copy()
        
        for col in temp_df.columns:
            if temp_df[col].dtype == 'object':
                temp_df[col] = LabelEncoder().fit_transform(temp_df[col].astype(str))
                
        X = temp_df.drop(columns=[target_col])
        y = temp_df[target_col]
        
        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)
        
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X)
        
        # Handle binary vs multiclass output from TreeExplainer
        if isinstance(shap_values, list):
            shap_values_to_aggregate = shap_values[1]
        elif len(shap_values.shape) == 3: # Shap > = 0.40 format 
             shap_values_to_aggregate = shap_values[:,:,1]
        else:
            shap_values_to_aggregate = shap_values
            
        mean_abs_shap = np.abs(shap_values_to_aggregate).mean(axis=0)
        
        feature_scores = {feat: float(score) for feat, score in zip(X.columns, mean_abs_shap)}
        sorted_features = dict(sorted(feature_scores.items(), key=lambda item: item[1], reverse=True)[:5])
        
        return sorted_features
    except Exception as e:
        logger.error(f"SHAP analysis failed: {e}")
        return {"error": str(e)}

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

def run_full_audit(
    df: pd.DataFrame,
    target_col: str,
    sensitive_cols: List[str],
    positive_label: Any = 1,
) -> Dict[str, Any]:
    """
    Run a fairness audit.
    Updated to focus on accurate DI calculation for valid categorical attributes.
    """
    results: Dict[str, Any] = {}

    # Enforce: only use the first sensitive column provided if several exist
    if not sensitive_cols:
        return {}
    
    # We only process the primary sensitive attribute as per new requirements
    primary_col = sensitive_cols[0]

    # Check if the column is numeric (ignore if so)
    if pd.api.types.is_numeric_dtype(df[primary_col]):
        logger.warning(f"[Fairness] Ignoring numeric sensitive column: {primary_col}")
        return {
            primary_col: {
                "status": "error",
                "message": f"Column '{primary_col}' is numeric. Disparate impact is only valid for categorical attributes."
            }
        }

    # --- Core metrics ---
    dir_results = calculate_disparate_impact(df, target_col, primary_col, positive_label)
    
    if dir_results.get("status") == "insufficient data":
        results[primary_col] = {
            "status": "insufficient data",
            "message": "Only one group detected in the sensitive attribute. Metrics cannot be computed.",
            "is_biased": False,
            "risk_level": "LOW",
            "disparate_impact_ratio": 1.0
        }
    else:
        dir_ratio = dir_results["disparate_impact_ratio"]
        spd = calculate_statistical_parity(df, target_col, primary_col, positive_label)
        
        # Threshold: DI < 0.8 is biased (FAIL)
        is_biased = dir_ratio < 0.8
        risk = "HIGH" if is_biased else "LOW"

        results[primary_col] = {
            "baseline_group": dir_results["baseline_group"],
            "minority_group": dir_results["minority_group"],
            "baseline_positive_rate": dir_results["baseline_rate"],
            "minority_positive_rate": dir_results["minority_rate"],
            "disparate_impact_ratio": dir_ratio,
            "statistical_parity_difference": float(spd),
            "risk_level": risk,
            "is_biased": bool(is_biased),
            "interpretation": f"Disparate Impact is {dir_ratio:.3f}. Threshold for FAIR is 0.800.",
        }

    return results


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _build_interpretation(
    col: str,
    baseline_group: str,
    minority_group: str,
    baseline_rate: float,
    minority_rate: float,
    dir_ratio: float,
    spd: float,
    risk: str,
    is_biased: bool,
) -> str:
    """Build a plain-English explanation of the fairness metrics for one column."""
    pct_baseline = round(baseline_rate * 100, 1)
    pct_minority = round(minority_rate * 100, 1)
    pct_gap = round(abs(spd) * 100, 1)

    direction = "lower" if spd < 0 else "higher"

    bias_verdict = (
        f"This indicates POTENTIAL BIAS (risk level: {risk})."
        if is_biased
        else f"This is within the acceptable fairness threshold (risk level: {risk})."
    )

    return (
        f"For the '{col}' attribute: the baseline group ('{baseline_group}') has a "
        f"positive outcome rate of {pct_baseline}%, while the minority group "
        f"('{minority_group}') has a rate of {pct_minority}%. "
        f"The minority group's rate is {pct_gap}% {direction} than the baseline group's. "
        f"The Disparate Impact Ratio is {dir_ratio:.4f} (ideal ≥ 0.8) and the "
        f"Statistical Parity Difference is {spd:.4f} (ideal = 0). "
        f"{bias_verdict}"
    )
