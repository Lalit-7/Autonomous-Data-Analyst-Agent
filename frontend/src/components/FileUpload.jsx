/**
 * FileUpload — drag-and-drop file upload zone with file info display.
 */
import React, { useRef, useState } from 'react';
import './FileUpload.css';

export default function FileUpload({ onUpload, uploadedFile, isUploading }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleClick = () => inputRef.current?.click();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) onUpload(file);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="card file-upload-card fade-in" id="file-upload-section">
      <div className="section-label">01 — UPLOAD</div>

      {!uploadedFile ? (
        <div
          className={`dropzone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          id="file-dropzone"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          {isUploading ? (
            <div className="upload-loading">
              <div className="spinner"></div>
              <p>Processing file...</p>
            </div>
          ) : (
            <>
              <div className="dropzone-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0D9488" strokeWidth="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p className="dropzone-text">
                <strong>Drop your file here</strong> or click to browse
              </p>
              <span className="mono" style={{ marginTop: '8px' }}>
                CSV, EXCEL, JSON
              </span>
            </>
          )}
        </div>
      ) : (
        <div className="file-info" id="uploaded-file-info">
          <div className="file-info-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0D9488" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <div className="file-info-details">
            <span className="file-name">{uploadedFile.filename}</span>
            <span className="mono">
              {uploadedFile.rows?.toLocaleString()} rows × {uploadedFile.columns} columns
              {uploadedFile.file_size && ` • ${formatSize(uploadedFile.file_size)}`}
            </span>
          </div>
          <button
            className="btn btn-outline"
            onClick={() => { onUpload(null); }}
            style={{ marginLeft: 'auto', padding: '6px 12px', fontSize: '0.8rem' }}
          >
            Change
          </button>
        </div>
      )}
    </div>
  );
}
