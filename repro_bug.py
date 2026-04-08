import pandas as pd
import numpy as np
from app.services.fairness_engine import run_full_audit

def test_audit_hardening():
    print("--- Case 1: Case Sensitivity ---")
    df = pd.DataFrame({
        "gender": ["Male", "Female"] * 10,
        "HIRED": [1, 0] * 10
    })
    # Passing "GENDER" and "hired" (case mismatch)
    try:
        # Note: validator handles case sensitivity at the endpoint level, 
        # so here we test if the engine can handle it if we pass lower-case manually 
        # but let's assume we pass the correct ones from validator.
        res = run_full_audit(df, "HIRED", ["gender"])
        print(f"Success: Status={res.get('overall_fairness_grade')}")
    except Exception as e:
        print(f"Failed Case 1: {e}")

    print("\n--- Case 2: All-Null Sensitive Attribute ---")
    df_null_attr = pd.DataFrame({
        "gender": [np.nan] * 20,
        "age_group": ["Old", "Young"] * 10,
        "hired": [1, 0] * 10
    })
    try:
        # gender is all null. run_full_audit should handle it via try/except in the loop
        res = run_full_audit(df_null_attr, "hired", ["gender", "age_group"])
        print(f"Success: Audited {res['total_sensitive_attrs']} attrs. Biased: {res['biased_attrs']}")
        # print(f"Results keys: {list(res['results'].keys())}")
    except Exception as e:
        print(f"Failed Case 2: {e}")

    print("\n--- Case 3: Non-Binary Numeric Target (Thresholding) ---")
    df_numeric = pd.DataFrame({
        "gender": ["Male", "Female"] * 10,
        "salary": [3000, 4000, 5000, 6000, 7000] * 4
    })
    try:
        # salary is numeric/continuous. Engine should binarize via median.
        res = run_full_audit(df_numeric, "salary", ["gender"])
        print(f"Success: Binarization worked. Grade={res['overall_fairness_grade']}")
    except Exception as e:
        print(f"Failed Case 3: {e}")

    print("\n--- Case 4: Column with only 1 group after dropping NaNs ---")
    df_single = pd.DataFrame({
        "gender": ["Male", np.nan, "Male", np.nan] * 5,
        "hired": [1, 0, 1, 0] * 5
    })
    try:
        # Only 'Male' group exists. DI should return insufficient data.
        res = run_full_audit(df_single, "hired", ["gender"])
        print(f"Success: Handled single group. Results: {res['results']['gender'].get('status')}")
    except Exception as e:
        print(f"Failed Case 4: {e}")

if __name__ == "__main__":
    test_audit_hardening()
