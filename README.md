# FairLens AI



A full-stack platform for detecting and remediating algorithmic bias. Upload a CSV, scan a HuggingFace dataset, or connect a GitHub repo — FairLens auto-detects protected attributes, runs statistical fairness audits, and delivers actionable, plain-English explanations with confidence scores.

**Stack:** FastAPI · React/Vite · Firebase Auth · Google Cloud Run

---

## Features

| Feature | Details |
|---|---|
| 📤 **Multi-Source Upload** | CSV upload, HuggingFace datasets (streamed), Kaggle, GitHub repos |
| 🔍 **Zero-Click Audit** | Auto-detects target column, sensitive attributes, and positive class |
| ⚖️ **Fairness Metrics** | Disparate Impact Ratio, Statistical Parity Difference, SHAP attribution, proxy detection |
| 🚦 **Domain-Aware Risk** | HIGH / MEDIUM / LOW per attribute with domain-specific thresholds (hiring, credit, healthcare, etc.) |
| 🛡️ **Bias Remediation** | Reweighing, disparate impact remover, and other mitigation strategies |
| 📊 **Confidence Scoring** | Sample-size-aware confidence level (HIGH / MEDIUM / LOW) on every audit |
| 📝 **Human-Readable Explanations** | Plain-English bias explanations per attribute |
| 🤖 **Deep Insights** | Deterministic, metrics-driven analysis (Gemma-style) |
| 📄 **PDF Reports** | Auto-generated audit reports with charts |
| 🧪 **Hardened Pipeline** | Zero-division guards, text-only fallback, auto-sampling for large datasets |
| ☁️ **Cloud Run Ready** | Docker container on port 8080 |

---

## Project Structure

```
fairlens-ai/
├── app/
│   ├── main.py                       # FastAPI app, CORS, router registration
│   ├── routes/
│   │   ├── audit.py                  # /api/audit/run, /api/audit/mitigate
│   │   ├── auth.py                   # Firebase / demo auth
│   │   ├── dashboard.py              # Dashboard stats & audit history
│   │   ├── external_sources.py       # Kaggle, real-world data sources
│   │   ├── history.py                # Audit history CRUD
│   │   ├── huggingface_scanner.py    # /api/scan/huggingface, /api/scan/huggingface/audit
│   │   ├── preview.py                # File preview endpoints
│   │   ├── report.py                 # PDF report generation
│   │   ├── upload.py                 # CSV upload, HF upload, file store
│   │   └── visualize.py              # Chart generation endpoints
│   ├── services/
│   │   ├── fairness_engine.py        # DIR, SPD, SHAP, proxy detection, full audit
│   │   ├── autonomous_config.py      # Auto-detect target, sensitive attrs, positive class
│   │   ├── debiasing.py              # Mitigation strategies (reweighing, etc.)
│   │   ├── huggingface_hub.py        # HF Hub API, streaming dataset loader
│   │   ├── chart_generator.py        # Matplotlib/Plotly chart generation
│   │   ├── pdf_generator.py          # PDF report builder
│   │   ├── gemini_service.py         # Gemini API integration
│   │   └── industry_templates.py     # Domain-specific audit templates
│   ├── state/
│   │   └── audit_history.py          # In-memory audit record store
│   └── utils/
│       ├── validator.py              # Column validation, deterministic normalization
│       └── reproducibility.py        # Seed management for reproducibility
├── frontend/
│   ├── src/
│   │   ├── pages/                    # Audit, Results, Dashboard, Upload, etc.
│   │   ├── components/               # BiasScoreCard, DebiasingPanel, ShapChart, etc.
│   │   └── services/api.js           # Axios API client
│   └── vite.config.js
├── tests/
│   ├── test_intelligence.py          # 46 unit tests (HF, GitHub, insights, audit)
│   ├── test_harden_pipeline.py       # Pipeline hardening tests
│   └── test_api.py                   # Integration tests (requires running server)
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Quick Start

### Backend

```bash
cd fairlens-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

API: **http://localhost:8080** · Docs: **http://localhost:8080/docs**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: **http://localhost:5175**

---

## API Reference

### Upload & Preview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload a CSV dataset |
| `POST` | `/api/upload/huggingface` | Upload from HuggingFace |
| `POST` | `/api/upload/kaggle` | Upload from Kaggle |
| `GET` | `/api/files/{file_id}/columns` | Column names and row preview |
| `GET` | `/api/files/{file_id}/preview` | Tabular preview |

### Audit & Remediation

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/audit/run` | Run a fully autonomous fairness audit |
| `POST` | `/api/audit/mitigate` | Apply a mitigation strategy and re-audit |
| `POST` | `/api/templates/detect` | Detect industry template for a dataset |
| `GET` | `/api/audit/{file_id}/report` | Retrieve audit report |
| `GET` | `/api/audit/download/{file_id}` | Download mitigated dataset |

### HuggingFace & GitHub Scanning

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/scan/huggingface` | Scan a HuggingFace model or dataset (auto-detect) |
| `POST` | `/api/scan/huggingface/audit` | Full fairness audit on a HuggingFace dataset |
| `POST` | `/api/scan/github` | Scan a GitHub repo for models and datasets |
| `POST` | `/api/scan/github/preview` | Preview a dataset found in a GitHub repo |

### Reports & Visualization

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/report/generate` | Generate PDF report |
| `POST` | `/api/report/v2/generate/{audit_id}` | Generate v2 report by audit ID |
| `POST` | `/api/visualize` | Generate bias visualization charts |

### Dashboard & History

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/dashboard/stats` | Dashboard summary statistics |
| `GET` | `/api/dashboard/audits` | List all audits |
| `GET` | `/api/dashboard/audits/{audit_id}` | Get a specific audit |
| `GET` | `/api/history/audits` | Full audit history |
| `DELETE` | `/api/history/audits/{audit_id}` | Delete an audit record |

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/google` | Google/Firebase sign-in |
| `POST` | `/api/auth/demo` | Demo mode login |
| `GET` | `/api/auth/me` | Current user info |

---

### POST /api/audit/run

Run a fully autonomous fairness audit. If `target_column` or `sensitive_columns` are omitted, they are auto-detected.

**Request:**
```json
{
  "file_id": "a1b2c3d4",
  "target_column": "loan_approved",
  "sensitive_columns": ["gender", "race"],
  "positive_label": 1,
  "domain": "credit"
}
```

**Response:**
```json
{
  "summary": {
    "overall_risk": "MEDIUM",
    "overall_grade": "C",
    "score": 62,
    "deep_analysis": { "overview": "..." }
  },
  "attributes": [
    {
      "name": "gender",
      "risk": "MEDIUM",
      "dir": 0.6667,
      "spd": -0.24,
      "baseline_group": "male",
      "minority_group": "female",
      "baseline_rate": 0.72,
      "minority_rate": 0.48,
      "deep_insight": { "...": "..." },
      "interpretation": "..."
    }
  ],
  "confidence": { "level": "HIGH", "value": 1.0, "sample_size": 1000 },
  "explanation": [
    { "attribute": "gender", "risk": "MEDIUM", "text": "The attribute 'gender' shows moderate bias (DIR: 0.67). Monitor this attribute closely." }
  ],
  "metadata": {
    "file_id": "a1b2c3d4",
    "target_column": "loan_approved",
    "rows": 1000,
    "cols": 5,
    "sampled": false
  }
}
```

---

## Fairness Metrics

| Metric | Formula | Fair Threshold |
|--------|---------|----------------|
| **Disparate Impact Ratio (DIR)** | `minority_rate / baseline_rate` | ≥ 0.8 (80% rule) |
| **Statistical Parity Difference (SPD)** | `minority_rate − baseline_rate` | 0 = ideal |

**Domain-Specific Thresholds:**

| Domain | DIR Threshold | SPD Flag | Standard |
|--------|--------------|----------|----------|
| Hiring | 0.80 | 0.15 | EEOC 80% Rule |
| Credit | 0.80 | 0.10 | ECOA / Fair Lending |
| Insurance | 0.85 | 0.10 | Insurance Fairness |
| Healthcare | 0.90 | 0.05 | Health Equity |
| Education | 0.75 | 0.15 | Educational Equity |

**Risk Levels:**
- 🔴 **HIGH** — DIR < 0.6
- 🟡 **MEDIUM** — 0.6 ≤ DIR < 0.8
- 🟢 **LOW** — DIR ≥ 0.8

**Grading Scale:** A (90-100) · B (75-89) · C (60-74) · D (40-59) · F (0-39)

---

## Safety & Hardening

- **Auto-sampling**: Datasets over 2,000 rows are randomly sampled (seed=42) to prevent OOM
- **Zero-division guards**: Both-rates-zero → DIR=1.0 (no disparity); empty groups filtered out
- **Text-only fallback**: Datasets with only unstructured text return a structured warning instead of crashing
- **Streaming HF loader**: 3-strategy approach (direct slice → streaming → alternate splits) avoids downloading multi-GB datasets
- **Thread pool isolation**: All HuggingFace and GitHub endpoints run in `asyncio.run_in_executor()` to prevent server blocking
- **Positive class detection**: Auto-detects 1, "yes", "approved", "hired", etc. to prevent 0% vs 0% outputs

---

## Running Tests

```bash
# Unit tests (no server required)
pytest tests/test_intelligence.py tests/test_harden_pipeline.py -v

# Integration tests (requires running server on :8080)
pytest tests/test_api.py -v
```

---

## Docker / Cloud Run

```bash
# Build and run
docker build -t fairlens-ai .
docker run -p 8080:8080 --env-file .env fairlens-ai

# Deploy to Cloud Run
gcloud builds submit --tag gcr.io/YOUR_PROJECT/fairlens-ai
gcloud run deploy fairlens-ai \
  --image gcr.io/YOUR_PROJECT/fairlens-ai \
  --platform managed --region us-central1 \
  --allow-unauthenticated
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Gemini API key for AI-powered explanations |
| `GITHUB_TOKEN` | Optional | GitHub token for repo scanning (higher rate limits) |
| `HF_TOKEN` | Optional | HuggingFace token for gated datasets/models |

---

## Notes

- **In-memory storage**: Uploaded files and audit history are stored in Python dicts and lost on restart. Production deployments should use Cloud Storage or a database.
- **Port 8080**: Required by Cloud Run — do not change.
- **Deterministic by design**: Same CSV → same JSON output. Seeds are locked, column ordering is sorted, no randomness in the audit pipeline.
