"""
FairLens AI — External Data Sources Routes
---------------------------------------------
Endpoints for fetching datasets from Kaggle and HuggingFace Hub.
"""

import uuid
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.routes.upload import file_store
from app.services.data_loader import load_from_kaggle, load_from_huggingface

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class KaggleRequest(BaseModel):
    kaggle_url: str = Field(..., description="Full Kaggle dataset URL")
    kaggle_username: str = Field(..., description="Kaggle username")
    kaggle_key: str = Field(..., description="Kaggle API key")


class HuggingFaceRequest(BaseModel):
    dataset_id: str = Field(..., description="HuggingFace dataset ID (e.g. scikit-learn/adult-census-income)")
    split: str = Field("train", description="Dataset split: train, test, or validation")
    hf_token: Optional[str] = Field(None, description="Optional HuggingFace token for private datasets")


# ---------------------------------------------------------------------------
# POST /api/upload/kaggle
# ---------------------------------------------------------------------------
@router.post("/upload/kaggle", summary="Fetch dataset from Kaggle")
async def upload_from_kaggle(request: KaggleRequest) -> Dict[str, Any]:
    """
    Download a dataset from Kaggle, load the first CSV found, and store in memory.
    Credentials are used only for this request and never stored.
    """
    logger.info("Kaggle fetch requested: %s", request.kaggle_url)

    df, dataset_name = load_from_kaggle(
        kaggle_url=request.kaggle_url,
        username=request.kaggle_username,
        key=request.kaggle_key,
    )

    # Auto-detect configuration
    try:
        from app.services.auto_detect import auto_detect_columns
        auto_config = auto_detect_columns(df)
    except Exception as exc:
        logger.error("Auto-detection failed for Kaggle dataset: %s", exc)
        auto_config = {
            "target_column": df.columns[-1],
            "positive_value": 1,
            "sensitive_attributes": [],
            "confidence_score": 0.1,
        }

    file_id = uuid.uuid4().hex[:8]
    file_store[file_id] = {
        "df": df,
        "auto_config": auto_config,
        "filename": dataset_name,
    }

    return {
        "file_id": file_id,
        "filename": dataset_name,
        "rows": len(df),
        "columns": list(df.columns),
        "auto_config": auto_config,
        "source": "kaggle",
        "message": f"Kaggle dataset loaded successfully. {len(df)} rows, {len(df.columns)} columns.",
    }


# ---------------------------------------------------------------------------
# POST /api/upload/huggingface
# ---------------------------------------------------------------------------
@router.post("/upload/huggingface", summary="Fetch dataset from HuggingFace")
async def upload_from_huggingface(request: HuggingFaceRequest) -> Dict[str, Any]:
    """
    Load a dataset from HuggingFace Hub and store in memory.
    The optional token is used only for this request and never stored.
    """
    logger.info("HuggingFace fetch requested: %s (split=%s)", request.dataset_id, request.split)

    df, dataset_name = load_from_huggingface(
        dataset_id=request.dataset_id,
        split=request.split,
        hf_token=request.hf_token,
    )

    # Auto-detect configuration
    try:
        from app.services.auto_detect import auto_detect_columns
        auto_config = auto_detect_columns(df)
    except Exception as exc:
        logger.error("Auto-detection failed for HuggingFace dataset: %s", exc)
        auto_config = {
            "target_column": df.columns[-1],
            "positive_value": 1,
            "sensitive_attributes": [],
            "confidence_score": 0.1,
        }

    file_id = uuid.uuid4().hex[:8]
    file_store[file_id] = {
        "df": df,
        "auto_config": auto_config,
        "filename": dataset_name,
    }

    return {
        "file_id": file_id,
        "filename": dataset_name,
        "rows": len(df),
        "columns": list(df.columns),
        "auto_config": auto_config,
        "source": "huggingface",
        "message": f"HuggingFace dataset loaded successfully. {len(df)} rows, {len(df.columns)} columns.",
    }
