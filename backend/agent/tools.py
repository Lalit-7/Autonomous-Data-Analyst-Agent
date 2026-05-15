"""
Tool definitions — standalone functions wrapping core analysis capabilities.
No LangChain dependency — tools are called directly by the agent orchestrator.
"""

import json
import pandas as pd
import numpy as np

from ml.analyzer import run_profiling, run_clustering, run_classification, run_regression, run_anomaly_detection, detect_task_type
from ml.visualizer import (
    generate_distribution_charts, generate_correlation_heatmap,
    generate_categorical_charts, generate_cluster_plot,
    generate_feature_importance_plot, generate_anomaly_plot,
)


def dataset_profiler(df: pd.DataFrame) -> dict:
    """Profile the dataset: compute statistics, detect nulls, identify data types. Returns profiling dict."""
    try:
        return run_profiling(df)
    except Exception as e:
        return {"error": f"Profiling failed: {str(e)}"}


def correlation_engine(df: pd.DataFrame, method: str = "pearson") -> dict:
    """Calculate correlation matrix and identify top correlated pairs. Returns correlation dict."""
    try:
        numeric_df = df.select_dtypes(include=["number"])
        if numeric_df.shape[1] < 2:
            return {"error": "Need at least 2 numeric columns"}

        corr = numeric_df.corr(method=method)
        high_pairs = []
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                val = corr.iloc[i, j]
                if abs(val) > 0.3:
                    high_pairs.append({
                        "feature_1": corr.columns[i],
                        "feature_2": corr.columns[j],
                        "correlation": round(float(val), 4),
                        "strength": "strong" if abs(val) > 0.7 else "moderate" if abs(val) > 0.5 else "weak",
                    })
        high_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return {"method": method, "num_features": int(numeric_df.shape[1]), "top_correlations": high_pairs[:20]}
    except Exception as e:
        return {"error": f"Correlation failed: {str(e)}"}


def ml_auto_runner(df: pd.DataFrame, query: str = "analyze") -> dict:
    """Auto-detect task type and run appropriate ML model. Returns results dict."""
    try:
        detection = detect_task_type(df, query)
        task_type = detection["task_type"]
        target_col = detection.get("target_column")

        if task_type == "classification" and target_col:
            return run_classification(df, target_col)
        elif task_type == "regression" and target_col:
            return run_regression(df, target_col)
        elif task_type in ["clustering", "exploration_with_clustering"]:
            return run_clustering(df)
        elif task_type == "anomaly_detection":
            return run_anomaly_detection(df)
        else:
            return {"task_type": "exploration", "message": "Statistical analysis only"}
    except Exception as e:
        return {"error": f"ML failed: {str(e)}"}


def code_executor(df: pd.DataFrame, python_code: str) -> dict:
    """Execute custom Python code with access to the dataset. Returns stdout output."""
    try:
        local_ns = {"df": df.copy(), "pd": pd, "np": np}
        import io as _io
        import sys as _sys
        old_stdout = _sys.stdout
        _sys.stdout = buffer = _io.StringIO()
        exec(python_code, {"__builtins__": __builtins__}, local_ns)
        output = buffer.getvalue()
        _sys.stdout = old_stdout
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return {"output": output, "status": "success"}
    except Exception as e:
        return {"error": f"Code execution failed: {str(e)}"}
