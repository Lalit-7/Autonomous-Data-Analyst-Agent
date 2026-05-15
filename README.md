# 🤖 Autonomous Data Analyst Agent

An AI-powered web application that autonomously analyzes datasets, runs real machine learning models, generates visualizations, and produces plain-English insight reports — all without user guidance.

**Upload data → Ask a question → Get a complete analysis.**

---

## ✨ Features

- **Autonomous Analysis** — The agent decides what to run (profiling, ML models, charts) without asking.
- **Real ML Models** — KMeans clustering, GradientBoosting classification/regression, IsolationForest anomaly detection.
- **Auto-Detection** — Automatically determines classification, regression, clustering, or anomaly detection from data shape.
- **Rich Visualizations** — Distribution plots, correlation heatmaps, cluster scatter plots, feature importance charts.
- **Session Memory** — ChromaDB-backed memory for follow-up questions with full context.
- **PDF Export** — Download a complete analysis report as PDF.
- **Multi-Format Upload** — CSV, Excel (.xlsx/.xls), and JSON.
- **LangGraph Orchestration** — Structured agentic loop with tool routing, retry logic, and state management.
- **Editorial UI** — Clean, professional SaaS dashboard with light paper-and-ink aesthetic.

---

## 🏗️ Architecture

```
┌──────────────────────┐     REST API      ┌─────────────────────────┐
│   React Frontend     │  ◄──────────────► │   FastAPI Backend       │
│   (Vite)             │                   │                         │
└──────────────────────┘                   │  ┌───────────────────┐  │
                                           │  │ LangGraph Agent   │  │
                                           │  │  • Gemini 2.0     │  │
                                           │  │  • 6 Agent Tools  │  │
                                           │  └───────────────────┘  │
                                           │  ┌───────────────────┐  │
                                           │  │ ChromaDB Memory   │  │
                                           │  └───────────────────┘  │
                                           │  ┌───────────────────┐  │
                                           │  │ ML Engine         │  │
                                           │  │ scikit-learn      │  │
                                           │  └───────────────────┘  │
                                           └─────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + Vite | SPA dashboard UI |
| Backend | FastAPI + Uvicorn | REST API server |
| LLM | Google Gemini 2.0 Flash | Reasoning + tool selection |
| Agent | LangGraph | Agentic loop orchestration |
| ML | scikit-learn | KMeans, GradientBoosting, IsolationForest |
| Charts | Matplotlib + Seaborn | Statistical visualizations |
| Memory | ChromaDB | Session context retrieval |
| PDF | FPDF2 | Report generation |

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py              # FastAPI server with all API endpoints
│   ├── agent/
│   │   ├── graph.py          # LangGraph agentic loop with Gemini
│   │   ├── tools.py          # 6 tool definitions (profiler, ML, viz, etc.)
│   │   ├── memory.py         # ChromaDB session memory
│   │   └── prompts.py        # System prompts and guardrails
│   ├── ml/
│   │   ├── analyzer.py       # Auto-ML detection and execution engine
│   │   └── visualizer.py     # Chart generation (matplotlib/seaborn)
│   ├── utils/
│   │   └── file_handler.py   # File loading, profiling, PDF generation
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/       # React UI components
│   │   ├── services/api.js   # Backend API client
│   │   ├── App.jsx           # Main app shell
│   │   ├── App.css           # Layout styles
│   │   ├── index.css         # Design system
│   │   └── main.jsx          # Entry point
│   ├── index.html
│   ├── vite.config.js
│   └── .env
└── README.md
```

---

## 🧠 How the Agent Works

1. **User uploads data** → Backend saves file, profiles schema
2. **User asks a question** → Backend retrieves session memory from ChromaDB
3. **Auto-ML engine** runs profiling, detects task type, executes appropriate model
4. **Chart engine** generates distribution plots, correlation heatmaps, cluster plots
5. **LangGraph agent** invokes Gemini with tools, synthesizes all results into insights
6. **Memory update** → Stores Q&A pair in ChromaDB for follow-up context
7. **Response** → Charts, metrics, and plain-English insights returned to the frontend

---

## 📄 License

MIT License — free for personal and commercial use.
