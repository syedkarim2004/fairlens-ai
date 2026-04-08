import pandas as pd
import numpy as np
import logging
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def calculate_shap_importance(df: pd.DataFrame, sensitive_cols: List[str], label_col: str) -> List[Dict[str, Any]]:
    """
    Train a lightweight Random Forest and use SHAP to attribute feature contributions.
    Returns: [{"feature": str, "shap_value": float, "is_sensitive": bool, "contribution_pct": float}]
    """
    try:
        if len(df) < 50:
            logger.info(f"Dataset too small ({len(df)} rows). Returning uniform importance.")
            num_features = len(df.columns) - 1
            if num_features <= 0: return []
            
            importance = 1.0 / num_features
            return [{
                "feature": col,
                "shap_value": importance,
                "is_sensitive": col in sensitive_cols,
                "contribution_pct": round(importance * 100, 2)
            } for col in df.columns if col != label_col]

        # Preprocessing: Handle categorical and missing values
        temp_df = df.copy()
        for col in temp_df.columns:
            if pd.api.types.is_numeric_dtype(temp_df[col]):
                # Fill numeric NaNs
                temp_df[col] = temp_df[col].fillna(temp_df[col].median() if not temp_df[col].isna().all() else 0)
            else:
                # Handle non-numeric (encoding + filling)
                temp_df[col] = temp_df[col].fillna("Unknown")
                temp_df[col] = LabelEncoder().fit_transform(temp_df[col].astype(str))

        X = temp_df.drop(columns=[label_col])
        y = temp_df[label_col]

        # Train Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Calculate SHAP values
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # Handling binary/multiclass output formats of SHAP
        if isinstance(shap_values, list):
            # For list of arrays, shap_values[1] is the positive class contribution
            shap_abs = np.abs(shap_values[1]).mean(axis=0)
        elif len(shap_values.shape) == 3:
            # SHAP 0.40+ format [samples, features, classes]
            shap_abs = np.abs(shap_values[:, :, 1]).mean(axis=0)
        else:
            shap_abs = np.abs(shap_values).mean(axis=0)

        total_shap = np.sum(shap_abs) if np.sum(shap_abs) > 0 else 1.0
        
        results = []
        for feat, val in zip(X.columns, shap_abs):
            results.append({
                "feature": feat,
                "shap_value": float(val),
                "is_sensitive": feat in sensitive_cols,
                "contribution_pct": round((val / total_shap) * 100, 2)
            })

        # Sort by importance
        results.sort(key=lambda x: x["shap_value"], reverse=True)
        return results

    except Exception as e:
        logger.error(f"Error in calculate_shap_importance: {str(e)}")
        # Fallback to feature importance if SHAP fails
        try:
            X = df.drop(columns=[label_col])._get_numeric_data()
            if X.empty: return []
            importances = [1.0/len(X.columns)] * len(X.columns)
            return [{
                "feature": col,
                "shap_value": 0.0,
                "is_sensitive": col in sensitive_cols,
                "contribution_pct": 100.0/len(X.columns)
            } for col in X.columns]
        except:
            return []
