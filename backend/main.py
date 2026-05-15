"""
FastAPI server — handles file uploads, analysis requests, session management, and PDF downloads.
"""

import os
import uuid
import json
import shutil
import asyncio
import tempfile
import pandas as pd
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from agent.graph import run_agent
from agent.memory import memory
from utils.file_handler import load_file, get_data_profile, get_schema_summary, generate_pdf_report

# App configuration
app = FastAPI(title="Autonomous Data Analyst Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions = {}
UPLOAD_DIR = Path(tempfile.gettempdir()) / "analyst_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint. Returns API status."""
    return {"status": "active", "service": "Autonomous Data Analyst Agent", "version": "1.0.0"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload — save, load, and profile the dataset. Returns session info and data profile."""
    # Validate file type
    allowed_extensions = [".csv", ".xlsx", ".xls", ".json"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}")

    session_id = str(uuid.uuid4())

    # Save uploaded file
    file_path = UPLOAD_DIR / f"{session_id}{ext}"
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Load and profile the data
    try:
        df = load_file(str(file_path), file.filename)
        profile = get_data_profile(df)
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    # Store session
    sessions[session_id] = {
        "session_id": session_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "file_size": len(content),
        "uploaded_at": datetime.now().isoformat(),
        "profile": profile,
        "analyses": [],
        "df": df,
    }

    return {
        "session_id": session_id,
        "filename": file.filename,
        "file_size": len(content),
        "rows": profile["rows"],
        "columns": profile["columns"],
        "column_names": profile["column_names"],
        "dtypes": profile["dtypes"],
        "numeric_columns": profile["numeric_columns"],
        "categorical_columns": profile["categorical_columns"],
        "null_counts": profile["null_counts"],
        "sample_data": profile["sample_data"][:3],
    }


@app.post("/api/analyze")
async def analyze_data(session_id: str = Form(...), query: str = Form(...)):
    """Run the autonomous agent on the uploaded dataset with the given query. Returns analysis results."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a file first.")

    session = sessions[session_id]
    df = session["df"]

    try:
        result = await run_agent(session_id, query, df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Store analysis in session
    analysis_record = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "insights": result.get("insights", ""),
        "metrics": result.get("metrics", {}),
        "charts": result.get("charts", []),
        "tags": result.get("tags", []),
        "task_type": result.get("task_type", "exploration"),
    }
    session["analyses"].append(analysis_record)

    return {
        "session_id": session_id,
        "query": query,
        "insights": result.get("insights", ""),
        "charts": result.get("charts", []),
        "metrics": result.get("metrics", {}),
        "tags": result.get("tags", []),
        "task_type": result.get("task_type", "exploration"),
        "ml_result": result.get("ml_result", {}),
        "profiling": result.get("profiling", {}),
        "steps_completed": result.get("steps_completed", []),
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session info and history. Returns session metadata and past analyses."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "session_id": session_id,
        "filename": session["filename"],
        "rows": session["profile"]["rows"],
        "columns": session["profile"]["columns"],
        "analyses_count": len(session["analyses"]),
        "analyses": [
            {
                "query": a["query"],
                "timestamp": a["timestamp"],
                "task_type": a.get("task_type", ""),
                "tags": a.get("tags", []),
            }
            for a in session["analyses"]
        ],
    }


@app.get("/api/download-report/{session_id}")
async def download_report(session_id: str):
    """Generate and download a PDF report for the session. Returns the PDF file."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    report_data = {
        "dataset_info": {
            "filename": session["filename"],
            "rows": session["profile"]["rows"],
            "columns": session["profile"]["columns"],
        },
        "analyses": session["analyses"],
    }

    try:
        pdf_bytes = generate_pdf_report(report_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=analysis_report_{session_id[:8]}.pdf"},
    )


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and clean up files. Returns confirmation."""
    if session_id in sessions:
        session = sessions[session_id]
        try:
            if os.path.exists(session["file_path"]):
                os.remove(session["file_path"])
        except Exception:
            pass
        memory.clear_session(session_id)
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
