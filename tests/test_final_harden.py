import pandas as pd
import requests
import json
import time

BASE_URL = "http://localhost:8080/api"

def test_final_harden():
    print("🚀 Starting Final Hardening Verification...")

    # 1. Test Tiny Dataset (3 rows)
    print("\n--- TEST: Tiny Dataset (3 rows) ---")
    data_3 = {
        "outcome": [1, 0, 1],
        "gender": ["m", "f", "m"],
        "age": [20, 30, 40]
    }
    df_3 = pd.DataFrame(data_3)
    csv_3 = "/tmp/tiny_3row.csv"
    df_3.to_csv(csv_3, index=False)
    
    files = {'file': open(csv_3, 'rb')}
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    file_id_3 = resp.json()['file_id']
    
    audit_req_3 = {
        "file_id": file_id_3,
        "target_column": "outcome",
        "sensitive_columns": ["gender"]
    }
    resp = requests.post(f"{BASE_URL}/audit/run", json=audit_req_3)
    res_3 = resp.json()
    if res_3.get('status') == "success":
        print(f"✅ SUCCESS: 3-row audit completed. Attributes: {[a['name'] for a in res_3['results']['attributes']]}")
    else:
        print(f"❌ FAILURE: 3-row audit failed. {res_3.get('message')}")

    # 2. Test No-Attribute Fallback
    print("\n--- TEST: No-Attribute Fallback (Empty sensitive_columns) ---")
    audit_req_fallback = {
        "file_id": file_id_3,
        "target_column": "outcome",
        "sensitive_columns": [] # Requested empty
    }
    resp = requests.post(f"{BASE_URL}/audit/run", json=audit_req_fallback)
    res_fallback = resp.json()
    if res_fallback.get('status') == "success":
        attrs = [a['name'] for a in res_fallback['results']['attributes']]
        print(f"✅ SUCCESS: Fallback triggered. Analyzed: {attrs}")
    else:
        print(f"❌ FAILURE: Fallback failed. {res_fallback.get('message')}")

    # 3. Test High-Cardinality Target Immunity
    print("\n--- TEST: High-Cardinality Target ---")
    data_hc = {
        "unique_outcome": [i * 0.1 for i in range(100)], # Fully unique
        "sensitive": ["A", "B"] * 50
    }
    df_hc = pd.DataFrame(data_hc)
    csv_hc = "/tmp/hc_target.csv"
    df_hc.to_csv(csv_hc, index=False)
    
    files = {'file': open(csv_hc, 'rb')}
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    file_id_hc = resp.json()['file_id']
    
    audit_req_hc = {
        "file_id": file_id_hc,
        "target_column": "unique_outcome",
        "sensitive_columns": ["sensitive"]
    }
    resp = requests.post(f"{BASE_URL}/audit/run", json=audit_req_hc)
    res_hc = resp.json()
    if res_hc.get('status') == "success":
        print(f"✅ SUCCESS: High-cardinality target accepted. Attributes: {[a['name'] for a in res_hc['results']['attributes']]}")
    else:
        print(f"❌ FAILURE: HC target rejected. {res_hc.get('message')}")

if __name__ == "__main__":
    test_final_harden()
