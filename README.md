# FairLens AI — Backend

> **Google Solution Challenge 2026** — Bias Detection & Remediation Platform

A production-ready FastAPI backend that enables teams to upload datasets, run algorithmic fairness audits, and receive AI-powered explanations of detected bias — all deployable to Google Cloud Run.

---

## Features

| Feature | Details |
|---|---|
| 📤 **CSV Upload** | Upload datasets and get a `file_id` back |
| 🔍 **Fairness Audit** | Disparate Impact Ratio + Statistical Parity Difference |
| 🚦 **Risk Levels** | HIGH / MEDIUM / LOW classification per protected attribute |
| 🤖 **Gemini Explanation** | Plain-English AI explanation via Gemini 1.5 Flash |
| ☁️ **Cloud Run Ready** | Docker container listening on port 8080 |

---

## Project Structure

```
fairlens-backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── routes/
│   │   ├── upload.py            # POST /api/upload, GET /api/files/{id}/columns
│   │   └── audit.py             # POST /api/audit
│   ├── services/
│   │   ├── fairness_engine.py   # Bias metric calculations
│   │   └── gemini_service.py    # Gemini 1.5 Flash integration
│   └── utils/
│       └── validator.py         # Input validation helpers
├── tests/
│   └── test_api.py              # Integration tests (TestClient)
├── Dockerfile                   # Cloud Run deployment
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start (Local)

### 1. Clone and install dependencies

```bash
cd fairlens-backend
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

### 3. Run the development server

```bash
uvicorn app.main:app --reload --port 8080
```

The API is now running at **http://localhost:8080**

- **Interactive docs**: http://localhost:8080/docs
- **Health check**: http://localhost:8080/health

---

## API Reference

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root check |
| `GET` | `/health` | Health check for Cloud Run |
| `POST` | `/api/upload` | Upload a CSV dataset |
| `GET` | `/api/files/{file_id}/columns` | Get columns and row preview |
| `POST` | `/api/audit` | Run a fairness audit |

---

### POST /api/upload

Upload a CSV file. Must be `.csv` with at least 10 rows.

**Response:**
```json
{
  "file_id": "a1b2c3d4",
  "filename": "loan_data.csv",
  "rows": 1000,
  "columns": ["gender", "race", "age", "loan_approved"],
  "message": "File 'loan_data.csv' uploaded successfully."
}
```

---

### POST /api/audit

Run a fairness audit on an uploaded file.

**Request body:**
```json
{
  "file_id": "a1b2c3d4",
  "target_column": "loan_approved",
  "sensitive_columns": ["gender", "race"],
  "positive_label": 1
}
```

**Response:**
```json
{
  "file_id": "a1b2c3d4",
  "status": "FAIL",
  "total_rows": 1000,
  "target_column": "loan_approved",
  "bias_results": {
    "gender": {
      "baseline_group": "male",
      "minority_group": "female",
      "baseline_positive_rate": 0.72,
      "minority_positive_rate": 0.48,
      "disparate_impact_ratio": 0.6667,
      "statistical_parity_difference": -0.24,
      "risk_level": "MEDIUM",
      "is_biased": true,
      "interpretation": "..."
    }
  },
  "gemini_explanation": "...",
  "summary": "Bias detected in 1 out of 2 sensitive attributes..."
}
```

---

## Fairness Metrics Explained

| Metric | Formula | Threshold |
|--------|---------|-----------|
| **Disparate Impact Ratio** | `minority_rate / baseline_rate` | ≥ 0.8 = fair (80% rule) |
| **Statistical Parity Difference** | `minority_rate − baseline_rate` | = 0 is ideal |

**Risk Levels:**
- 🔴 **HIGH** — DIR < 0.6
- 🟡 **MEDIUM** — 0.6 ≤ DIR < 0.8
- 🟢 **LOW** — DIR ≥ 0.8

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Docker / Cloud Run Deployment

### Build and run locally

```bash
docker build -t fairlens-backend .
docker run -p 8080:8080 --env-file .env fairlens-backend
```

### Deploy to Cloud Run

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/fairlens-backend

# Deploy
gcloud run deploy fairlens-backend \
  --image gcr.io/YOUR_PROJECT_ID/fairlens-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Gemini API key for AI explanations. If not set, fallback message is returned. |

---

## Notes

- **In-memory storage only**: Uploaded files are stored in a Python dict and lost on restart. A production deployment should use Cloud Storage or a database.
- **Gemini fallback**: If `GEMINI_API_KEY` is not set or the API call fails, `"Gemini explanation unavailable."` is returned instead.
- **Port**: Cloud Run requires port `8080`. Do not change this.
