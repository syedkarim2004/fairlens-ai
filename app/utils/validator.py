"""
FairLens AI — Input Validators
-------------------------------
Reusable validation helpers for CSV data and column checks.
Raises FastAPI HTTPExceptions so errors propagate cleanly through the API.
"""

from typing import List

import pandas as pd
from fastapi import HTTPException


# Minimum number of rows required for a meaningful fairness audit
MIN_ROWS = 10


def validate_csv(df: pd.DataFrame) -> None:
    """
    Validate that a DataFrame meets the minimum requirements for a fairness audit.

    Raises:
        HTTPException 400: If the file is empty or has fewer than MIN_ROWS rows.
    """
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty. Please provide a valid dataset.",
        )

    if len(df) < MIN_ROWS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The dataset must contain at least {MIN_ROWS} rows for a meaningful audit. "
                f"Uploaded file has only {len(df)} row(s)."
            ),
        )


def validate_columns_exist(df: pd.DataFrame, columns: List[str]) -> None:
    """
    Validate that all requested columns are present in the DataFrame.

    Args:
        df: The pandas DataFrame to check.
        columns: A list of column names that must exist in the DataFrame.

    Raises:
        HTTPException 400: If one or more columns are missing.
    """
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The following column(s) were not found in the dataset: {missing}. "
                f"Available columns: {list(df.columns)}"
            ),
        )
