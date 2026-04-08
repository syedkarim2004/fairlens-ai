import requests
import json

BASE_URL = "http://localhost:8000"

def verify_pdf_report():
    # 1. Get Demo Token
    print("Getting demo token...")
    auth_res = requests.post(f"{BASE_URL}/api/auth/demo")
    if auth_res.status_code != 200:
        print(f"Auth failed: {auth_res.text}")
        return
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Generate Test Data to get a file_id
    print("Generating test data...")
    gen_res = requests.post(f"{BASE_URL}/api/generate-test-data")
    file_id = gen_res.json()["file_id"]
    print(f"File ID: {file_id}")

    # 3. Run Audit to populate audit_store
    print("Running audit...")
    audit_res = requests.post(
        f"{BASE_URL}/api/audit",
        headers=headers,
        json={
            "file_id": file_id,
            "target_column": "decision",
            "sensitive_columns": ["gender"],
            "positive_label": "approved"
        }
    )
    if audit_res.status_code != 200:
        print(f"Audit failed: {audit_res.text}")
        return
    print("Audit successful.")

    # 4. Generate PDF Report
    print(f"Generating PDF for {file_id}...")
    report_res = requests.post(
        f"{BASE_URL}/api/report/v2/generate/{file_id}",
        headers=headers
    )
    
    if report_res.status_code == 200:
        print("PDF generation successful!")
        print(f"Content-Type: {report_res.headers.get('Content-Type')}")
        print(f"Content-Disposition: {report_res.headers.get('Content-Disposition')}")
        
        # Save to file for manual check if needed
        with open("test_report.pdf", "wb") as f:
            f.write(report_res.content)
        print("Report saved as test_report.pdf")
    else:
        print(f"PDF generation failed: {report_res.status_code}")
        print(report_res.text)

if __name__ == "__main__":
    verify_pdf_report()
