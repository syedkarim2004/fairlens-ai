import requests
import json
import time

BASE_URL = "http://localhost:8080"

def get_audit(file_id):
    url = f"{BASE_URL}/api/audit/run"
    payload = {"file_id": file_id}
    response = requests.post(url, json=payload)
    return response.json()

def test_determinism():
    print("Testing Determinism for FairLens AI...")
    
    # 1. Generate test data
    gen_resp = requests.post(f"{BASE_URL}/api/generate-test-data")
    file_id = gen_resp.json()["file_id"]
    print(f"Generated File ID: {file_id}")
    
    # 2. Run Audit 3 times
    results = []
    for i in range(3):
        print(f"Run {i+1}...")
        res = get_audit(file_id)
        # Remove timestamp as it will naturally change
        if "summary" in res and "timestamp" in res["summary"]:
            del res["summary"]["timestamp"]
        results.append(res)
        time.sleep(1)
        
    # 3. Compare Results
    match_1_2 = results[0] == results[1]
    match_2_3 = results[1] == results[2]
    
    if match_1_2 and match_2_3:
        print("\n✅ SUCCESS: All 3 runs are IDENTICAL!")
        print(json.dumps(results[0], indent=2))
    else:
        print("\n❌ FAILURE: Randomness detected!")
        if not match_1_2:
            print("Run 1 vs Run 2 differ.")
        if not match_2_3:
            print("Run 2 vs Run 3 differ.")

if __name__ == "__main__":
    try:
        test_determinism()
    except Exception as e:
        print(f"Connection Error: {e}. Is the backend running on port 8000?")
