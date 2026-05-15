/**
 * AnalysisResult — displays the analysis output: tags, title, metrics, insights, and action buttons.
 * Converts raw markdown from Gemini into clean, professional formatted HTML.
 */
import React, { useMemo } from 'react';
import './AnalysisResult.css';

const TAG_COLORS = {
  'Completed': 'tag-green',
  'Classification': 'tag-purple',
  'Regression': 'tag-purple',
  'Clustering': 'tag-teal',
  'Anomaly Detection': 'tag-red',
  'Exploratory Analysis': 'tag-teal',
  'EDA + Clustering': 'tag-teal',
};

/**
 * Convert markdown text to an array of React elements.
 * Handles: ## headings, **bold**, *italic*, `code`, numbered lists, bullet lists.
 */
function renderMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let listItems = [];
  let listType = null; // 'ol' or 'ul'

  const flushList = () => {
    if (listItems.length > 0) {
      if (listType === 'ol') {
        elements.push(<ol key={`ol-${elements.length}`} className="insight-list">{listItems}</ol>);
      } else {
        elements.push(<ul key={`ul-${elements.length}`} className="insight-list">{listItems}</ul>);
      }
      listItems = [];
      listType = null;
    }
  };

  const formatInline = (str) => {
    // Process inline formatting: **bold**, *italic*, `code`
    const parts = [];
    let remaining = str;
    let key = 0;

    while (remaining.length > 0) {
      // Bold: **text**
      const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
      // Code: `text`
      const codeMatch = remaining.match(/`(.+?)`/);
      // Italic: *text* (single asterisk, not double)
      const italicMatch = remaining.match(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/);

      // Find earliest match
      let earliest = null;
      let earliestIdx = Infinity;

      if (boldMatch && remaining.indexOf(boldMatch[0]) < earliestIdx) {
        earliest = { type: 'bold', match: boldMatch };
        earliestIdx = remaining.indexOf(boldMatch[0]);
      }
      if (codeMatch && remaining.indexOf(codeMatch[0]) < earliestIdx) {
        earliest = { type: 'code', match: codeMatch };
        earliestIdx = remaining.indexOf(codeMatch[0]);
      }

      if (!earliest) {
        parts.push(remaining);
        break;
      }

      const idx = earliestIdx;
      if (idx > 0) parts.push(remaining.substring(0, idx));

      if (earliest.type === 'bold') {
        parts.push(<strong key={key++}>{earliest.match[1]}</strong>);
      } else if (earliest.type === 'code') {
        parts.push(<code key={key++} className="inline-code">{earliest.match[1]}</code>);
      }

      remaining = remaining.substring(idx + earliest.match[0].length);
    }

    return parts;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      continue;
    }

    // Heading: ## or ###
    const h2Match = trimmed.match(/^##\s+(.+)/);
    const h3Match = trimmed.match(/^###\s+(.+)/);

    if (h2Match) {
      flushList();
      elements.push(
        <h3 key={`h-${i}`} className="insight-heading">{formatInline(h2Match[1])}</h3>
      );
      continue;
    }
    if (h3Match) {
      flushList();
      elements.push(
        <h4 key={`h-${i}`} className="insight-subheading">{formatInline(h3Match[1])}</h4>
      );
      continue;
    }

    // Numbered list: 1. text or 1) text
    const numMatch = trimmed.match(/^\d+[\.\)]\s+(.+)/);
    if (numMatch) {
      if (listType !== 'ol') flushList();
      listType = 'ol';
      listItems.push(<li key={`li-${i}`}>{formatInline(numMatch[1])}</li>);
      continue;
    }

    // Bullet list: * text or - text
    const bulletMatch = trimmed.match(/^[\*\-]\s+(.+)/);
    if (bulletMatch) {
      if (listType !== 'ul') flushList();
      listType = 'ul';
      listItems.push(<li key={`li-${i}`}>{formatInline(bulletMatch[1])}</li>);
      continue;
    }

    // Regular paragraph
    flushList();
    elements.push(<p key={`p-${i}`}>{formatInline(trimmed)}</p>);
  }

  flushList();
  return elements;
}

export default function AnalysisResult({ result, onExportPdf, onViewReport }) {
  if (!result) return null;

  const { insights, metrics, tags, task_type, query } = result;

  const getTitle = () => {
    const titles = {
      classification: 'Classification Analysis',
      regression: 'Regression Analysis',
      clustering: 'Cluster Segmentation',
      anomaly_detection: 'Anomaly Detection',
      exploration: 'Exploratory Data Analysis',
      exploration_with_clustering: 'EDA + Cluster Analysis',
    };
    return titles[task_type] || 'Data Analysis';
  };

  const renderedInsights = useMemo(() => renderMarkdown(insights), [insights]);

  return (
    <div className="card analysis-result-card slide-up" id="analysis-result">
      <div className="section-label">03 — RESULTS</div>

      {/* Tags */}
      {tags && tags.length > 0 && (
        <div className="result-tags">
          {tags.map((tag, i) => (
            <span key={i} className={`tag ${TAG_COLORS[tag] || 'tag-teal'}`}>{tag}</span>
          ))}
        </div>
      )}

      {/* Title */}
      <h2 className="result-title">{getTitle()}</h2>
      {query && (
        <p className="mono result-query">Query: "{query}"</p>
      )}

      {/* Metrics Row */}
      {metrics && Object.keys(metrics).length > 0 && (
        <div className="metrics-row">
          {Object.entries(metrics).slice(0, 4).map(([key, value]) => (
            <div className="metric-item" key={key}>
              <span className="metric-value">{value}</span>
              <span className="metric-label mono">{key}</span>
            </div>
          ))}
        </div>
      )}

      <hr className="divider" />

      {/* Insights — rendered as clean HTML, no raw markdown */}
      {insights && (
        <div className="result-insights">
          <h4>Analysis Insights</h4>
          <div className="insights-text">
            {renderedInsights}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="result-actions">
        <button className="btn btn-outline" onClick={onViewReport} id="view-report-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          View Full Report
        </button>
        <button className="btn btn-primary" onClick={onExportPdf} id="export-pdf-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export PDF
        </button>
      </div>
    </div>
  );
}
