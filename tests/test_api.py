"""
FairLens AI — API Tests
------------------------
Integration tests using FastAPI's TestClient.
Tests cover root, health, file upload, column retrieval, and audit endpoints.
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: Generate an in-memory CSV for testing
# ---------------------------------------------------------------------------

def make_csv_bytes(rows: int = 20) -> bytes:
    """
    Generate a minimal CSV for testing with:
      - 'gender': alternating 'male' / 'female'
      - 'age': cycling through 3 age groups
      - 'loan_approved': binary 0/1 outcome with slight skew
    """
    lines = ["gender,age,loan_approved"]
    genders = ["male", "female"]
    ages = ["young", "middle", "senior"]
    for i in range(rows):
        gender = genders[i % 2]
        age = ages[i % 3]
        # Males slightly more likely to be approved to create detectable bias
        approved = 1 if (i % 3 != 2) and gender == "male" else (1 if i % 4 == 0 else 0)
        lines.append(f"{gender},{age},{approved}")
    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------------------
# Root & Health Tests
# ---------------------------------------------------------------------------

class TestRootAndHealth:
    def test_root_returns_200(self):
        """GET / should return 200 with the expected message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "FairLens AI is running"

    def test_health_returns_ok(self):
        """GET /health should return status=ok and the correct service name."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "fairlens-backend"


# ---------------------------------------------------------------------------
# Upload Tests
# ---------------------------------------------------------------------------

class TestUpload:
    def test_upload_valid_csv(self):
        """POST /api/upload with a valid CSV should return file_id and metadata."""
        csv_bytes = make_csv_bytes(rows=20)
        response = client.post(
            "/api/upload",
            files={"file": ("test_data.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test_data.csv"
        assert data["rows"] == 20
        assert "gender" in data["columns"]
        assert "loan_approved" in data["columns"]
        assert "message" in data

    def test_upload_non_csv_file_rejected(self):
        """POST /api/upload with a .txt file should return 400."""
        response = client.post(
            "/api/upload",
            files={"file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_too_few_rows_rejected(self):
        """POST /api/upload with fewer than 10 rows should return 400."""
        csv_bytes = make_csv_bytes(rows=5)
        response = client.post(
            "/api/upload",
            files={"file": ("small.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 400

    def test_get_columns_after_upload(self):
        """GET /api/files/{file_id}/columns should return metadata for an uploaded file."""
        # Upload first
        csv_bytes = make_csv_bytes(rows=15)
        upload_response = client.post(
            "/api/upload",
            files={"file": ("cols_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]

        # Then retrieve columns
        col_response = client.get(f"/api/files/{file_id}/columns")
        assert col_response.status_code == 200
        data = col_response.json()
        assert data["file_id"] == file_id
        assert "columns" in data
        assert data["row_count"] == 15
        assert len(data["preview"]) == 3  # First 3 rows

    def test_get_columns_unknown_file_returns_404(self):
        """GET /api/files/{file_id}/columns with a bad file_id should return 404."""
        response = client.get("/api/files/nonexist/columns")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Audit Tests
# ---------------------------------------------------------------------------

class TestAudit:
    def _upload_test_file(self, rows: int = 30) -> str:
        """Upload a test CSV and return the file_id."""
        csv_bytes = make_csv_bytes(rows=rows)
        response = client.post(
            "/api/upload",
            files={"file": ("audit_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        return response.json()["file_id"]

    def test_audit_valid_request(self):
        """POST /api/audit with valid parameters should return a complete audit report."""
        file_id = self._upload_test_file(rows=30)
        response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "loan_approved",
                "sensitive_columns": ["gender"],
                "positive_label": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Top-level fields
        assert data["file_id"] == file_id
        assert data["status"] in ("PASS", "FAIL")
        assert data["total_rows"] == 30
        assert data["target_column"] == "loan_approved"
        assert "bias_results" in data
        assert "gemini_explanation" in data
        assert "summary" in data

        # Per-column metrics
        gender_result = data["bias_results"]["gender"]
        assert "disparate_impact_ratio" in gender_result
        assert "statistical_parity_difference" in gender_result
        assert "risk_level" in gender_result
        assert gender_result["risk_level"] in ("HIGH", "MEDIUM", "LOW")
        assert isinstance(gender_result["is_biased"], bool)
        assert "interpretation" in gender_result

    def test_audit_missing_target_column(self):
        """POST /api/audit with a non-existent target_column should return 400."""
        file_id = self._upload_test_file()
        response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "nonexistent_col",
                "sensitive_columns": ["gender"],
            },
        )
        assert response.status_code == 400

    def test_audit_missing_sensitive_column(self):
        """POST /api/audit with a non-existent sensitive column should return 400."""
        file_id = self._upload_test_file()
        response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "loan_approved",
                "sensitive_columns": ["nonexistent_sensitive"],
            },
        )
        assert response.status_code == 400

    def test_audit_unknown_file_id(self):
        """POST /api/audit with an unknown file_id should return 404."""
        response = client.post(
            "/api/audit",
            json={
                "file_id": "badid99",
                "target_column": "loan_approved",
                "sensitive_columns": ["gender"],
            },
        )
        assert response.status_code == 404

    def test_audit_multiple_sensitive_columns(self):
        """POST /api/audit with multiple sensitive columns should return results for each."""
        file_id = self._upload_test_file(rows=30)
        response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "loan_approved",
                "sensitive_columns": ["gender", "age"],
                "positive_label": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "gender" in data["bias_results"]
        assert "age" in data["bias_results"]

    def test_audit_saves_timestamp(self):
        """POST /api/audit response should include an ISO-8601 timestamp."""
        file_id = self._upload_test_file(rows=30)
        response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "loan_approved",
                "sensitive_columns": ["gender"],
                "positive_label": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO-8601 sanity check


# ---------------------------------------------------------------------------
# Generate Test Data Tests
# ---------------------------------------------------------------------------

class TestGenerateTestData:
    def test_generate_test_data_returns_file_id(self):
        """POST /api/generate-test-data should return a file_id and 500 rows."""
        response = client.post("/api/generate-test-data")
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["rows"] == 500
        assert "gender" in data["columns"]
        assert "hired" in data["columns"]
        assert "bias_note" in data
        assert "message" in data

    def test_generated_data_usable_in_audit(self):
        """File generated by generate-test-data should be immediately auditable."""
        gen_response = client.post("/api/generate-test-data")
        assert gen_response.status_code == 200
        file_id = gen_response.json()["file_id"]

        audit_response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "hired",
                "sensitive_columns": ["gender"],
                "positive_label": 1,
            },
        )
        assert audit_response.status_code == 200
        data = audit_response.json()
        gender_result = data["bias_results"]["gender"]

        # The generated dataset has a ~25-point hire-rate gap between genders.
        # |SPD| > 0.1 is always true regardless of which group the engine
        # designates as baseline (most frequent), making this check seed-independent.
        spd = gender_result["statistical_parity_difference"]
        assert abs(spd) > 0.1, (
            f"Expected |SPD| > 0.1 for a 25-point injected bias, got SPD={spd}"
        )
        # is_biased must be True: DIR will be either < 0.8 or > 1/0.8 = 1.25
        assert gender_result["is_biased"] is True

    def test_generated_data_stored_in_file_store(self):
        """GET /api/files/{file_id}/columns should work for a generated file."""
        gen_response = client.post("/api/generate-test-data")
        file_id = gen_response.json()["file_id"]

        col_response = client.get(f"/api/files/{file_id}/columns")
        assert col_response.status_code == 200
        data = col_response.json()
        assert data["row_count"] == 500


# ---------------------------------------------------------------------------
# Audit Report Tests
# ---------------------------------------------------------------------------

class TestAuditReport:
    def _run_full_flow(self) -> str:
        """Generate test data, run audit, return file_id."""
        gen_response = client.post("/api/generate-test-data")
        assert gen_response.status_code == 200
        file_id = gen_response.json()["file_id"]

        audit_response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "hired",
                "sensitive_columns": ["gender"],
                "positive_label": 1,
            },
        )
        assert audit_response.status_code == 200
        return file_id

    def test_report_returns_full_audit(self):
        """GET /api/audit/{file_id}/report should return the stored audit report."""
        file_id = self._run_full_flow()
        response = client.get(f"/api/audit/{file_id}/report")
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == file_id
        assert "bias_results" in data
        assert "gemini_explanation" in data
        assert "summary" in data
        assert "timestamp" in data
        assert data["status"] in ("PASS", "FAIL")

    def test_report_unknown_file_id_returns_404(self):
        """GET /api/audit/{file_id}/report for an unaudited file_id returns 404."""
        response = client.get("/api/audit/zzzzzzzz/report")
        assert response.status_code == 404

    def test_report_matches_audit_response(self):
        """The report endpoint should return identical data to the audit response."""
        gen_response = client.post("/api/generate-test-data")
        file_id = gen_response.json()["file_id"]

        audit_response = client.post(
            "/api/audit",
            json={
                "file_id": file_id,
                "target_column": "hired",
                "sensitive_columns": ["gender"],
                "positive_label": 1,
            },
        )
        audit_data = audit_response.json()

        report_response = client.get(f"/api/audit/{file_id}/report")
        report_data = report_response.json()

        # Core fields must match
        assert report_data["status"]       == audit_data["status"]
        assert report_data["total_rows"]   == audit_data["total_rows"]
        assert report_data["bias_results"] == audit_data["bias_results"]
        assert report_data["summary"]      == audit_data["summary"]


# ---------------------------------------------------------------------------
# Demo Page Tests
# ---------------------------------------------------------------------------

class TestDemo:
    def test_demo_returns_html(self):
        """GET /demo should return a 200 HTML page."""
        response = client.get("/demo")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_demo_contains_key_elements(self):
        """Demo page should contain expected titles and button labels."""
        response = client.get("/demo")
        body = response.text
        assert "FairLens AI" in body
        assert "Generate Test Dataset" in body
        assert "Run Audit" in body
        assert "View Report" in body
        assert "/api/generate-test-data" in body
