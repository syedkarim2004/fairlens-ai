"""
FairLens AI — Chart Generator
-------------------------------
Server-side matplotlib chart generation for data visualization.
All charts are rendered to PNG and returned as base64-encoded strings.
"""

import io
import base64
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Force non-interactive backend before any pyplot import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Color Palette
# ---------------------------------------------------------------------------
GOOGLE_BLUE = "#4285F4"
GOOGLE_GREEN = "#34A853"
GOOGLE_YELLOW = "#FBBC04"
GOOGLE_RED = "#EA4335"
GOOGLE_GREY = "#5F6368"
GOOGLE_DARK_BLUE = "#1A73E8"
GOOGLE_DARK_RED = "#D93025"
GOOGLE_AMBER = "#F9AB00"

PALETTE = [
    GOOGLE_BLUE, GOOGLE_RED, GOOGLE_YELLOW, GOOGLE_GREEN,
    GOOGLE_GREY, GOOGLE_DARK_BLUE, GOOGLE_DARK_RED, GOOGLE_AMBER,
    "#8E24AA", "#00897B", "#F4511E", "#6D4C41",
]

# Chart styling defaults
FONT_FAMILY = "sans-serif"
TITLE_SIZE = 14
LABEL_SIZE = 11
TICK_SIZE = 9


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_charts(df: pd.DataFrame, columns: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Generate charts for the requested columns.

    Returns:
        {column_name: {"type": "histogram"|"pie"|"bar", "image_base64": "data:image/png;base64,..."}}
    """
    charts: Dict[str, Dict[str, str]] = {}

    for col in columns:
        if col not in df.columns:
            logger.warning("Column '%s' not found in DataFrame — skipping chart.", col)
            continue

        try:
            series = df[col].dropna()

            if pd.api.types.is_numeric_dtype(series):
                chart_type = "histogram"
                img = _generate_histogram(series, col)
            elif series.nunique() <= 15:
                chart_type = "pie"
                img = _generate_pie_chart(series, col)
            else:
                chart_type = "bar"
                img = _generate_bar_chart(series, col)

            charts[col] = {"type": chart_type, "image_base64": img}

        except Exception as exc:
            logger.error("Chart generation failed for column '%s': %s", col, exc)
            charts[col] = {"type": "error", "image_base64": "", "error": str(exc)}

    return charts


# ---------------------------------------------------------------------------
# Chart Generators
# ---------------------------------------------------------------------------

def _generate_histogram(series: pd.Series, col_name: str) -> str:
    """Generate a histogram for numeric columns."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _apply_style(fig, ax)

    n_bins = min(20, max(5, series.nunique()))
    ax.hist(
        series, bins=n_bins, color=GOOGLE_BLUE, edgecolor="white",
        linewidth=0.8, alpha=0.85, rwidth=0.92,
    )

    ax.set_title(f"Distribution of {col_name}", fontsize=TITLE_SIZE, fontweight="600", pad=16)
    ax.set_xlabel(col_name, fontsize=LABEL_SIZE, labelpad=10)
    ax.set_ylabel("Frequency", fontsize=LABEL_SIZE, labelpad=10)

    # Subtle gridlines
    ax.yaxis.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)

    # Nice tick formatting
    ax.tick_params(labelsize=TICK_SIZE)
    if series.max() > 10000:
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    return _fig_to_base64(fig)


def _generate_pie_chart(series: pd.Series, col_name: str) -> str:
    """Generate a pie chart for low-cardinality categorical columns."""
    fig, ax = plt.subplots(figsize=(7, 5))

    counts = series.value_counts()
    labels = [str(l) for l in counts.index]
    sizes = counts.values
    colors = PALETTE[: len(labels)]

    # Explode the largest slice slightly
    explode = [0.03] * len(labels)
    if len(explode) > 0:
        explode[0] = 0.06

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct="%1.1f%%",
        colors=colors,
        explode=explode,
        startangle=90,
        pctdistance=0.78,
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
    )

    for text in autotexts:
        text.set_fontsize(TICK_SIZE)
        text.set_fontweight("600")
        text.set_color("white")

    ax.set_title(f"Distribution of {col_name}", fontsize=TITLE_SIZE, fontweight="600", pad=16)

    # Legend outside the pie
    ax.legend(
        wedges, [f"{l} ({s:,})" for l, s in zip(labels, sizes)],
        loc="center left", bbox_to_anchor=(1.0, 0.5),
        fontsize=TICK_SIZE, frameon=False,
    )

    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_base64(fig)


def _generate_bar_chart(series: pd.Series, col_name: str) -> str:
    """Generate a horizontal bar chart for high-cardinality categoricals (top 10)."""
    fig, ax = plt.subplots(figsize=(7, 5))
    _apply_style(fig, ax)

    counts = series.value_counts().head(10)
    labels = [str(l)[:25] for l in counts.index]  # Truncate long labels
    values = counts.values

    # Horizontal bars
    y_pos = np.arange(len(labels))
    bars = ax.barh(
        y_pos, values, color=GOOGLE_BLUE, edgecolor="white",
        linewidth=0.5, height=0.65, alpha=0.85,
    )

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=TICK_SIZE, color=GOOGLE_GREY,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=TICK_SIZE)
    ax.invert_yaxis()  # Top-to-bottom

    ax.set_title(f"Top 10 Values — {col_name}", fontsize=TITLE_SIZE, fontweight="600", pad=16)
    ax.set_xlabel("Count", fontsize=LABEL_SIZE, labelpad=10)

    ax.xaxis.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)

    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_style(fig, ax):
    """Apply consistent Google-inspired styling."""
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E0E0E0")
    ax.spines["bottom"].set_color("#E0E0E0")
    ax.tick_params(colors=GOOGLE_GREY, labelsize=TICK_SIZE)
    fig.tight_layout(pad=2.0)


def _fig_to_base64(fig) -> str:
    """Render a matplotlib figure to a base64-encoded PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
