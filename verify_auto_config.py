import pandas as pd
import json
from app.services.autonomous_config import analyze_dataset

# Load test dataset
df = pd.read_csv("/tmp/test_dataset.csv")

# Run analysis
result = analyze_dataset(df)

# Print result nicely
print(json.dumps(result, indent=2))

# Basic assertions
assert result["target_column"] == "hired"
assert "gender" in result["sensitive_attributes"]
assert "race" in result["sensitive_attributes"]
assert result["positive_value"] == "1"

# Check explanations
exps = result["human_explanations"]
assert "target_explanation" in exps
assert "sensitive_explanations" in exps
assert "positive_outcome_explanation" in exps
assert "overall_summary" in exps

print("\n✅ Autonomous Configuration & Reasoning Verified!")
