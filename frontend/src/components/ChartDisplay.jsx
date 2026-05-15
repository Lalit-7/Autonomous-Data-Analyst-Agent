/**
 * ChartDisplay — renders base64-encoded charts from the analysis.
 */
import React from 'react';
import './ChartDisplay.css';

export default function ChartDisplay({ charts }) {
  if (!charts || charts.length === 0) return null;

  return (
    <div className="charts-section slide-up" id="charts-section">
      <div className="section-label">04 — VISUALIZATIONS</div>
      <div className="charts-grid">
        {charts.map((chart, i) => (
          <div className="card chart-card" key={i}>
            {chart.title && (
              <h4 className="chart-title mono">{chart.title}</h4>
            )}
            {chart.base64 && (
              <img
                src={`data:image/png;base64,${chart.base64}`}
                alt={chart.title || `Chart ${i + 1}`}
                className="chart-image"
                loading="lazy"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
