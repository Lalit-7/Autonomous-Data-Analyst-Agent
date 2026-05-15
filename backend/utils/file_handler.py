"""
File handler utilities — loading CSV/Excel/JSON, profiling data, and generating PDF reports.
"""

import pandas as pd
import numpy as np
import json
import os
import io
import base64
import tempfile
from datetime import datetime
from fpdf import FPDF


def load_file(file_path: str, filename: str) -> pd.DataFrame:
    """Load a CSV, Excel, or JSON file into a pandas DataFrame. Returns the DataFrame."""
    try:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use CSV, Excel, or JSON.")
        return df
    except Exception as e:
        raise ValueError(f"Failed to load file '{filename}': {str(e)}")


def get_data_profile(df: pd.DataFrame) -> dict:
    """Generate a comprehensive profile of the DataFrame. Returns a dict with shape, dtypes, nulls, stats, and sample."""
    numeric_cols = list(df.select_dtypes(include=["number"]).columns)
    categorical_cols = list(df.select_dtypes(include=["object", "category"]).columns)
    datetime_cols = list(df.select_dtypes(include=["datetime64"]).columns)

    # Basic statistics for numeric columns
    stats = {}
    if numeric_cols:
        desc = df[numeric_cols].describe().round(3)
        stats = desc.to_dict()

    # Value counts for categorical columns (top 10)
    cat_summary = {}
    for col in categorical_cols[:20]:
        try:
            vc = df[col].value_counts().head(10)
            cat_summary[col] = {str(k): int(v) for k, v in vc.items()}
        except Exception:
            cat_summary[col] = {}

    profile = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": {col: int(count) for col, count in df.isnull().sum().items()},
        "null_percentages": {
            col: round(float(count / max(len(df), 1) * 100), 2)
            for col, count in df.isnull().sum().items()
        },
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "numeric_stats": stats,
        "categorical_summary": cat_summary,
        "sample_data": df.head(5).fillna("null").to_dict(orient="records"),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }
    return profile


def get_schema_summary(df: pd.DataFrame) -> str:
    """Generate a concise text summary of the dataframe schema for the LLM. Returns a string."""
    lines = [f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns\n"]
    lines.append("Columns:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = df[col].isnull().sum()
        unique = df[col].nunique()
        null_pct = round(nulls / max(len(df), 1) * 100, 1)
        sample_vals = df[col].dropna().head(3).tolist()
        sample_str = ", ".join(str(v) for v in sample_vals)
        lines.append(
            f"  - {col} ({dtype}): {unique} unique, {null_pct}% null | sample: [{sample_str}]"
        )
    return "\n".join(lines)


def _safe(text: str) -> str:
    """Encode text safely for FPDF (latin-1 only). Returns cleaned string."""
    return text.encode("latin-1", "replace").decode("latin-1")


def _render_markdown_to_pdf(pdf: FPDF, text: str):
    """Render markdown-formatted text into the PDF with proper formatting.
    Handles: ## headings, **bold** inline, * bullet lists, numbered lists, paragraphs.
    Returns None.
    """
    import re

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            pdf.ln(3)
            i += 1
            continue

        # --- Heading: ## or ### ---
        h2_match = re.match(r'^#{2,3}\s+(.+)', stripped)
        if h2_match:
            heading_text = h2_match.group(1)
            # Remove any remaining markdown bold from heading
            heading_text = re.sub(r'\*\*(.+?)\*\*', r'\1', heading_text)
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, _safe(heading_text), ln=True)
            pdf.set_draw_color(13, 148, 136)  # teal underline
            pdf.line(10, pdf.get_y(), 120, pdf.get_y())
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(3)
            i += 1
            continue

        # --- Numbered list: 1. text or 1) text ---
        num_match = re.match(r'^(\d+)[\.\)]\s+(.+)', stripped)
        if num_match:
            num = num_match.group(1)
            content = num_match.group(2)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(8)  # indent
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(8, 6, f"{num}.", ln=False)
            _render_inline_bold(pdf, content)
            pdf.ln(6)
            i += 1
            continue

        # --- Bullet list: * text or - text ---
        bullet_match = re.match(r'^[\*\-]\s+(.+)', stripped)
        if bullet_match:
            content = bullet_match.group(1)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(8)  # indent
            pdf.cell(5, 6, "-", ln=False)  # bullet
            _render_inline_bold(pdf, content)
            pdf.ln(6)
            i += 1
            continue

        # --- Regular paragraph ---
        _render_inline_bold_multi(pdf, stripped)
        pdf.ln(2)
        i += 1


def _render_inline_bold(pdf: FPDF, text: str):
    """Render a single line with **bold** segments inline. Does not add line break. Returns None."""
    import re
    parts = re.split(r'(\*\*.+?\*\*)', text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(6, _safe(part[2:-2]))
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.write(6, _safe(part))


def _render_inline_bold_multi(pdf: FPDF, text: str):
    """Render a paragraph with **bold** as a multi-cell (word-wrapping). Returns None."""
    import re
    # Check if text has bold markers
    if "**" not in text:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _safe(text))
        return

    # Split into bold and non-bold segments
    parts = re.split(r'(\*\*.+?\*\*)', text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(6, _safe(part[2:-2]))
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.write(6, _safe(part))
    pdf.ln(6)


def generate_pdf_report(session_data: dict) -> bytes:
    """Generate a PDF report from session analysis data. Returns bytes of the PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "Data Analysis Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0, 8,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ln=True, align="C",
    )
    pdf.ln(10)

    # Dataset info
    info = session_data.get("dataset_info", {})
    if info:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Dataset Overview", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"File: {info.get('filename', 'N/A')}", ln=True)
        pdf.cell(
            0, 7,
            f"Records: {info.get('rows', 'N/A')}  |  Features: {info.get('columns', 'N/A')}",
            ln=True,
        )
        pdf.ln(5)

    # Analysis results
    analyses = session_data.get("analyses", [])
    for i, analysis in enumerate(analyses):
        pdf.set_font("Helvetica", "B", 14)
        query_text = analysis.get("query", f"Analysis {i + 1}")
        pdf.cell(0, 10, _safe(f"Q: {query_text[:80]}"), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        # Insights — rendered with proper markdown formatting
        insights = analysis.get("insights", "")
        if insights:
            _render_markdown_to_pdf(pdf, insights)
            pdf.ln(3)

        # Metrics
        metrics = analysis.get("metrics", {})
        if metrics:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Key Metrics:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for key, val in metrics.items():
                pdf.cell(8)
                pdf.set_font("Helvetica", "B", 10)
                pdf.write(6, _safe(f"{key}: "))
                pdf.set_font("Helvetica", "", 10)
                pdf.write(6, _safe(str(val)))
                pdf.ln(6)
            pdf.ln(3)

        # Charts
        charts = analysis.get("charts", [])
        for j, chart in enumerate(charts):
            try:
                if "base64" in chart and chart["base64"]:
                    img_data = base64.b64decode(chart["base64"])
                    tmp_path = os.path.join(
                        tempfile.gettempdir(), f"chart_{i}_{j}.png"
                    )
                    with open(tmp_path, "wb") as f:
                        f.write(img_data)
                    pdf.image(tmp_path, w=170)
                    pdf.ln(5)
                    os.remove(tmp_path)
            except Exception:
                pass

        pdf.ln(5)

    return bytes(pdf.output())

