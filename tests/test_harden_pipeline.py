import pandas as pd
import requests
import json
import time

BASE_URL = "http://localhost:8080/api"

def test_harden_pipeline():
    print("🚀 Starting Hardened Pipeline Verification...")

    # 1. Create a "Dirty" Dataset
    # - One good column (gender)
    # - One all-null column (null_col)
    # - One constant ID column (user_id)
    # - One single-group column (species)
    data = {
        "user_id": range(1, 11),
        "gender": ["male", "female", "male", "female", "male", "female", "male", "female", "male", "female"],
        "null_col": [None] * 10,
        "species": ["human"] * 10,
        "hired": [1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
    }
    df = pd.DataFrame(data)
    csv_file = "/tmp/dirty_dataset.csv"
    df.to_csv(csv_file, index=False)

    # 2. Upload
    print("\n📤 Uploading dirty dataset...")
    files = {'file': open(csv_file, 'rb')}
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.text}")
        return
    
    file_id = resp.json()['file_id']
    print(f"✅ Uploaded. File ID: {file_id}")

    # 3. Test Audit with Dirty Columns
    print("\n🧐 Testing Audit with multiple sensitive columns (including invalid ones)...")
    audit_req = {
        "file_id": file_id,
        "target_column": "hired",
        "sensitive_columns": ["gender", "null_col", "user_id", "species"],
        "positive_label": 1
    }
    
    resp = requests.post(f"{BASE_URL}/audit/run", json=audit_req)
    if resp.status_code != 200:
        print(f"❌ Audit request failed: {resp.text}")
        return

    result = resp.json()
    print(f"📡 Status: {result.get('status')}")
    print(f"💬 Message: {result.get('message')}")

    if result.get('status') == "success":
        attrs = result['results']['attributes']
        print("\n📊 Per-Attribute Results:")
        for attr in attrs:
            name = attr.get('name')
            status = attr.get('status', 'success')
            msg = attr.get('message', 'N/A')
            print(f"  - {name}: [{status}] {msg if status != 'success' else 'Metrics computed'}")
        
        print(f"\n🏆 Overall Grade: {result['results']['grade']}")
    else:
        print(f"❌ Audit failed as expected: {result.get('message')}")

    # 4. Test missing file
    print("\n👻 Testing audit with non-existent file...")
    resp = requests.post(f"{BASE_URL}/audit/run", json={"file_id": "ghost123"})
    print(f"📡 Result: {resp.json().get('status')} - {resp.json().get('message')}")

if __name__ == "__main__":
    test_harden_pipeline()
