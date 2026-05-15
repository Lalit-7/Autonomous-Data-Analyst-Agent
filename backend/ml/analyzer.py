"""
ML auto-detection and execution engine — decides which model to run and executes it.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, r2_score, silhouette_score,
)
import warnings

warnings.filterwarnings("ignore")


def detect_task_type(df: pd.DataFrame, query: str) -> dict:
    """Detect the appropriate ML task based on data characteristics and user query. Returns a dict with task_type and target_column."""
    query_lower = query.lower()
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Keywords for task detection
    classification_keywords = ["predict", "classify", "churn", "fraud", "spam", "default", "diagnosis", "outcome", "label", "class"]
    regression_keywords = ["forecast", "predict price", "estimate", "predict value", "regression", "revenue", "sales", "cost"]
    clustering_keywords = ["cluster", "segment", "group", "pattern", "find patterns", "categorize"]
    anomaly_keywords = ["outlier", "anomaly", "anomalies", "unusual", "weird", "abnormal", "fraud detection"]
    exploration_keywords = ["analyze", "explore", "summary", "overview", "what's interesting", "tell me about", "describe"]

    # Check for anomaly detection
    if any(kw in query_lower for kw in anomaly_keywords):
        return {"task_type": "anomaly_detection", "target_column": None}

    # Check for clustering
    if any(kw in query_lower for kw in clustering_keywords):
        return {"task_type": "clustering", "target_column": None}

    # Try to detect a target column from the query or data
    potential_targets = _find_target_column(df, query_lower, classification_keywords, regression_keywords)

    if potential_targets:
        target_col = potential_targets[0]
        if df[target_col].dtype in ["object", "category"] or df[target_col].nunique() <= 10:
            return {"task_type": "classification", "target_column": target_col}
        else:
            return {"task_type": "regression", "target_column": target_col}

    # Check query keywords for prediction
    if any(kw in query_lower for kw in classification_keywords):
        target = _guess_target_from_data(df)
        if target:
            if df[target].dtype in ["object", "category"] or df[target].nunique() <= 10:
                return {"task_type": "classification", "target_column": target}
            else:
                return {"task_type": "regression", "target_column": target}

    if any(kw in query_lower for kw in regression_keywords):
        target = _guess_target_from_data(df, prefer_numeric=True)
        if target:
            return {"task_type": "regression", "target_column": target}

    # Default: exploration + clustering if enough numeric columns
    if len(numeric_cols) >= 3:
        return {"task_type": "exploration_with_clustering", "target_column": None}

    return {"task_type": "exploration", "target_column": None}


def _find_target_column(df: pd.DataFrame, query: str, class_kws: list, reg_kws: list) -> list:
    """Find column names mentioned in the query. Returns list of matching column names."""
    matches = []
    for col in df.columns:
        col_lower = col.lower().replace("_", " ").replace("-", " ")
        if col_lower in query or col.lower() in query:
            matches.append(col)

    # Also check common target column names
    common_targets = ["target", "label", "class", "outcome", "churn", "fraud", "default", "y", "status", "result"]
    for col in df.columns:
        if col.lower() in common_targets and col not in matches:
            matches.append(col)

    return matches


def _guess_target_from_data(df: pd.DataFrame, prefer_numeric: bool = False) -> str:
    """Guess the most likely target column based on data heuristics. Returns column name or None."""
    # Common target column names
    target_names = ["target", "label", "class", "outcome", "churn", "fraud", "default", "y", "status", "result", "prediction"]
    for col in df.columns:
        if col.lower().strip() in target_names:
            return col

    # Last column is often the target
    if prefer_numeric:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            return numeric_cols[-1]
    else:
        return df.columns[-1]

    return None


def _prepare_features(df: pd.DataFrame, target_col: str = None) -> tuple:
    """Prepare numeric features from the dataframe. Returns (X_scaled, feature_names, scaler)."""
    exclude_cols = [target_col] if target_col else []
    numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c not in exclude_cols]

    if not numeric_cols:
        # Try to encode categorical columns
        temp_df = df.copy()
        for col in df.select_dtypes(include=["object", "category"]).columns:
            if col not in exclude_cols:
                try:
                    le = LabelEncoder()
                    temp_df[col] = le.fit_transform(temp_df[col].astype(str))
                    numeric_cols.append(col)
                except Exception:
                    pass
        df = temp_df

    if not numeric_cols:
        return None, [], None

    X = df[numeric_cols].copy()
    X = X.fillna(X.median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, numeric_cols, scaler


def run_profiling(df: pd.DataFrame) -> dict:
    """Run comprehensive statistical profiling on the dataframe. Returns a dict of statistics."""
    result = {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "null_summary": {},
        "numeric_stats": {},
        "categorical_stats": {},
        "high_correlations": [],
    }

    # Null analysis
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        if null_count > 0:
            result["null_summary"][col] = {
                "count": null_count,
                "percentage": round(null_count / len(df) * 100, 2),
            }

    # Numeric statistics
    numeric_df = df.select_dtypes(include=["number"])
    if not numeric_df.empty:
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            result["numeric_stats"][col] = {
                "mean": round(float(data.mean()), 3),
                "median": round(float(data.median()), 3),
                "std": round(float(data.std()), 3),
                "min": round(float(data.min()), 3),
                "max": round(float(data.max()), 3),
                "skewness": round(float(data.skew()), 3),
                "kurtosis": round(float(data.kurtosis()), 3),
            }

    # Categorical statistics
    for col in df.select_dtypes(include=["object", "category"]).columns:
        result["categorical_stats"][col] = {
            "unique_values": int(df[col].nunique()),
            "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A",
            "top_frequency": int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0,
        }

    # High correlations
    if numeric_df.shape[1] >= 2:
        corr = numeric_df.corr()
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                val = corr.iloc[i, j]
                if abs(val) > 0.5:
                    result["high_correlations"].append({
                        "col1": corr.columns[i],
                        "col2": corr.columns[j],
                        "correlation": round(float(val), 3),
                    })

    result["high_correlations"].sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return result


def run_clustering(df: pd.DataFrame, n_clusters: int = None) -> dict:
    """Run KMeans clustering on numeric features. Returns dict with labels, metrics, and cluster summaries."""
    X_scaled, feature_cols, scaler = _prepare_features(df)
    if X_scaled is None or len(feature_cols) < 2:
        return {"error": "Not enough numeric features for clustering"}

    # Determine optimal number of clusters using elbow method
    if n_clusters is None:
        max_k = min(8, len(X_scaled) // 5, 10)
        max_k = max(max_k, 2)
        inertias = []
        for k in range(2, max_k + 1):
            try:
                km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
                km.fit(X_scaled)
                inertias.append((k, km.inertia_))
            except Exception:
                break

        if len(inertias) >= 2:
            # Simple elbow detection
            diffs = [inertias[i][1] - inertias[i + 1][1] for i in range(len(inertias) - 1)]
            ratios = [diffs[i] / max(diffs[i + 1], 1e-10) for i in range(len(diffs) - 1)]
            if ratios:
                best_idx = ratios.index(max(ratios)) + 1
                n_clusters = inertias[best_idx][0]
            else:
                n_clusters = 3
        else:
            n_clusters = 3

    # Run final KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(X_scaled)
    sil_score = float(silhouette_score(X_scaled, labels)) if n_clusters > 1 else 0

    # Cluster summaries
    cluster_summaries = {}
    df_temp = df.copy()
    df_temp["_cluster"] = labels
    for cluster_id in range(n_clusters):
        cluster_data = df_temp[df_temp["_cluster"] == cluster_id]
        summary = {"size": int(len(cluster_data))}
        for col in feature_cols[:5]:
            if col in cluster_data.columns:
                summary[f"{col}_mean"] = round(float(cluster_data[col].mean()), 3)
        cluster_summaries[f"Cluster {cluster_id}"] = summary

    return {
        "task_type": "clustering",
        "algorithm": "KMeans",
        "n_clusters": n_clusters,
        "silhouette_score": round(sil_score, 4),
        "labels": labels.tolist(),
        "feature_columns": feature_cols,
        "cluster_summaries": cluster_summaries,
    }


def run_classification(df: pd.DataFrame, target_col: str) -> dict:
    """Run XGBoost/GradientBoosting classification. Returns dict with metrics and feature importances."""
    if target_col not in df.columns:
        return {"error": f"Target column '{target_col}' not found"}

    df_clean = df.dropna(subset=[target_col]).copy()
    if len(df_clean) < 20:
        return {"error": "Not enough data for classification (need at least 20 rows)"}

    # Encode target
    le = LabelEncoder()
    y = le.fit_transform(df_clean[target_col].astype(str))
    class_names = le.classes_.tolist()

    # Prepare features
    X_scaled, feature_cols, scaler = _prepare_features(df_clean, target_col)
    if X_scaled is None or len(feature_cols) < 1:
        return {"error": "No usable features for classification"}

    # Split data
    test_size = min(0.2, max(0.1, 10 / len(df_clean)))
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None)

    # Train model
    model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42, learning_rate=0.1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    avg_mode = "binary" if len(class_names) == 2 else "weighted"
    prec = precision_score(y_test, y_pred, average=avg_mode, zero_division=0)
    rec = recall_score(y_test, y_pred, average=avg_mode, zero_division=0)
    f1 = f1_score(y_test, y_pred, average=avg_mode, zero_division=0)

    # Feature importances
    importances = dict(zip(feature_cols, model.feature_importances_.tolist()))

    return {
        "task_type": "classification",
        "algorithm": "GradientBoosting (XGBoost-style)",
        "target_column": target_col,
        "class_names": class_names,
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "feature_importances": importances,
        "feature_columns": feature_cols,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }


def run_regression(df: pd.DataFrame, target_col: str) -> dict:
    """Run GradientBoosting regression. Returns dict with metrics and feature importances."""
    if target_col not in df.columns:
        return {"error": f"Target column '{target_col}' not found"}

    df_clean = df.dropna(subset=[target_col]).copy()
    if len(df_clean) < 20:
        return {"error": "Not enough data for regression (need at least 20 rows)"}

    y = df_clean[target_col].values.astype(float)

    X_scaled, feature_cols, scaler = _prepare_features(df_clean, target_col)
    if X_scaled is None or len(feature_cols) < 1:
        return {"error": "No usable features for regression"}

    test_size = min(0.2, max(0.1, 10 / len(df_clean)))
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, random_state=42)

    model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42, learning_rate=0.1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    importances = dict(zip(feature_cols, model.feature_importances_.tolist()))

    return {
        "task_type": "regression",
        "algorithm": "GradientBoosting (XGBoost-style)",
        "target_column": target_col,
        "rmse": round(float(rmse), 4),
        "r2_score": round(float(r2), 4),
        "mse": round(float(mse), 4),
        "feature_importances": importances,
        "feature_columns": feature_cols,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }


def run_anomaly_detection(df: pd.DataFrame, contamination: float = 0.05) -> dict:
    """Run IsolationForest anomaly detection. Returns dict with anomaly labels and summary."""
    X_scaled, feature_cols, scaler = _prepare_features(df)
    if X_scaled is None or len(feature_cols) < 1:
        return {"error": "No usable features for anomaly detection"}

    contamination = min(contamination, 0.5)
    contamination = max(contamination, 0.01)

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    predictions = model.fit_predict(X_scaled)
    scores = model.decision_function(X_scaled)

    n_anomalies = int((predictions == -1).sum())

    return {
        "task_type": "anomaly_detection",
        "algorithm": "IsolationForest",
        "total_records": int(len(df)),
        "anomalies_found": n_anomalies,
        "anomaly_percentage": round(n_anomalies / max(len(df), 1) * 100, 2),
        "contamination": contamination,
        "predictions": predictions.tolist(),
        "feature_columns": feature_cols,
    }


def auto_analyze(df: pd.DataFrame, query: str) -> dict:
    """Main entry point — auto-detect task type and run appropriate analysis. Returns full analysis results."""
    detection = detect_task_type(df, query)
    task_type = detection["task_type"]
    target_col = detection.get("target_column")

    result = {
        "detection": detection,
        "profiling": {},
        "ml_result": {},
    }

    # Always run profiling
    try:
        result["profiling"] = run_profiling(df)
    except Exception as e:
        result["profiling"] = {"error": str(e)}

    # Run ML based on detected task
    try:
        if task_type == "classification" and target_col:
            result["ml_result"] = run_classification(df, target_col)
        elif task_type == "regression" and target_col:
            result["ml_result"] = run_regression(df, target_col)
        elif task_type == "clustering":
            result["ml_result"] = run_clustering(df)
        elif task_type == "anomaly_detection":
            result["ml_result"] = run_anomaly_detection(df)
        elif task_type == "exploration_with_clustering":
            result["ml_result"] = run_clustering(df)
        else:
            result["ml_result"] = {"task_type": "exploration", "note": "Statistical analysis only — dataset characteristics do not support ML modeling"}
    except Exception as e:
        result["ml_result"] = {"error": str(e), "task_type": task_type}

    return result
