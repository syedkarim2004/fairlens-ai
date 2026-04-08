import pandas as pd
import numpy as np
import sys
import os

# Add the project root to sys.path to allow imports from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.services.fairness_engine import run_full_audit

def test_production_metrics():
    print("🚀 Starting Production Metrics Verification...")
    
    # Create a synthetic dataset with known bias
    # Total: 100 
    # Group A (Baseline): 50 rows, 40 hired (80% rate)
    # Group B (Minority): 50 rows, 10 hired (20% rate)
    data = {
        "gender": ["A"]*50 + ["B"]*50,
        "hired": [1]*40 + [0]*10 + [1]*10 + [0]*40
    }
    df = pd.DataFrame(data)
    
    # Expected Metrics:
    # Max Rate = 0.8, Min Rate = 0.2
    # DIR = 0.2 / 0.8 = 0.25
    # SPD = 0.8 - 0.2 = 0.6
    # Risk Level = HIGH (DIR < 0.5)
    # Overall Score = 0.25
    # Grade = F (Score < 0.6)
    
    print("\n--- Running Audit ---")
    results = run_full_audit(df, target_col="hired", sensitive_cols=["gender"], positive_label=1)
    
    attr_data = results["attributes"]["gender"]
    
    print(f"Calculated DIR: {attr_data['disparate_impact_ratio']}")
    print(f"Calculated SPD: {attr_data['statistical_parity_difference']}")
    print(f"Risk Level: {attr_data['risk_level']}")
    print(f"Overall Score: {results['overall_score']}")
    print(f"Fairness Grade: {results['grade']}")
    
    # Asserts
    assert attr_data['disparate_impact_ratio'] == 0.25, f"Expected 0.25, got {attr_data['disparate_impact_ratio']}"
    assert attr_data['statistical_parity_difference'] == 0.6, f"Expected 0.6, got {attr_data['statistical_parity_difference']}"
    assert attr_data['risk_level'] == "HIGH", f"Expected HIGH risk, got {attr_data['risk_level']}"
    assert results['overall_score'] == 0.25, f"Expected overall score 0.25, got {results['overall_score']}"
    assert results['grade'] == "F", f"Expected grade F, got {results['grade']}"
    
    print("\n✅ Verification COMPLETE: Metrics align with production requirements.")

if __name__ == "__main__":
    try:
        test_production_metrics()
    except Exception as e:
        print(f"❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
