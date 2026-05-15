/**
 * Navbar — top navigation bar with branding.
 */
import React from 'react';
import './Navbar.css';

export default function Navbar() {
  return (
    <nav className="navbar" id="main-navbar">
      <div className="navbar-inner">
        {/* Left: Brand */}
        <div className="navbar-brand">
          <div className="navbar-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="6" fill="#0D9488" />
              <path d="M8 10h12M8 14h8M8 18h10" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
          <div className="navbar-titles">
            <span className="navbar-title">Data Analyst Agent</span>
            <span className="navbar-subtitle mono">Autonomous Intelligence System</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
