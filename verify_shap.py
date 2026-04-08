import pandas as pd
import numpy as np
from app.services.fairness_engine import calculate_shap_importance, run_full_audit
import json

def test_shap():
    print("\n--- Testing SHAP Attribution ---")
    
    # Create an imbalanced dataset
    data = {
        "gender": ["Male"]*50 + ["Female"]*50,
        "age": np.random.randint(20, 60, 100),
        "experience": np.random.randint(0, 20, 100),
        "hired": [1]*40 + [0]*10 + [0]*40 + [1]*10 # Bias: Men hired, Women not
    }
    df = pd.DataFrame(data)
    
    # 1. Test direct calculate_shap_importance
    shap_results = calculate_shap_importance(df, "hired", ["gender"])
    print(f"SHAP Results: {json.dumps(shap_results, indent=2)}")
    
    assert len(shap_results) > 0
    assert any(res["feature"] == "gender" and res["is_sensitive"] for res in shap_results)
    print("✅ SHAP Attribution Structure Validated")

    # 2. Test full audit integration
    audit_results = run_full_audit(df, "hired", ["gender"])
    print(f"Audit Summary: {audit_results['summary']}")
    
    assert "bias_attribution" in audit_results
    assert len(audit_results["bias_attribution"]) > 0
    print("✅ SHAP Integration in Full Audit Validated")

if __name__ == "__main__":
    try:
        test_shap()
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
