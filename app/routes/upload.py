"""
FairLens AI — Upload Routes
-----------------------------
Handles CSV file uploads and file metadata retrieval.
Files are stored in-memory in `file_store` for the lifetime of the process.
"""

import io
import uuid
import logging
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.utils.validator import validate_csv

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# In-Memory File Store
# ---------------------------------------------------------------------------
# Maps file_id (str) → pandas DataFrame.
# This is intentionally module-level so audit.py can import it directly.
file_store: Dict[str, pd.DataFrame] = {}


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------
@router.post("/upload", summary="Upload a CSV dataset")
async def upload_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept a CSV file upload, validate it, store it in memory, and return metadata.

    Validations:
    - File must have a `.csv` extension.
    - File must contain at least 10 data rows.

    Returns:
        file_id, filename, row count, column list, and a success message.
    """
    # --- Validate file extension ---
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files (.csv) are accepted.",
        )

    # --- Read file content ---
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        logger.error("Failed to parse CSV file '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse the CSV file. Ensure it is valid: {str(exc)}",
        )

    # --- Validate content (rows, emptiness) ---
    validate_csv(df)

    # --- Store in memory with a unique ID ---
    file_id = uuid.uuid4().hex[:8]
    file_store[file_id] = df

    logger.info(
        "File uploaded — id=%s, name=%s, rows=%d, cols=%d",
        file_id,
        file.filename,
        len(df),
        len(df.columns),
    )

    return {
        "file_id": file_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "message": (
            f"File '{file.filename}' uploaded successfully. "
            f"Use file_id '{file_id}' to run an audit."
        ),
    }


# ---------------------------------------------------------------------------
# GET /api/files/{file_id}/columns
# ---------------------------------------------------------------------------
@router.get("/files/{file_id}/columns", summary="Get file columns and preview")
async def get_file_columns(file_id: str) -> Dict[str, Any]:
    """
    Retrieve the column list, row count, and a preview of the first 3 rows
    for a previously uploaded file.

    Args:
        file_id: The 8-character ID returned by the upload endpoint.

    Returns:
        file_id, column list, row count, and first 3 rows as a list of dicts.
    """
    if file_id not in file_store:
        raise HTTPException(
            status_code=404,
            detail=f"File with id '{file_id}' not found. Please upload the file first.",
        )

    df = file_store[file_id]

    return {
        "file_id": file_id,
        "columns": list(df.columns),
        "row_count": len(df),
        # Return first 3 rows as list of dicts (JSON-serializable)
        "preview": df.head(3).to_dict(orient="records"),
    }
