"""
FairLens AI — Unified Data Loader
----------------------------------
Handles loading datasets from multiple file formats and external sources.
All loaders convert to pandas DataFrame and validate minimum requirements.
"""

import io
import os
import re
import uuid
import zipfile
import logging
import tempfile
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported Extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv"}
MIN_ROWS = 10


# ---------------------------------------------------------------------------
# File Format Loaders
# ---------------------------------------------------------------------------

def _load_csv(contents: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(contents))


def _load_excel(contents: bytes) -> pd.DataFrame:
    import openpyxl  # noqa: F401 — ensure dependency is installed
    return pd.read_excel(io.BytesIO(contents), engine="openpyxl")


def _load_json(contents: bytes) -> pd.DataFrame:
    """Load JSON — supports array-of-objects and records orientation."""
    text = contents.decode("utf-8")
    try:
        return pd.read_json(io.StringIO(text), orient="records")
    except ValueError:
        # Fallback: try default orient
        return pd.read_json(io.StringIO(text))


def _load_parquet(contents: bytes) -> pd.DataFrame:
    import pyarrow  # noqa: F401 — ensure dependency is installed
    return pd.read_parquet(io.BytesIO(contents))


def _load_tsv(contents: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(contents), sep="\t")


# Extension → loader mapping
_LOADERS = {
    ".csv": _load_csv,
    ".xlsx": _load_excel,
    ".xls": _load_excel,
    ".json": _load_json,
    ".parquet": _load_parquet,
    ".tsv": _load_tsv,
}


# ---------------------------------------------------------------------------
# Public API — Upload File
# ---------------------------------------------------------------------------

async def load_from_upload(file: UploadFile) -> Tuple[pd.DataFrame, str]:
    """
    Load a dataset from an uploaded file (any supported format).

    Returns:
        (DataFrame, original_filename)

    Raises:
        HTTPException on invalid format, parse error, or insufficient rows.
    """
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Accepted formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    try:
        contents = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file '%s': %s", filename, exc)
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    loader = _LOADERS[ext]
    try:
        df = loader(contents)
    except Exception as exc:
        logger.error("Failed to parse '%s' (format=%s): %s", filename, ext, exc)
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse the {ext} file. Ensure it is valid: {str(exc)}",
        )

    _validate_dataframe(df, filename)
    logger.info("Loaded file '%s' — %d rows, %d cols", filename, len(df), len(df.columns))
    return df, filename


# ---------------------------------------------------------------------------
# Public API — Kaggle
# ---------------------------------------------------------------------------

KAGGLE_URL_PATTERN = re.compile(
    r"kaggle\.com/datasets/(?P<owner>[^/]+)/(?P<dataset>[^/?#]+)"
)


def load_from_kaggle(kaggle_url: str, username: str, key: str) -> Tuple[pd.DataFrame, str]:
    """
    Download a dataset from Kaggle and load the first CSV found.

    Returns:
        (DataFrame, dataset_name)
    """
    # 1. Parse slug from URL
    match = KAGGLE_URL_PATTERN.search(kaggle_url)
    if not match:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid Kaggle URL. Expected format: "
                "https://www.kaggle.com/datasets/{owner}/{dataset-name}"
            ),
        )

    slug = f"{match.group('owner')}/{match.group('dataset')}"

    # 2. Set credentials temporarily (never persisted)
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()

        download_dir = os.path.join(tempfile.gettempdir(), f"fairlens_{uuid.uuid4().hex[:8]}")
        os.makedirs(download_dir, exist_ok=True)

        logger.info("Downloading Kaggle dataset '%s' to '%s'", slug, download_dir)
        api.dataset_download_files(slug, path=download_dir, unzip=True)

        # 3. Find first CSV in the extracted files
        csv_files = list(Path(download_dir).rglob("*.csv"))
        if not csv_files:
            raise HTTPException(
                status_code=404,
                detail=f"No CSV files found in Kaggle dataset '{slug}'.",
            )

        df = pd.read_csv(csv_files[0])
        dataset_name = f"kaggle_{match.group('dataset')}.csv"
        _validate_dataframe(df, dataset_name)

        logger.info("Kaggle dataset '%s' loaded — %d rows from '%s'", slug, len(df), csv_files[0].name)
        return df, dataset_name

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Kaggle download failed for '%s': %s", slug, exc)
        error_msg = str(exc).lower()
        if "401" in error_msg or "unauthorized" in error_msg or "invalid credentials" in error_msg:
            raise HTTPException(status_code=401, detail="Kaggle authentication failed. Check your username and API key.")
        elif "404" in error_msg or "not found" in error_msg:
            raise HTTPException(status_code=404, detail=f"Kaggle dataset '{slug}' not found.")
        else:
            raise HTTPException(status_code=500, detail=f"Kaggle download failed: {str(exc)}")
    finally:
        # Clean up env vars
        os.environ.pop("KAGGLE_USERNAME", None)
        os.environ.pop("KAGGLE_KEY", None)


# ---------------------------------------------------------------------------
# Public API — HuggingFace
# ---------------------------------------------------------------------------

def load_from_huggingface(
    dataset_id: str,
    split: str = "train",
    hf_token: Optional[str] = None,
) -> Tuple[pd.DataFrame, str]:
    """
    Load a dataset from HuggingFace Hub and convert to DataFrame.

    Returns:
        (DataFrame, dataset_name)
    """
    try:
        from datasets import load_dataset

        logger.info("Loading HuggingFace dataset '%s' (split=%s)", dataset_id, split)

        kwargs = {"path": dataset_id, "split": split}
        if hf_token:
            kwargs["token"] = hf_token

        hf_dataset = load_dataset(**kwargs)
        df = hf_dataset.to_pandas()

        dataset_name = f"hf_{dataset_id.replace('/', '_')}.csv"
        _validate_dataframe(df, dataset_name)

        logger.info("HuggingFace dataset '%s' loaded — %d rows", dataset_id, len(df))
        return df, dataset_name

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("HuggingFace load failed for '%s': %s", dataset_id, exc)
        error_msg = str(exc).lower()
        if "not found" in error_msg or "doesn't exist" in error_msg or "404" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=f"HuggingFace dataset '{dataset_id}' not found. Check the dataset ID.",
            )
        elif "authentication" in error_msg or "token" in error_msg or "gated" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="This dataset requires authentication. Please provide a valid HuggingFace token.",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load HuggingFace dataset: {str(exc)}",
            )


# ---------------------------------------------------------------------------
# Internal Validation
# ---------------------------------------------------------------------------

def _validate_dataframe(df: pd.DataFrame, source_name: str) -> None:
    """Validate a loaded DataFrame meets minimum requirements."""
    if df is None or df.empty:
        raise HTTPException(
            status_code=400,
            detail=f"The dataset '{source_name}' is empty.",
        )
    if len(df) < MIN_ROWS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The dataset '{source_name}' has only {len(df)} rows. "
                f"A minimum of {MIN_ROWS} rows is required for meaningful analysis."
            ),
        )
    if len(df.columns) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"The dataset '{source_name}' must have at least 2 columns.",
        )
