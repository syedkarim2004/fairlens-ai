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
@router.post("/upload", summary="Upload a dataset (CSV, Excel, JSON, Parquet, TSV)")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept a dataset upload in multiple formats, validate it, store it in memory,
    and return metadata.

    Supported formats: .csv, .xlsx, .xls, .json, .parquet, .tsv

    Returns:
        file_id, filename, row count, column list, and a success message.
    """
    from app.services.data_loader import load_from_upload

    # --- Load file using unified data loader (validates format + min rows) ---
    df, filename = await load_from_upload(file)

    # --- Store in memory with a unique ID ---
    file_id = uuid.uuid4().hex[:8]
    
    # --- Auto-Detection (Zero-Config) ---
    try:
        from app.services.auto_detect import auto_detect_columns
        auto_config = auto_detect_columns(df)
    except Exception as exc:
        logger.error("Auto-detection failed: %s", exc)
        auto_config = {
            "target_column": df.columns[-1],
            "positive_value": 1,
            "sensitive_attributes": [],
            "confidence_score": 0.1
        }
        
    file_store[file_id] = {
        "df": df,
        "auto_config": auto_config,
        "filename": file.filename
    }

    logger.info(
        "File uploaded — id=%s, name=%s, rows=%d, cols=%d, detected_target=%s",
        file_id,
        file.filename,
        len(df),
        len(df.columns),
        auto_config.get("target_column")
    )

    return {
        "file_id": file_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "auto_config": auto_config,
        "message": (
            f"File '{file.filename}' uploaded and analyzed successfully. "
            f"System detected target '{auto_config.get('target_column')}'."
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

    file_entry = file_store[file_id]
    if isinstance(file_entry, dict):
        df = file_entry["df"]
    else:
        df = file_entry

    return {
        "file_id": file_id,
        "columns": list(df.columns),
        "row_count": len(df),
        # Return first 3 rows as list of dicts (JSON-serializable)
        "preview": df.head(3).to_dict(orient="records"),
    }

# ---------------------------------------------------------------------------
# POST /api/upload/real
# ---------------------------------------------------------------------------
@router.post("/upload/real", summary="Upload dataset and auto-detect sensitive columns")
async def upload_real_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept dataset, store it, and automatically analyze headers to recommend
    target_column and sensitive_columns from known roots.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")

    validate_csv(df)

    file_id = uuid.uuid4().hex[:8]
    
    # --- Use the new Auto-Detection Engine ---
    try:
        from app.services.auto_detect import auto_detect_columns
        auto_config = auto_detect_columns(df)
    except Exception as exc:
        logger.error("Auto-detection in legacy endpoint failed: %s", exc)
        auto_config = {
            "target_column": df.columns[-1],
            "positive_value": 1,
            "sensitive_attributes": [],
            "confidence_score": 0.1
        }

    file_store[file_id] = {
        "df": df,
        "auto_config": auto_config,
        "filename": file.filename
    }

    return {
        "file_id": file_id,
        "filename": file.filename,
        "columns": df.columns.tolist(),
        "auto_config": auto_config,
        "recommended_sensitive_columns": auto_config.get("sensitive_attributes", []),
        "recommended_target_column": auto_config.get("target_column"),
        "message": "File uploaded and analyzed successfully using autonomous engine."
    }
