"""
FairLens AI — Visualize Routes
---------------------------------
Server-side chart generation for data exploration.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.routes.upload import file_store
from app.services.chart_generator import generate_charts

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request Schema
# ---------------------------------------------------------------------------

class VisualizeRequest(BaseModel):
    file_id: str = Field(..., description="The file ID from upload")
    columns: List[str] = Field(..., description="Columns to visualize")


# ---------------------------------------------------------------------------
# POST /api/visualize
# ---------------------------------------------------------------------------
@router.post("/visualize", summary="Generate data visualizations")
async def visualize_data(request: VisualizeRequest) -> Dict[str, Any]:
    """
    Generate matplotlib charts for the requested columns.

    - Numeric columns → histogram
    - Categorical (≤15 unique) → pie chart
    - High-cardinality categorical → bar chart (top 10)

    Returns base64-encoded PNG images for each column.
    """
    if request.file_id not in file_store:
        raise HTTPException(
            status_code=404,
            detail=f"File with id '{request.file_id}' not found.",
        )

    file_entry = file_store[request.file_id]
    if isinstance(file_entry, dict):
        df = file_entry["df"]
    else:
        df = file_entry

    if not request.columns:
        raise HTTPException(
            status_code=400,
            detail="At least one column must be specified for visualization.",
        )

    # Validate columns exist
    missing = [c for c in request.columns if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Columns not found in dataset: {', '.join(missing)}",
        )

    try:
        charts = generate_charts(df, request.columns)
        return {"charts": charts}
    except Exception as exc:
        logger.error("Chart generation failed for file '%s': %s", request.file_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Chart generation failed: {str(exc)}",
        )
