from typing import List, Any, Tuple, Dict, Optional
import numpy as np
import pandas as pd
from fastapi import HTTPException


# Minimum number of rows required for a comparison (at least 2)
MIN_ROWS = 2


def validate_csv(df: pd.DataFrame) -> None:
    """
    Validate that a DataFrame meets the minimum requirements for a fairness audit.

    Raises:
        HTTPException 400: If the file is empty or has fewer than 2 rows.
    """
    if df is None or df.empty:
        raise HTTPException(
            status_code=400,
            detail="The uploaded dataset is empty or invalid. Please provide a valid CSV.",
        )

    if len(df) < MIN_ROWS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The dataset must contain at least {MIN_ROWS} rows for a comparison. "
                f"Uploaded file has only {len(df)} row(s)."
            ),
        )


def validate_columns_exist(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """
    Validate that all requested columns are present in the DataFrame.
    Supports case-insensitive matching — returns the actual column names from the DF.

    Args:
        df: The pandas DataFrame to check.
        columns: A list of proposed column names.

    Returns:
        The list of actual column names as they appear in the DataFrame.

    Raises:
        HTTPException 400: If one or more columns are missing.
    """
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Dataframe is empty or null.")

    actual_cols = []
    missing = []
    
    df_cols_lower = {col.lower(): col for col in df.columns}
    
    for col in columns:
        if col is None: continue
        if col in df.columns:
            actual_cols.append(col)
        elif col.lower() in df_cols_lower:
            actual_cols.append(df_cols_lower[col.lower()])
        else:
            missing.append(col)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The following column(s) were not found in the dataset: {missing}. "
                f"Available columns: {list(df.columns)}"
            ),
        )
    return actual_cols


def is_column_valid(df: pd.DataFrame, col: str, is_target: bool = False) -> Tuple[bool, str]:
    """
    Check if a column is technically valid for a fairness audit.
    Returns (is_valid, error_message).
    
    Soft Validation Rules:
    - Target: Never skip if it exists and has >1 unique value (or is numeric).
    - Sensitive: Skip only if all-null or <2 unique values.
    """
    if col not in df.columns:
        return False, f"Missing: Column '{col}' not found."
        
    col_data = df[col].dropna()
    if col_data.empty:
        return False, f"Empty: Column '{col}' is all null."
        
    unique_vals = col_data.unique()
    if len(unique_vals) < 2:
        # Numeric targets can be binarized via threshold later
        if is_target and pd.api.types.is_numeric_dtype(df[col]):
            return True, ""
        return False, f"Constant: Column '{col}' has only one unique value: {list(unique_vals)}."
        
    # High Cardinality Check (Softened)
    if not is_target:
        if len(unique_vals) > len(df) * 0.95 and len(df) > 100:
            # We don't reject anymore, we just return True but the engine/AI should warn
            # For now, let's keep it True to ensure '0 attributes' doesn't happen.
            return True, "" 
            
    return True, ""


def normalize_dataset_deterministic(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Perform strict deterministic pre-processing:
    1. Sort columns alphabetically.
    2. Drop rows with null in target.
    3. Fill missing values: median (numeric) or mode (categorical).
    4. Sort index and reset.
    """
    if df is None or df.empty:
        return df

    # 1. Sort Columns Alphabetically
    df = df.reindex(sorted(df.columns), axis=1)

    # 2. Drop Null Target Rows
    if target_col in df.columns:
        df = df.dropna(subset=[target_col])

    # 3. Fill Missing Values
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                fill_val = df[col].median()
            else:
                mode_vals = df[col].mode()
                fill_val = mode_vals[0] if not mode_vals.empty else "N/A"
            df[col] = df[col].fillna(fill_val)

    # 4. Sort Index & Reset
    df = df.sort_index().reset_index(drop=True)
    
    return df


def validate_audit_readiness(df: pd.DataFrame, target_col: str, sensitive_cols: List[str]) -> None:
    """
    Perform deep validation to ensure at least some parts of the dataset are ready.
    """
    # Target must be valid for the audit to start
    valid_target, target_err = is_column_valid(df, target_col, is_target=True)
    if not valid_target:
        raise HTTPException(status_code=400, detail=target_err)
