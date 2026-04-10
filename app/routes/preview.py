"""
FairLens AI — Preview Routes
-------------------------------
Provides rich dataset preview with statistics and auto-detected suggestions.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.routes.upload import file_store
from app.services.auto_detector import get_dataset_preview

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/files/{file_id}/preview
# ---------------------------------------------------------------------------
@router.get("/files/{file_id}/preview", summary="Get dataset preview with statistics")
async def get_file_preview(file_id: str) -> Dict[str, Any]:
    """
    Retrieve a comprehensive preview of an uploaded dataset, including:
    - First 10 rows
    - Column data types
    - Per-column statistics (numeric and categorical)
    - Auto-detected sensitive columns, target column, and domain
    """
    if file_id not in file_store:
        raise HTTPException(
            status_code=404,
            detail=f"File with id '{file_id}' not found. Please upload the file first.",
        )

    file_entry = file_store[file_id]
    if isinstance(file_entry, dict):
        df = file_entry["df"]
        filename = file_entry.get("filename", "dataset")
    else:
        df = file_entry
        filename = "dataset"

    try:
        preview = get_dataset_preview(df, filename)
        preview["file_id"] = file_id
        return preview
    except Exception as exc:
        logger.error("Preview generation failed for file '%s': %s", file_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(exc)}",
        )
