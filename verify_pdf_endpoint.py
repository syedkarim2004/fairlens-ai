import requests
import json
import os

def test_pdf():
    print("\n--- Testing PDF Report Generation ---")
    
    # Mock Audit Data
    mock_audit = {
        "overall_fairness_grade": "F",
        "overall_risk_score": 85,
        "total_sensitive_attrs": 3,
        "biased_attrs": 2,
        "summary": "CRITICAL BIAS ALERT: Significant bias detected in local hiring patterns. Immediate remediation is required for 'Gender' and 'Zip Code' attributes, which show a Disparate Impact Ratio below 0.4.",
        "results": {
            "gender": {
                "disparate_impact_ratio": 0.35,
                "statistical_parity_difference": -0.45,
                "risk_level": "HIGH",
                "is_biased": True,
                "baseline_group": "Male",
                "minority_group": "Female"
            },
            "race": {
                "disparate_impact_ratio": 0.82,
                "statistical_parity_difference": -0.05,
                "risk_level": "LOW",
                "is_biased": False,
                "baseline_group": "Group A",
                "minority_group": "Group B"
            }
        },
        "bias_attribution": [
            {"feature": "gender", "shap_value": 0.25, "is_sensitive": True, "contribution_pct": 45.0},
            {"feature": "zip_code", "shap_value": 0.15, "is_sensitive": False, "contribution_pct": 25.0},
            {"feature": "experience", "shap_value": 0.10, "is_sensitive": False, "contribution_pct": 20.0}
        ]
    }
    
    payload = {
        "audit_data": mock_audit,
        "dataset_name": "Enterprise_Hiring_v3.csv"
    }

    # Hit the local endpoint
    # Note: Backend should be running on :8080
    url = "http://localhost:8080/api/report/generate"
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            with open("test_audit_report.pdf", "wb") as f:
                f.write(response.content)
            print("✅ PDF Generated successfully: test_audit_report.pdf")
            print(f"File size: {os.path.getsize('test_audit_report.pdf')} bytes")
        else:
            print(f"❌ PDF Generation Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_pdf()
