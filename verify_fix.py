import requests
import pandas as pd
import io

BASE_URL = "http://localhost:8080/api"

def verify():
    # 1. Create a dummy CSV
    df = pd.DataFrame({
        "gender": ["male", "female", "male", "female", "male"],
        "hired": [1, 0, 1, 0, 1]
    })
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    # 2. Upload
    print("Uploading test dataset...")
    files = {'file': ('test.csv', csv_buffer, 'text/csv')}
    resp = requests.post(f"{BASE_URL}/upload", files=files)
    file_id = resp.json()['file_id']
    print(f"File ID: {file_id}")
    
    # 3. Audit
    print("Running audit...")
    audit_req = {
        "file_id": file_id,
        "target_column": "hired",
        "sensitive_columns": ["gender"]
    }
    resp = requests.post(f"{BASE_URL}/audit/run", json=audit_req)
    data = resp.json()
    
    # 4. Check keys
    keys = list(data.keys())
    print(f"\nTop-level Keys in Response: {keys}")
    
    essential_keys = ["bias_results", "overall_grade", "risk_score", "gemini_explanation"]
    missing = [k for k in essential_keys if k not in keys]
    
    if not missing:
        print("\n✅ SUCCESS: All essential keys for Results.jsx are present.")
        print(f"Grade: {data['overall_grade']}")
        print(f"Risk Score: {data['risk_score']}")
        print(f"Attributes in bias_results: {list(data['bias_results'].keys())}")
    else:
        print(f"\n❌ FAILURE: Missing keys: {missing}")

if __name__ == "__main__":
    verify()
