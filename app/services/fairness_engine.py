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

import pandas as pd


# ---------------------------------------------------------------------------
# Individual Metric Functions
# ---------------------------------------------------------------------------

def calculate_disparate_impact(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    positive_label: int = 1,
) -> Dict[str, Any]:
    """
    Calculate the Disparate Impact Ratio (DIR) for a sensitive column.

    DIR = (positive rate for minority group) / (positive rate for baseline group)

    The baseline group is the most frequent value in the sensitive column.
    The minority group is the least frequent value (for the clearest contrast).

    Args:
        df: Dataset as a pandas DataFrame.
        target_col: Name of the binary outcome/target column.
        sensitive_col: Name of the sensitive/protected attribute column.
        positive_label: The label value considered "positive" (default: 1).

    Returns:
        A dict with baseline_group, minority_group, baseline_rate,
        minority_rate, and disparate_impact_ratio.
    """
    value_counts = df[sensitive_col].value_counts()

    # Baseline = most frequent group; minority = least frequent group
    baseline_group = value_counts.index[0]
    minority_group = value_counts.index[-1]

    # Positive outcome rates per group
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

    # Avoid division by zero — if baseline has 0% positive rate, DIR is undefined
    if baseline_rate == 0:
        disparate_impact_ratio = 0.0
    else:
        disparate_impact_ratio = round(minority_rate / baseline_rate, 4)

    return {
        "baseline_group": str(baseline_group),
        "minority_group": str(minority_group),
        "baseline_rate": round(baseline_rate, 4),
        "minority_rate": round(minority_rate, 4),
        "disparate_impact_ratio": disparate_impact_ratio,
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
# Full Audit Orchestration
# ---------------------------------------------------------------------------

def run_full_audit(
    df: pd.DataFrame,
    target_col: str,
    sensitive_cols: List[str],
    positive_label: int = 1,
) -> Dict[str, Any]:
    """
    Run a complete fairness audit across all specified sensitive columns.

    For each sensitive column, computes:
      - Disparate Impact Ratio
      - Statistical Parity Difference
      - Risk level
      - Bias flag (is_biased = True if DIR < 0.8)
      - Plain-English interpretation

    Args:
        df: Dataset as a pandas DataFrame.
        target_col: Name of the binary outcome/target column.
        sensitive_cols: List of sensitive/protected attribute column names.
        positive_label: The label value considered "positive" (default: 1).

    Returns:
        A dict mapping each sensitive column name to its audit metrics.
    """
    results: Dict[str, Any] = {}

    for col in sensitive_cols:
        # --- Core metrics ---
        dir_data = calculate_disparate_impact(df, target_col, col, positive_label)
        spd = calculate_statistical_parity(df, target_col, col, positive_label)
        dir_ratio = dir_data["disparate_impact_ratio"]
        risk = get_risk_level(dir_ratio)
        # is_biased when DIR is outside the symmetric acceptable band [0.8, 1.25].
        # DIR > 1.25 means the *minority* group is actually advantaged — still a bias signal.
        is_biased = dir_ratio < 0.8 or dir_ratio > (1 / 0.8)

        # --- Human-readable interpretation ---
        interpretation = _build_interpretation(
            col=col,
            baseline_group=dir_data["baseline_group"],
            minority_group=dir_data["minority_group"],
            baseline_rate=dir_data["baseline_rate"],
            minority_rate=dir_data["minority_rate"],
            dir_ratio=dir_ratio,
            spd=spd,
            risk=risk,
            is_biased=is_biased,
        )

        results[col] = {
            "baseline_group": str(dir_data["baseline_group"]),
            "minority_group": str(dir_data["minority_group"]),
            "baseline_positive_rate": float(dir_data["baseline_rate"]),
            "minority_positive_rate": float(dir_data["minority_rate"]),
            "disparate_impact_ratio": float(dir_ratio),
            "statistical_parity_difference": float(spd),
            "risk_level": risk,
            "is_biased": bool(is_biased),   # cast numpy.bool_ → Python bool
            "interpretation": interpretation,
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
