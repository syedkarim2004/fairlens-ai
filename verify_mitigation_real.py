import requests
import json
import time

BASE_URL = "http://localhost:8081/api"

def test_mitigation_flow():
    print("🚀 Starting Mitigation Flow Test...")
    
    # 1. Generate Data
    print("\n[1/3] Generating deterministic test data...")
    res = requests.post(f"{BASE_URL}/generate-test-data")
    if res.status_code != 200:
        print(f"❌ Failed to generate data: {res.text}")
        return
    file_id = res.json()["file_id"]
    print(f"✅ Data generated. File ID: {file_id}")

    # 2. Run Initial Audit
    print("\n[2/3] Running initial audit...")
    audit_res = requests.post(f"{BASE_URL}/audit/run", json={
        "file_id": file_id,
        "target_column": "decision",
        "sensitive_columns": ["gender"],
        "positive_label": "approved"
    })
    if audit_res.status_code != 200:
        print(f"❌ Audit failed: {audit_res.text}")
        return
    baseline = audit_res.json()
    print(f"✅ Audit complete. Score: {baseline['summary']['score']}")
    print(f"📊 Before - Gender DIR: {baseline['attributes'][0]['dir']}")

    # 3. Apply Mitigation (Reweighing)
    print("\n[3/3] Applying mitigation (Reweigh Training Data)...")
    mit_res = requests.post(f"{BASE_URL}/audit/mitigate", json={
        "file_id": file_id,
        "method": "anonymize",
        "target_column": "decision",
        "sensitive_attribute": "gender"
    })
    
    if mit_res.status_code == 200:
        result = mit_res.json()
        print(f"✅ Mitigation successful!")
        print(f"📈 Improvement: {result['improvement']}")
        print(f"📊 Before DIR: {result['before']['DIR']:.4f}")
        print(f"📊 After DIR:  {result['after']['DIR']:.4f}")
        print(f"💾 Mitigated File ID: {result['mitigated_file_id']}")
    else:
        print(f"❌ Mitigation failed: {mit_res.text}")

if __name__ == "__main__":
    test_mitigation_flow()
