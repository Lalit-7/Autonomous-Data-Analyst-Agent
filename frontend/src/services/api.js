/**
 * API service — handles all communication with the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Upload a file to the backend. Returns session info and data profile. */
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

/** Run analysis on the uploaded dataset. Returns insights, charts, metrics. */
export async function analyzeData(sessionId, query) {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('query', query);

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

/** Get session info and history. */
export async function getSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`);
  if (!res.ok) throw new Error('Session not found');
  return res.json();
}

/** Download PDF report for a session. Returns a blob URL. */
export async function downloadReport(sessionId) {
  const res = await fetch(`${API_BASE}/api/download-report/${sessionId}`);
  if (!res.ok) throw new Error('Report download failed');
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

/** Delete a session. */
export async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
}
