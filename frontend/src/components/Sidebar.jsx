/**
 * Sidebar — right column with agent stats, clickable task queue, and processing steps.
 */
import React from 'react';
import './Sidebar.css';

const PROCESSING_STEPS = [
  { id: 1, label: 'Data Cleaning', key: 'cleaning' },
  { id: 2, label: 'Feature Engineering', key: 'features' },
  { id: 3, label: 'Model Training', key: 'training' },
  { id: 4, label: 'Validation', key: 'validation' },
  { id: 5, label: 'Report Generation', key: 'report' },
];

export default function Sidebar({ stats, currentStep, isAnalyzing, analysisHistory, activeTaskIndex, onTaskClick }) {
  const getStepStatus = (stepIndex) => {
    if (!isAnalyzing && !currentStep) return 'pending';
    if (currentStep === 'Complete') return 'done';

    const activeSteps = {
      'Initializing agent...': 0,
      'Running auto-analysis...': 1,
      'Generating visualizations...': 2,
      'LLM synthesizing insights...': 3,
      'Storing in session memory...': 4,
      'Complete': 5,
    };
    const activeIndex = activeSteps[currentStep] ?? -1;

    if (stepIndex < activeIndex) return 'done';
    if (stepIndex === activeIndex) return 'active';
    return 'pending';
  };

  // Get the display list (most recent first) with original indices
  const displayTasks = analysisHistory
    ? analysisHistory.map((task, i) => ({ ...task, originalIndex: i })).slice(-5).reverse()
    : [];

  return (
    <aside className="sidebar" id="sidebar">
      {/* Agent Stats */}
      <div className="card sidebar-card fade-in" id="agent-stats">
        <div className="section-label">AGENT PERFORMANCE</div>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-value">{stats.recordsProcessed?.toLocaleString() || '0'}</span>
            <span className="stat-label mono">Records Processed</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.avgAccuracy || '—'}</span>
            <span className="stat-label mono">Avg Accuracy</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.tasksCompleted || 0}</span>
            <span className="stat-label mono">Tasks Completed</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.avgTime || '—'}</span>
            <span className="stat-label mono">Avg Time</span>
          </div>
        </div>
      </div>

      {/* Clickable Task Queue */}
      <div className="card sidebar-card fade-in" id="task-queue">
        <div className="section-label">TASK QUEUE</div>
        {displayTasks.length > 0 ? (
          <ul className="task-list">
            {displayTasks.map((task, i) => {
              const isActive = task.originalIndex === activeTaskIndex;
              const isProcessing = i === 0 && isAnalyzing;
              return (
                <li
                  className={`task-item clickable ${isActive ? 'task-active' : ''}`}
                  key={task.originalIndex}
                  onClick={() => !isProcessing && onTaskClick && onTaskClick(task.originalIndex)}
                  title={`Click to view: ${task.query}`}
                >
                  <span className={`task-dot ${isProcessing ? 'processing' : 'done'}`}></span>
                  <div className="task-info">
                    <span className="task-name">{task.query?.slice(0, 40) || 'Analysis'}</span>
                    <span className="mono task-meta">
                      {task.task_type?.toUpperCase().replace('_', ' ') || 'ANALYSIS'}
                    </span>
                  </div>
                  {isActive && (
                    <span className="task-active-badge mono">VIEWING</span>
                  )}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="sidebar-empty mono">No tasks yet. Upload data to begin.</p>
        )}
      </div>

      {/* Processing Steps */}
      <div className="card sidebar-card fade-in" id="processing-steps">
        <div className="section-label">PROCESSING PIPELINE</div>
        <div className="timeline">
          {PROCESSING_STEPS.map((step, i) => {
            const status = getStepStatus(i);
            return (
              <div className={`timeline-item ${status}`} key={step.id}>
                <div className="timeline-node">
                  {status === 'done' && (
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                  {status === 'active' && <div className="node-spinner"></div>}
                </div>
                <span className="timeline-label">{step.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

