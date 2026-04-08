import requests
import json
import time

BASE_URL = "http://localhost:8080/api"

def test_all():
    print("🚀 Starting Comprehensive Mitigation Audit...")
    
    # 1. Setup Determinism & Generate Data
    gen_resp = requests.post(f"{BASE_URL}/generate-test-data")
    file_id = gen_resp.json()["file_id"]
    print(f"✅ Test data generated: {file_id}")
    
    # 2. RUN INITIAL AUDIT (Required by the backend)
    print("🔍 Running initial base audit...")
    audit_resp = requests.post(f"{BASE_URL}/audit", json={
        "file_id": file_id,
        "target_column": "decision",
        "sensitive_columns": ["gender"],
        "positive_label": 1
    })
    if audit_resp.status_code != 200:
        print(f"❌ Base Audit Failed: {audit_resp.text}")
        return
    print("✅ Base Audit Complete.")

    methods = ["reweigh", "anonymize", "threshold", "retrain"]
    results = {}
    
    for method in methods:
        print(f"\n--- Testing Method: {method} ---")
        payload = {
            "file_id": file_id,
            "sensitive_attribute": "gender",
            "target_column": "decision",
            "method": method
        }
        
        start_time = time.time()
        resp = requests.post(f"{BASE_URL}/audit/mitigate", json=payload)
        duration = time.time() - start_time
        
        if resp.status_code == 200:
            data = resp.json()
            improvement = data["improvement"]
            before_dir = data["before"]["DIR"]
            after_dir = data["after"]["DIR"]
            print(f"✅ Success ({duration:.1f}s)")
            print(f"📊 Before DIR: {before_dir:.4f}")
            print(f"📊 After DIR:  {after_dir:.4f}")
            print(f"📈 Improvement: {improvement}")
            results[method] = data
        else:
            print(f"❌ Failed: {resp.text}")

    print("\n" + "="*40)
    print("FINAL SUMMARY")
    print("="*40)
    for m, d in results.items():
        print(f"{m.upper():12} | Before: {d['before']['DIR']:.3f} | After: {d['after']['DIR']:.3f} | {d['improvement']}")

if __name__ == "__main__":
    test_all()
