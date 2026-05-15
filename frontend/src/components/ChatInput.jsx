/**
 * ChatInput — query input bar with suggested prompt chips.
 */
import React, { useState } from 'react';
import './ChatInput.css';

const SUGGESTED_PROMPTS = [
  'Find patterns',
  'Predict outcomes',
  'Show correlations',
  'Detect anomalies',
  'Segment customers',
  'Summarize data',
];

export default function ChatInput({ onSubmit, isAnalyzing, disabled }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || isAnalyzing || disabled) return;
    onSubmit(query.trim());
    setQuery('');
  };

  const handleChipClick = (prompt) => {
    if (isAnalyzing || disabled) return;
    onSubmit(prompt);
  };

  return (
    <div className="card chat-input-card fade-in" id="chat-input-section">
      <div className="section-label">02 — ASK</div>

      <form onSubmit={handleSubmit} className="chat-form">
        <div className="chat-input-wrapper">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your data..."
            className="chat-input"
            disabled={isAnalyzing || disabled}
            id="query-input"
          />
          <button
            type="submit"
            className="btn btn-primary chat-send"
            disabled={!query.trim() || isAnalyzing || disabled}
            id="send-query-btn"
          >
            {isAnalyzing ? (
              <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }}></div>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
      </form>

      <div className="prompt-chips">
        {SUGGESTED_PROMPTS.map(prompt => (
          <button
            key={prompt}
            className="prompt-chip"
            onClick={() => handleChipClick(prompt)}
            disabled={isAnalyzing || disabled}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
