/**
 * App.jsx — Main application shell wiring all components together.
 */
import React, { useState, useCallback } from 'react';
import Navbar from './components/Navbar';
import FileUpload from './components/FileUpload';
import ChatInput from './components/ChatInput';
import AnalysisResult from './components/AnalysisResult';
import ChartDisplay from './components/ChartDisplay';
import Sidebar from './components/Sidebar';
import { uploadFile, analyzeData, downloadReport } from './services/api';
import './App.css';

export default function App() {

  const [sessionId, setSessionId] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [activeTaskIndex, setActiveTaskIndex] = useState(-1);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    recordsProcessed: 0,
    avgAccuracy: '—',
    tasksCompleted: 0,
    avgTime: '—',
  });

  /* Handle file upload */
  const handleUpload = useCallback(async (file) => {
    if (file === null) {
      setUploadedFile(null);
      setSessionId(null);
      setAnalysisResult(null);
      setAnalysisHistory([]);
      setError('');
      setStats({ recordsProcessed: 0, avgAccuracy: '—', tasksCompleted: 0, avgTime: '—' });
      return;
    }

    setIsUploading(true);
    setError('');
    try {
      const data = await uploadFile(file);
      setSessionId(data.session_id);
      setUploadedFile(data);
      setStats(prev => ({ ...prev, recordsProcessed: data.rows || 0 }));
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, []);

  /* Handle analysis query */
  const handleAnalyze = useCallback(async (query) => {
    if (!sessionId) {
      setError('Please upload a file first');
      return;
    }

    setIsAnalyzing(true);
    setError('');
    setCurrentStep('Initializing agent...');
    const startTime = Date.now();

    try {
      // Simulate step progression for UX while waiting for backend
      const stepTimer = setInterval(() => {
        setCurrentStep(prev => {
          const steps = [
            'Initializing agent...',
            'Running auto-analysis...',
            'Generating visualizations...',
            'LLM synthesizing insights...',
            'Storing in session memory...',
          ];
          const idx = steps.indexOf(prev);
          if (idx < steps.length - 1) return steps[idx + 1];
          return prev;
        });
      }, 3000);

      const result = await analyzeData(sessionId, query);
      clearInterval(stepTimer);

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      const fullResult = { ...result, query };
      setAnalysisResult(fullResult);
      setCurrentStep('Complete');
      setAnalysisHistory(prev => {
        const updated = [...prev, { query, task_type: result.task_type, timestamp: new Date().toISOString(), result: fullResult }];
        setActiveTaskIndex(updated.length - 1);
        return updated;
      });

      // Update stats
      setStats(prev => {
        const newCompleted = prev.tasksCompleted + 1;
        let acc = prev.avgAccuracy;
        if (result.metrics?.Accuracy) {
          acc = result.metrics.Accuracy;
        } else if (result.metrics?.['R² Score']) {
          acc = result.metrics['R² Score'];
        } else if (result.metrics?.Silhouette) {
          acc = result.metrics.Silhouette;
        }
        return {
          ...prev,
          tasksCompleted: newCompleted,
          avgAccuracy: acc,
          avgTime: `${elapsed}s`,
        };
      });
    } catch (err) {
      setError(err.message || 'Analysis failed');
      setCurrentStep('');
    } finally {
      setIsAnalyzing(false);
    }
  }, [sessionId]);

  /* Handle PDF export — smart filename from task type + dataset + query */
  const handleExportPdf = useCallback(async () => {
    if (!sessionId) return;
    try {
      const blobUrl = await downloadReport(sessionId);

      // Build smart filename: "Classification Analysis heart dataset Summarize.pdf"
      const taskTitles = {
        classification: 'Classification Analysis',
        regression: 'Regression Analysis',
        clustering: 'Cluster Segmentation',
        anomaly_detection: 'Anomaly Detection',
        exploration: 'Exploratory Analysis',
      };
      const taskPart = taskTitles[analysisResult?.task_type] || 'Data Analysis';
      const datasetPart = uploadedFile?.filename?.replace(/\.\w+$/, '') || 'dataset';
      const queryPart = analysisResult?.query
        ? analysisResult.query.split(' ').slice(0, 3).join(' ')
        : '';
      const pdfName = `${taskPart} ${datasetPart} ${queryPart}`.trim().replace(/[^a-zA-Z0-9\s\-_]/g, '');

      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `${pdfName}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError('PDF download failed: ' + err.message);
    }
  }, [sessionId, analysisResult, uploadedFile]);

  /* Handle view report (scroll to results) */
  const handleViewReport = useCallback(() => {
    document.getElementById('analysis-result')?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /* Handle task queue click — switch to a previous analysis */
  const handleTaskClick = useCallback((taskIndex) => {
    const task = analysisHistory[taskIndex];
    if (task?.result) {
      setAnalysisResult(task.result);
      setActiveTaskIndex(taskIndex);
      setCurrentStep('Complete');
      // Scroll to results
      setTimeout(() => {
        document.getElementById('analysis-result')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [analysisHistory]);

  return (
    <>
      <Navbar />

      <main className="main-container">
        <div className="main-grid">
          {/* Left Column — Primary Analysis Area */}
          <div className="main-left">
            <FileUpload
              onUpload={handleUpload}
              uploadedFile={uploadedFile}
              isUploading={isUploading}
            />

            {/* Currently Analyzing Card */}
            {isAnalyzing && (
              <div className="card analyzing-card slide-up" id="analyzing-card">
                <div className="section-label">CURRENTLY ANALYZING</div>
                <div className="analyzing-info">
                  <span className="analyzing-name">{uploadedFile?.filename}</span>
                  <span className="mono analyzing-meta">
                    {uploadedFile?.rows?.toLocaleString()} records • {uploadedFile?.columns} features
                  </span>
                </div>
                <div className="progress-bar" style={{ marginTop: 16 }}>
                  <div
                    className="progress-fill"
                    style={{
                      width: currentStep === 'Complete' ? '100%'
                        : currentStep.includes('memory') ? '90%'
                        : currentStep.includes('synthesizing') ? '75%'
                        : currentStep.includes('visualizations') ? '55%'
                        : currentStep.includes('auto-analysis') ? '35%'
                        : '15%'
                    }}
                  ></div>
                </div>
                <span className="mono analyzing-step" style={{ marginTop: 8, display: 'block' }}>
                  {currentStep}
                </span>
              </div>
            )}

            <ChatInput
              onSubmit={handleAnalyze}
              isAnalyzing={isAnalyzing}
              disabled={!uploadedFile}
            />

            {/* Error Display */}
            {error && (
              <div className="card error-card fade-in" id="error-display">
                <p className="error-text">⚠ {error}</p>
                <button className="btn btn-outline" onClick={() => setError('')} style={{ marginTop: 8, padding: '6px 12px', fontSize: '0.8rem' }}>
                  Dismiss
                </button>
              </div>
            )}

            {/* Analysis Result */}
            <AnalysisResult
              result={analysisResult}
              onExportPdf={handleExportPdf}
              onViewReport={handleViewReport}
            />

            {/* Charts */}
            <ChartDisplay charts={analysisResult?.charts} />

            {/* Latest Insights */}
            {analysisResult?.profiling?.high_correlations?.length > 0 && (
              <div className="insights-row slide-up" id="latest-insights">
                <div className="section-label">05 — LATEST INSIGHTS</div>
                <div className="insights-grid">
                  {analysisResult.profiling.high_correlations.slice(0, 3).map((corr, i) => (
                    <div className="card insight-mini-card" key={i}>
                      <div className="insight-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0D9488" strokeWidth="2">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="8" x2="12" y2="12" />
                          <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                      </div>
                      <p className="insight-finding">
                        <strong>{corr.col1}</strong> and <strong>{corr.col2}</strong> have a {corr.strength} correlation ({corr.correlation})
                      </p>
                      <span className="mono insight-source">{corr.col1}, {corr.col2}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column — Sidebar */}
          <div className="main-right">
            <Sidebar
              stats={stats}
              currentStep={currentStep}
              isAnalyzing={isAnalyzing}
              analysisHistory={analysisHistory}
              activeTaskIndex={activeTaskIndex}
              onTaskClick={handleTaskClick}
            />
          </div>
        </div>
      </main>
    </>
  );
}
