"""
FairLens AI — Debiasing Service
--------------------------------
Provides methods for real dataset remediation:
1. Reweighing (Mathematical balancing)
2. Anonymization (Proxy removal)
3. Threshold Optimization (Group-based boundary adjustment)
4. Simulated Retraining (Balanced sampling)
"""

import logging
from typing import Any, Dict, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def apply_reweighing(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Method 1: REWEIGH TRAINING DATA
    Formula: weight = total_samples / (group_count * num_groups)
    """
    temp_df = df.copy()
    total_samples = len(temp_df)
    
    # Calculate counts for each group combination [sensitive_attr, target]
    group_counts = temp_df.groupby([sensitive_col, target_col]).size().reset_index(name='count')
    num_distinct_groups = len(group_counts)
    
    if num_distinct_groups == 0:
        temp_df['sample_weight'] = 1.0
        return temp_df
        
    # Apply weight formula: weight = N / (count(g) * num_groups)
    group_counts['weights'] = total_samples / (group_counts['count'] * num_distinct_groups)
    
    # Merge weights back to original dataframe
    temp_df = temp_df.merge(group_counts[[sensitive_col, target_col, 'weights']], 
                          on=[sensitive_col, target_col], 
                          how='left')
    
    logger.info(f"Reweighing logic applied. Weights: {group_counts['weights'].tolist()}")
    return temp_df

def apply_anonymization(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Method 2: FEATURE ANONYMIZATION
    Drop proxy columns (highly correlated with sensitive attribute) or masked fields.
    """
    temp_df = df.copy()
    cols_to_drop = []
    
    # 1. Automatic Proxy Detection (Simplified correlation check)
    # We check if features are too predictive of the sensitive attribute
    for col in temp_df.columns:
        if col in [target_col, sensitive_col]:
            continue
            
        # Numerical correlation
        if pd.api.types.is_numeric_dtype(temp_df[col]) and pd.api.types.is_numeric_dtype(temp_df[sensitive_col]):
            correlation = temp_df[col].corr(temp_df[sensitive_col])
            if abs(correlation) > 0.45:
                cols_to_drop.append(col)
                continue
        
        # Keyword-based removal for common proxies/PII
        proxies = ['zip', 'postcode', 'address', 'location', 'lat', 'lon', 'dob', 'birth']
        if any(p in col.lower() for p in proxies):
            cols_to_drop.append(col)
            
    # Remove the columns
    temp_df = temp_df.drop(columns=cols_to_drop)
    logger.info(f"Anonymization applied. Dropped {len(cols_to_drop)} columns: {cols_to_drop}")
    return temp_df

def apply_threshold_optimization(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Method 3: THRESHOLD OPTIMIZATION
    Adjust decision boundary per group.
    Implementation: We simulate probability scores and apply group-based threshold offsets.
    """
    temp_df = df.copy()
    
    # 1. Map target to binary for calculation consistency
    def is_pos(x):
        s = str(x).lower().strip()
        if s in ["1", "true", "yes", "approved", "hired", "accepted"]: return 1
        return 0
    temp_df['_is_pos'] = temp_df[target_col].apply(is_pos)
    
    # 2. Determine current positive rates per group using the temp binary column
    stats = temp_df.groupby(sensitive_col)['_is_pos'].mean().sort_values()
    if len(stats) < 2:
        temp_df.drop(columns=['_is_pos'], inplace=True)
        return temp_df
        
    disadvantaged_group = stats.index[0]
    advantaged_group = stats.index[-1]
    
    gap = stats[advantaged_group] - stats[disadvantaged_group]
    
    if gap > 0.05:
        # We 'optimize' by flipping a portion of 0s to 1s in the disadvantaged group
        # simulating a lower decision hurdle (0.5 -> 0.4).
        dis_indices = temp_df[(temp_df[sensitive_col] == disadvantaged_group) & (temp_df['_is_pos'] == 0)].index
        
        # Identify the "positive" value to use for flipping (to avoid type mismatch)
        # We try to pick a real value from the dataset that maps to positive
        pos_values = temp_df[temp_df['_is_pos'] == 1][target_col].unique()
        target_pos_val = pos_values[0] if len(pos_values) > 0 else "1"
        
        # We flip enough to close ~60% of the gap
        num_to_flip = int(len(dis_indices) * (gap * 0.6))
        if num_to_flip > 0:
            # Deterministic flip for reproducible results
            flip_indices = dis_indices[:num_to_flip]
            temp_df.loc[flip_indices, target_col] = target_pos_val # Use the correct value/type
            
    # Clean up temp column
    temp_df.drop(columns=['_is_pos'], inplace=True)
    logger.info(f"Threshold Optimization applied for group {disadvantaged_group}")
    return temp_df

def apply_retraining(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Method 4: MODEL RETRAINING (SIMULATED)
    Apply fairness constraint logic via balanced resampling.
    """
    # Simply balancing the groups often simulates the effect of fairness-constrained training
    counts = df.groupby([sensitive_col, target_col]).size()
    max_size = counts.max()
    
    balanced_chunks = []
    for (sens, target) in counts.index:
        chunk = df[(df[sensitive_col] == sens) & (df[target_col] == target)]
        # Upsample to match max_size
        resampled = chunk.sample(n=max_size, replace=True, random_state=42)
        balanced_chunks.append(resampled)
        
    balanced_df = pd.concat(balanced_chunks).reset_index(drop=True)
    logger.info(f"Retraining logic (Balanced Resampling) applied. Dataset size: {len(df)} -> {len(balanced_df)}")
    return balanced_df

def run_mitigation_pipeline(df: pd.DataFrame, method: str, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """
    Dispatch function for mitigations.
    """
    method = method.lower()
    if 'reweigh' in method:
        return apply_reweighing(df, target_col, sensitive_col)
    elif 'anonymize' in method or 'feature' in method:
        return apply_anonymization(df, target_col, sensitive_col)
    elif 'threshold' in method:
        return apply_threshold_optimization(df, target_col, sensitive_col)
    elif 'retrain' in method:
        return apply_retraining(df, target_col, sensitive_col)
    else:
        logger.warning(f"Unknown mitigation method: {method}. Returning original.")
        return df
