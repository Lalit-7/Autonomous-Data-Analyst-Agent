"""
Visualization engine — generates charts as base64 PNG images for embedding in the UI and PDF reports.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
import warnings

warnings.filterwarnings("ignore")

# Consistent style
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#FAFAFA",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": "#333333",
    "text.color": "#333333",
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    "grid.color": "#EEEEEE",
    "font.family": "sans-serif",
    "font.size": 10,
})

TEAL = "#0D9488"
GREEN = "#057A55"
PALETTE = ["#0D9488", "#057A55", "#F59E0B", "#EF4444", "#6366F1", "#EC4899", "#8B5CF6", "#14B8A6"]


def _fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string. Returns the base64 string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def generate_distribution_charts(df: pd.DataFrame, max_cols: int = 6) -> list:
    """Generate histogram/distribution charts for numeric columns. Returns list of {title, base64} dicts."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()[:max_cols]
    if not numeric_cols:
        return []

    n = len(numeric_cols)
    cols_per_row = min(3, n)
    rows = (n + cols_per_row - 1) // cols_per_row
    fig, axes = plt.subplots(rows, cols_per_row, figsize=(5 * cols_per_row, 4 * rows))
    if n == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, col in enumerate(numeric_cols):
        try:
            data = df[col].dropna()
            axes[i].hist(data, bins=30, color=TEAL, alpha=0.7, edgecolor="white")
            axes[i].set_title(col, fontsize=11, fontweight="bold")
            axes[i].set_xlabel("")
            axes[i].axvline(data.mean(), color=GREEN, linestyle="--", linewidth=1.5, label=f"Mean: {data.mean():.2f}")
            axes[i].legend(fontsize=8)
        except Exception:
            axes[i].set_visible(False)

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("DISTRIBUTION ANALYSIS", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    return [{"title": "Distribution Analysis", "base64": _fig_to_base64(fig)}]


def generate_correlation_heatmap(df: pd.DataFrame) -> list:
    """Generate a correlation heatmap for numeric columns. Returns list of {title, base64} dicts."""
    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.shape[1] < 2:
        return []

    # Limit to top 15 columns for readability
    if numeric_df.shape[1] > 15:
        numeric_df = numeric_df.iloc[:, :15]

    corr = numeric_df.corr()
    fig, ax = plt.subplots(figsize=(max(8, numeric_df.shape[1] * 0.8), max(6, numeric_df.shape[1] * 0.6)))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn",
        center=0, square=True, linewidths=0.5, ax=ax,
        cbar_kws={"shrink": 0.8},
        annot_kws={"size": 8},
    )
    ax.set_title("CORRELATION MATRIX", fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    return [{"title": "Correlation Matrix", "base64": _fig_to_base64(fig)}]


def generate_categorical_charts(df: pd.DataFrame, max_cols: int = 4) -> list:
    """Generate bar charts for top categorical columns. Returns list of {title, base64} dicts."""
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    # Pick columns with reasonable cardinality
    cat_cols = [c for c in cat_cols if 1 < df[c].nunique() <= 20][:max_cols]
    if not cat_cols:
        return []

    charts = []
    for col in cat_cols:
        fig, ax = plt.subplots(figsize=(8, 4))
        vc = df[col].value_counts().head(10)
        bars = ax.barh(vc.index.astype(str), vc.values, color=PALETTE[:len(vc)], edgecolor="white")
        ax.set_title(f"{col.upper()} — VALUE COUNTS", fontsize=12, fontweight="bold")
        ax.invert_yaxis()
        for bar, val in zip(bars, vc.values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=9)
        fig.tight_layout()
        charts.append({"title": f"{col} Distribution", "base64": _fig_to_base64(fig)})

    return charts


def generate_scatter_plot(df: pd.DataFrame, x: str, y: str, hue: str = None) -> list:
    """Generate a scatter plot for two numeric columns. Returns list of {title, base64} dicts."""
    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        if hue and hue in df.columns:
            for i, (name, group) in enumerate(df.groupby(hue)):
                color = PALETTE[i % len(PALETTE)]
                ax.scatter(group[x], group[y], c=color, alpha=0.6, s=30, label=str(name), edgecolors="white", linewidth=0.5)
            ax.legend(title=hue, fontsize=8, title_fontsize=9)
        else:
            ax.scatter(df[x], df[y], c=TEAL, alpha=0.6, s=30, edgecolors="white", linewidth=0.5)
        ax.set_xlabel(x, fontsize=10)
        ax.set_ylabel(y, fontsize=10)
        ax.set_title(f"{x.upper()} vs {y.upper()}", fontsize=12, fontweight="bold")
        fig.tight_layout()
        return [{"title": f"{x} vs {y}", "base64": _fig_to_base64(fig)}]
    except Exception:
        return []


def generate_cluster_plot(df: pd.DataFrame, labels: np.ndarray, feature_cols: list) -> list:
    """Generate scatter plots of clusters using top 2 features. Returns list of {title, base64} dicts."""
    if len(feature_cols) < 2:
        return []

    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        x_col, y_col = feature_cols[0], feature_cols[1]
        scatter = ax.scatter(
            df[x_col], df[y_col], c=labels, cmap="Set2",
            alpha=0.7, s=40, edgecolors="white", linewidth=0.5,
        )
        ax.set_xlabel(x_col, fontsize=10)
        ax.set_ylabel(y_col, fontsize=10)
        ax.set_title("CLUSTER VISUALIZATION", fontsize=12, fontweight="bold")
        plt.colorbar(scatter, ax=ax, label="Cluster")
        fig.tight_layout()
        return [{"title": "Cluster Visualization", "base64": _fig_to_base64(fig)}]
    except Exception:
        return []


def generate_feature_importance_plot(importances: dict) -> list:
    """Generate a horizontal bar chart of feature importances. Returns list of {title, base64} dicts."""
    if not importances:
        return []

    try:
        sorted_imp = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)[:15]
        features = [x[0] for x in sorted_imp]
        values = [x[1] for x in sorted_imp]

        fig, ax = plt.subplots(figsize=(8, max(4, len(features) * 0.4)))
        colors = [TEAL if v >= 0 else "#EF4444" for v in values]
        ax.barh(features, values, color=colors, edgecolor="white")
        ax.invert_yaxis()
        ax.set_title("FEATURE IMPORTANCE", fontsize=12, fontweight="bold")
        ax.set_xlabel("Importance Score")
        fig.tight_layout()
        return [{"title": "Feature Importance", "base64": _fig_to_base64(fig)}]
    except Exception:
        return []


def generate_anomaly_plot(df: pd.DataFrame, scores: np.ndarray, feature_cols: list) -> list:
    """Generate scatter plot highlighting anomalies. Returns list of {title, base64} dicts."""
    if len(feature_cols) < 2:
        return []

    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        x_col, y_col = feature_cols[0], feature_cols[1]
        normal = scores == 1
        anomaly = scores == -1

        ax.scatter(df.loc[normal, x_col], df.loc[normal, y_col], c=TEAL, alpha=0.5, s=30, label="Normal", edgecolors="white")
        ax.scatter(df.loc[anomaly, x_col], df.loc[anomaly, y_col], c="#EF4444", alpha=0.8, s=60, label="Anomaly", edgecolors="black", linewidth=1, marker="x")
        ax.set_xlabel(x_col, fontsize=10)
        ax.set_ylabel(y_col, fontsize=10)
        ax.set_title("ANOMALY DETECTION", fontsize=12, fontweight="bold")
        ax.legend()
        fig.tight_layout()
        return [{"title": "Anomaly Detection", "base64": _fig_to_base64(fig)}]
    except Exception:
        return []
