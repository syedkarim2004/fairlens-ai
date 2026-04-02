"""
FairLens AI — Main Application Entry Point
-----------------------------------------
FastAPI application for bias detection and remediation.
Designed for deployment on Google Cloud Run (port 8080).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from app.routes import upload, audit

# Load environment variables from .env file (if present).
# Must be called before any service that reads env vars is imported.
load_dotenv()

# ---------------------------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FairLens AI",
    description=(
        "A bias detection and remediation platform for responsible AI. "
        "Upload datasets, run fairness audits, and get AI-powered explanations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware — allow all origins for Cloud Run / frontend flexibility
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])


# ---------------------------------------------------------------------------
# Root & Health Endpoints
# ---------------------------------------------------------------------------
@app.get("/", summary="Root check")
async def root():
    """Simple root endpoint to confirm the service is online."""
    return {"message": "FairLens AI is running"}


@app.get("/health", summary="Health check")
async def health():
    """Health check endpoint used by Cloud Run and load balancers."""
    return {"status": "ok", "service": "fairlens-backend"}


# ---------------------------------------------------------------------------
# Demo UI
# ---------------------------------------------------------------------------
@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def demo():
    """
    Simple interactive demo page that exercises the three main API flows:
      1. Generate test data  → POST /api/generate-test-data
      2. Run audit           → POST /api/audit
      3. View report         → GET  /api/audit/{file_id}/report
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FairLens AI — Demo</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #f0faf4;
      color: #1a1a1a;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
    }

    header {
      text-align: center;
      margin-bottom: 40px;
    }

    header h1 {
      font-size: 2.4rem;
      font-weight: 800;
      color: #15803d;
      letter-spacing: -0.5px;
    }

    header p {
      margin-top: 8px;
      font-size: 1rem;
      color: #4b7263;
    }

    .badge {
      display: inline-block;
      margin-top: 12px;
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #86efac;
      border-radius: 9999px;
      padding: 4px 14px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.5px;
    }

    .card {
      background: #ffffff;
      border: 1px solid #d1fae5;
      border-radius: 16px;
      padding: 28px 32px;
      width: 100%;
      max-width: 760px;
      box-shadow: 0 4px 24px rgba(21,128,61,0.07);
      margin-bottom: 28px;
    }

    .card h2 {
      font-size: 1.1rem;
      font-weight: 700;
      color: #15803d;
      margin-bottom: 6px;
    }

    .card p.desc {
      font-size: 0.88rem;
      color: #6b7280;
      margin-bottom: 18px;
      line-height: 1.5;
    }

    .row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: flex-end;
    }

    label {
      font-size: 0.82rem;
      font-weight: 600;
      color: #374151;
      display: block;
      margin-bottom: 4px;
    }

    input[type="text"] {
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.9rem;
      width: 200px;
      outline: none;
      transition: border-color 0.2s;
    }

    input[type="text"]:focus {
      border-color: #22c55e;
      box-shadow: 0 0 0 3px rgba(34,197,94,0.15);
    }

    button {
      background: #16a34a;
      color: #ffffff;
      border: none;
      border-radius: 8px;
      padding: 9px 22px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.18s, transform 0.1s;
      white-space: nowrap;
    }

    button:hover  { background: #15803d; }
    button:active { transform: scale(0.97); }
    button:disabled { background: #86efac; cursor: not-allowed; }

    .status {
      margin-top: 14px;
      font-size: 0.82rem;
      font-weight: 600;
      min-height: 18px;
    }

    .status.ok  { color: #16a34a; }
    .status.err { color: #dc2626; }

    pre {
      background: #f8fff9;
      border: 1px solid #bbf7d0;
      border-radius: 10px;
      padding: 16px;
      font-size: 0.78rem;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-all;
      max-height: 380px;
      overflow-y: auto;
      margin-top: 14px;
      color: #1a1a1a;
      display: none;
    }

    footer {
      margin-top: 40px;
      font-size: 0.78rem;
      color: #9ca3af;
      text-align: center;
    }

    footer a { color: #16a34a; text-decoration: none; }
    footer a:hover { text-decoration: underline; }
  </style>
</head>
<body>

<header>
  <h1>⚖️ FairLens AI</h1>
  <p>Bias Detection &amp; Remediation — Interactive Demo</p>
  <span class="badge">Google Solution Challenge 2026</span>
</header>

<!-- Step 1: Generate Test Data -->
<div class="card">
  <h2>Step 1 — Generate Test Data</h2>
  <p class="desc">
    Creates a synthetic 500-row hiring dataset with intentional gender bias injected
    (men hired at ~60%, women at ~35%). Stores it in memory and returns a <code>file_id</code>.
  </p>
  <button id="btn-generate" onclick="generateData()">Generate Test Dataset</button>
  <div class="status" id="status-generate"></div>
  <pre id="pre-generate"></pre>
</div>

<!-- Step 2: Run Audit -->
<div class="card">
  <h2>Step 2 — Run Fairness Audit</h2>
  <p class="desc">
    Runs the full bias audit (Disparate Impact Ratio + Statistical Parity Difference)
    on the generated dataset, then calls Gemini for an AI-powered explanation.
  </p>
  <div class="row">
    <div>
      <label for="audit-file-id">file_id</label>
      <input type="text" id="audit-file-id" placeholder="paste file_id here" />
    </div>
    <button id="btn-audit" onclick="runAudit()">Run Audit</button>
  </div>
  <div class="status" id="status-audit"></div>
  <pre id="pre-audit"></pre>
</div>

<!-- Step 3: View Report -->
<div class="card">
  <h2>Step 3 — View Audit Report</h2>
  <p class="desc">
    Retrieves the stored audit report for a given <code>file_id</code> without
    re-running the audit.
  </p>
  <div class="row">
    <div>
      <label for="report-file-id">file_id</label>
      <input type="text" id="report-file-id" placeholder="paste file_id here" />
    </div>
    <button id="btn-report" onclick="viewReport()">View Report</button>
  </div>
  <div class="status" id="status-report"></div>
  <pre id="pre-report"></pre>
</div>

<footer>
  <a href="/docs" target="_blank">Swagger UI</a> &nbsp;·&nbsp;
  <a href="/redoc" target="_blank">ReDoc</a> &nbsp;·&nbsp;
  <a href="/health" target="_blank">Health</a>
</footer>

<script>
  // Shared helper: show result in a <pre> block
  function showResult(preId, statusId, data, ok) {
    const pre    = document.getElementById(preId);
    const status = document.getElementById(statusId);
    pre.style.display = 'block';
    pre.textContent   = JSON.stringify(data, null, 2);
    status.className  = 'status ' + (ok ? 'ok' : 'err');
    status.textContent = ok ? '✓ Success' : '✗ Error';
  }

  function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    btn.disabled    = loading;
    btn.textContent = loading ? 'Loading…' : btn.dataset.label || btn.textContent;
    if (!loading && !btn.dataset.label) btn.dataset.label = btn.textContent;
  }

  // ── Step 1: Generate Test Data ──────────────────────────────────────────
  async function generateData() {
    setLoading('btn-generate', true);
    try {
      const res  = await fetch('/api/generate-test-data', { method: 'POST' });
      const data = await res.json();
      showResult('pre-generate', 'status-generate', data, res.ok);

      // Auto-fill Step 2 & 3 file_id fields
      if (res.ok && data.file_id) {
        document.getElementById('audit-file-id').value  = data.file_id;
        document.getElementById('report-file-id').value = data.file_id;
      }
    } catch (e) {
      showResult('pre-generate', 'status-generate', { error: e.message }, false);
    } finally {
      document.getElementById('btn-generate').disabled    = false;
      document.getElementById('btn-generate').textContent = 'Generate Test Dataset';
    }
  }

  // ── Step 2: Run Audit ───────────────────────────────────────────────────
  async function runAudit() {
    const fileId = document.getElementById('audit-file-id').value.trim();
    if (!fileId) { alert('Please enter a file_id first.'); return; }

    setLoading('btn-audit', true);
    try {
      const res  = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_id: fileId,
          target_column: 'hired',
          sensitive_columns: ['gender'],
          positive_label: 1,
        }),
      });
      const data = await res.json();
      showResult('pre-audit', 'status-audit', data, res.ok);

      // Auto-fill Step 3 report file_id
      if (res.ok && data.file_id) {
        document.getElementById('report-file-id').value = data.file_id;
      }
    } catch (e) {
      showResult('pre-audit', 'status-audit', { error: e.message }, false);
    } finally {
      document.getElementById('btn-audit').disabled    = false;
      document.getElementById('btn-audit').textContent = 'Run Audit';
    }
  }

  // ── Step 3: View Report ─────────────────────────────────────────────────
  async function viewReport() {
    const fileId = document.getElementById('report-file-id').value.trim();
    if (!fileId) { alert('Please enter a file_id first.'); return; }

    setLoading('btn-report', true);
    try {
      const res  = await fetch(`/api/audit/${fileId}/report`);
      const data = await res.json();
      showResult('pre-report', 'status-report', data, res.ok);
    } catch (e) {
      showResult('pre-report', 'status-report', { error: e.message }, false);
    } finally {
      document.getElementById('btn-report').disabled    = false;
      document.getElementById('btn-report').textContent = 'View Report';
    }
  }
</script>
</body>
</html>"""
    return HTMLResponse(content=html)