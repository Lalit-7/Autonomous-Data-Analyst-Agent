"""
Agent orchestrator — autonomous analysis loop using Google Gemini with function calling.
Lightweight implementation that doesn't depend on heavy LangGraph imports.
"""

import os
import json
import pandas as pd
import numpy as np
import google.generativeai as genai

from agent.prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE, FOLLOW_UP_PROMPT_TEMPLATE
from agent.memory import memory
from ml.visualizer import (
    generate_distribution_charts, generate_correlation_heatmap,
    generate_categorical_charts, generate_cluster_plot,
    generate_feature_importance_plot, generate_anomaly_plot,
)
from ml.analyzer import auto_analyze, detect_task_type, run_profiling
from utils.file_handler import get_schema_summary

# Current dataframe reference for the session
_current_df = None


def set_current_dataframe(df: pd.DataFrame):
    """Set the global dataframe reference. Returns None."""
    global _current_df
    _current_df = df


def _configure_gemini():
    """Configure the Gemini API client. Returns None."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    genai.configure(api_key=api_key)


def _call_gemini(prompt: str, system_instruction: str = None) -> str:
    """Call Gemini to generate a text response. Returns the response text."""
    _configure_gemini()
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction or SYSTEM_PROMPT,
    )
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096,
            ),
        )
        return response.text
    except Exception as e:
        return f"LLM synthesis encountered an error: {str(e)}. The auto-analysis results below are still valid."


async def run_agent(session_id: str, query: str, df: pd.DataFrame, on_step=None) -> dict:
    """Run the full agent pipeline: memory → analysis → charts → LLM synthesis → memory store.
    Returns a dict with insights, charts, metrics, tags, and steps."""

    set_current_dataframe(df)
    schema = get_schema_summary(df)

    # Step 1: Retrieve memory context
    if on_step:
        await on_step("Retrieving session context...")

    memory_context = memory.retrieve_context(session_id, query)
    is_followup = "No previous interactions" not in memory_context

    # Step 2: Run auto-analysis (profiling + ML)
    if on_step:
        await on_step("Running auto-analysis...")

    analysis_result = auto_analyze(df, query)
    ml_result = analysis_result.get("ml_result", {})
    profiling = analysis_result.get("profiling", {})

    # Step 3: Generate charts
    if on_step:
        await on_step("Generating visualizations...")

    all_charts = []
    try:
        all_charts.extend(generate_distribution_charts(df))
    except Exception:
        pass
    try:
        all_charts.extend(generate_correlation_heatmap(df))
    except Exception:
        pass
    try:
        all_charts.extend(generate_categorical_charts(df))
    except Exception:
        pass

    # ML-specific charts
    if ml_result.get("task_type") == "clustering" and "labels" in ml_result:
        try:
            labels = np.array(ml_result["labels"])
            feature_cols = ml_result.get("feature_columns", [])
            all_charts.extend(generate_cluster_plot(df, labels, feature_cols))
        except Exception:
            pass

    if ml_result.get("feature_importances"):
        try:
            all_charts.extend(generate_feature_importance_plot(ml_result["feature_importances"]))
        except Exception:
            pass

    if ml_result.get("task_type") == "anomaly_detection" and "predictions" in ml_result:
        try:
            preds = np.array(ml_result["predictions"])
            feature_cols = ml_result.get("feature_columns", [])
            all_charts.extend(generate_anomaly_plot(df, preds, feature_cols))
        except Exception:
            pass

    # Step 4: Prepare analysis summary for LLM
    analysis_summary = json.dumps({
        "profiling": profiling,
        "ml_result": {k: v for k, v in ml_result.items() if k not in ["labels", "predictions"]},
    }, default=str, indent=2)

    # Build the LLM prompt
    if is_followup:
        base_prompt = FOLLOW_UP_PROMPT_TEMPLATE.format(
            query=query, memory_context=memory_context, schema=schema,
        )
    else:
        base_prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            query=query, memory_context=memory_context, schema=schema,
        )

    full_prompt = f"""{base_prompt}

## AUTO-ANALYSIS RESULTS (already computed — synthesize these into your response)
{analysis_summary}

Provide your complete analysis report with Summary, Key Metrics, Insights, and Recommendations.
Be specific — reference actual column names, values, and numbers from the results above."""

    # Step 5: Call Gemini to synthesize insights
    if on_step:
        await on_step("LLM synthesizing insights...")

    insights = _call_gemini(full_prompt)

    # Step 6: Build metrics
    metrics = {}
    if ml_result.get("accuracy"):
        metrics["Accuracy"] = f"{ml_result['accuracy'] * 100:.1f}%"
    if ml_result.get("r2_score"):
        metrics["R² Score"] = f"{ml_result['r2_score']:.4f}"
    if ml_result.get("rmse"):
        metrics["RMSE"] = f"{ml_result['rmse']:.4f}"
    if ml_result.get("silhouette_score"):
        metrics["Silhouette"] = f"{ml_result['silhouette_score']:.4f}"
    if ml_result.get("n_clusters"):
        metrics["Clusters"] = ml_result["n_clusters"]
    if ml_result.get("anomalies_found") is not None:
        metrics["Anomalies"] = ml_result["anomalies_found"]
    metrics["Records"] = int(df.shape[0])
    metrics["Features"] = int(df.shape[1])

    # Tags
    tags = ["Completed"]
    task_type = ml_result.get("task_type", "exploration")
    tag_map = {
        "classification": "Classification",
        "regression": "Regression",
        "clustering": "Clustering",
        "anomaly_detection": "Anomaly Detection",
        "exploration": "Exploratory Analysis",
        "exploration_with_clustering": "EDA + Clustering",
    }
    tags.append(tag_map.get(task_type, "Analysis"))
    if ml_result.get("algorithm"):
        tags.append(ml_result["algorithm"])

    # Step 7: Store in memory
    if on_step:
        await on_step("Storing in session memory...")

    memory.store_interaction(
        session_id=session_id,
        query=query,
        response=insights[:2000] if insights else "",
        metadata={"task_type": task_type},
    )

    if on_step:
        await on_step("Complete")

    return {
        "insights": insights,
        "charts": all_charts,
        "metrics": metrics,
        "tags": tags,
        "ml_result": {k: v for k, v in ml_result.items() if k not in ["labels", "predictions"]},
        "profiling": profiling,
        "steps_completed": ["profiling", "ml_analysis", "visualization", "llm_synthesis", "memory_store"],
        "task_type": task_type,
    }
