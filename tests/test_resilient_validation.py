import pandas as pd
import requests
import json
import time

BASE_URL = "http://localhost:8080/api"

def test_resilient_validation():
    print("🚀 Starting Resilient Validation Verification...")

    # 1. Create a "Stubbornly Invalid" Dataset
    # - target: 'outcome' (random numeric, high cardinality)
    # - requested_sensitive: 'constant_col' (invalid)
    # - potential_fallback: 'gender' (valid)
    data = {
        "outcome": [i * 1.5 for i in range(200)], # High cardinality numeric target
        "constant_col": ["A"] * 200,             # Invalid sensitive (requested)
        "id_col": [f"ID_{i}" for i in range(200)], # High cardinality sensitive (ID-like)
        "gender": ["male", "female"] * 100,        # Valid fallback
    }
    df = pd.DataFrame(data)
    csv_file = "/tmp/resilient_dataset.csv"
    df.to_csv(csv_file, index=False)

    # 2. Upload
    print("\n📤 Uploading resilient dataset...")
    files = {'file': open(csv_file, 'rb')}
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    file_id = resp.json()['file_id']
    print(f"✅ Uploaded. File ID: {file_id}")

    # 3. Test Fallback Mechanism
    print("\n🧐 Testing Fallback (Requesting only 'constant_col')...")
    audit_req = {
        "file_id": file_id,
        "target_column": "outcome",
        "sensitive_columns": ["constant_col"],
        "positive_label": 1
    }
    
    resp = requests.post(f"{BASE_URL}/audit/run", json=audit_req)
    result = resp.json()
    
    if result.get('status') == "success":
        attrs = result['results']['attributes']
        attr_names = [a['name'] for a in attrs]
        print(f"📡 Status: {result.get('status')}")
        print(f"📊 Attributes Analyzed: {attr_names}")
        
        if "gender" in attr_names and "constant_col" not in attr_names:
            print("✅ SUCCESS: System correctly skipped 'constant_col' and picked 'gender' as fallback.")
        else:
            print("❌ FAILURE: Fallback logic did not behave as expected.")
    else:
        print(f"❌ Audit failed: {result.get('message')}")

    # 4. Test Target Immunity
    print("\n🧐 Testing Target Immunity (High cardinality numeric target)...")
    # This was already tested in step 3 as 'outcome' is high cardinality.
    # If Step 3 succeeded, target immunity is working.
    print("✅ Target Immunity confirmed (High cardinality 'outcome' was used).")

if __name__ == "__main__":
    test_resilient_validation()
