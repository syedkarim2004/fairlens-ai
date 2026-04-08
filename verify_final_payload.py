
import requests
import json
import os

BASE_URL = "http://localhost:8000/api"

def verify_full_integration():
    print("--- Verifying Full Dashboard Integration ---")
    
    # 1. Generate Test Data
    print("\n1. Generating synthetic biased dataset...")
    gen_resp = requests.post(f"{BASE_URL}/generate-test-data")
    if gen_resp.status_code != 200:
        print(f"FAILED: Could not generate test data. Is the server running?")
        return
    
    data = gen_resp.json()
    file_id = data['file_id']
    print(f"SUCCESS: Generated file_id: {file_id}")
    
    # 2. Run Autonomous Audit
    print(f"\n2. Running autonomous audit for {file_id}...")
    audit_resp = requests.post(f"{BASE_URL}/audit/run", json={"file_id": file_id})
    
    if audit_resp.status_code != 200:
        print(f"FAILED: Audit endpoint returned {audit_resp.status_code}")
        print(audit_resp.text)
        return
        
    report = audit_resp.json()
    
    # 3. Structural Validation
    required_keys = ['status', 'overall_grade', 'bias_results', 'ai_analysis', 'recommendations']
    missing = [k for k in required_keys if k not in report]
    
    if missing:
        print(f"FAILED: Missing keys in response: {missing}")
    else:
        print("SUCCESS: All required keys present in API response.")
        
    # 4. Content Validation
    if 'ai_analysis' in report:
        ai = report['ai_analysis']
        if 'groq' in ai and 'gemma' in ai:
            print(f"SUCCESS: Dual-engine AI analysis found (Groq & Gemma).")
        else:
            print(f"WARNING: ai_analysis missing 'groq' or 'gemma' subkeys.")
            
    if 'recommendations' in report:
        recs = report['recommendations']
        if isinstance(recs, list) and len(recs) > 0:
            print(f"SUCCESS: Found {len(recs)} structured recommendations.")
            print(f"Example Rec: {recs[0]['title']} ({recs[0]['p']})")
        else:
            print(f"WARNING: Recommendations list is empty or invalid format.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_full_integration()
