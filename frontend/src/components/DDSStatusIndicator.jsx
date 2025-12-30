import React, { useState, useEffect } from 'react';
import './DDSStatusIndicator.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Get session ID from localStorage (same as api.js SessionManager)
const getSessionId = () => {
  return localStorage.getItem('bridge_session_id') || 'default';
};

// Standard difficulty order: Beginner -> Intermediate -> Advanced -> Expert
const DIFFICULTY_ORDER = ['beginner', 'intermediate', 'advanced', 'expert'];

const DDSStatusIndicator = () => {
  const [aiStatus, setAiStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetchAIStatus();
  }, []);

  const fetchAIStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/ai/status`, {
        headers: { 'X-Session-ID': getSessionId() }
      });
      const data = await response.json();
      setAiStatus(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch AI status:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dds-status-indicator loading">
        <span className="status-dot">⋯</span>
        <span className="status-text">Loading AI...</span>
      </div>
    );
  }

  if (!aiStatus) {
    return (
      <div className="dds-status-indicator error">
        <span className="status-dot">⚠️</span>
        <span className="status-text">AI Status Unknown</span>
      </div>
    );
  }

  const ddsAvailable = aiStatus.dds_available;
  const expertAI = aiStatus.difficulties?.expert;

  return (
    <div className={`dds-status-indicator ${ddsAvailable ? 'dds-enabled' : 'dds-disabled'}`}>
      <div
        className="status-main"
        onClick={() => setExpanded(!expanded)}
        title="Click for details"
      >
        <span className="status-dot">
          {ddsAvailable ? '✅' : '⚠️'}
        </span>
        <span className="status-text">
          {ddsAvailable ? 'DDS Expert AI Active' : 'Expert AI (Fallback)'}
        </span>
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
      </div>

      {expanded && (
        <div className="status-details">
          <div className="status-detail-section">
            <h4>Expert AI Status</h4>
            <div className="status-info">
              <div className="info-row">
                <span className="info-label">Name:</span>
                <span className="info-value">{expertAI?.name || 'Unknown'}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Rating:</span>
                <span className="info-value">{expertAI?.rating || 'N/A'}</span>
              </div>
              <div className="info-row">
                <span className="info-label">DDS:</span>
                <span className={`info-value ${ddsAvailable ? 'success' : 'warning'}`}>
                  {ddsAvailable ? 'Enabled ✓' : 'Not Available ✗'}
                </span>
              </div>
              <div className="info-description">
                {expertAI?.description || 'No description'}
              </div>
            </div>
          </div>

          {aiStatus.dds_statistics && (
            <div className="status-detail-section">
              <h4>DDS Performance</h4>
              <div className="status-info">
                <div className="info-row">
                  <span className="info-label">Solves:</span>
                  <span className="info-value">{aiStatus.dds_statistics.solve_count || 0}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Avg Time:</span>
                  <span className="info-value">
                    {aiStatus.dds_statistics.avg_time
                      ? `${(aiStatus.dds_statistics.avg_time * 1000).toFixed(1)}ms`
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="status-detail-section all-difficulties">
            <h4>All Difficulty Levels</h4>
            {DIFFICULTY_ORDER
              .filter(level => aiStatus.difficulties?.[level])
              .map(level => {
                const info = aiStatus.difficulties[level];
                const isActive = level === aiStatus.current_difficulty;
                return (
                  <div key={level} className="difficulty-row" style={{
                    fontWeight: isActive ? 'bold' : 'normal',
                    backgroundColor: isActive ? 'rgba(76, 175, 80, 0.1)' : 'transparent'
                  }}>
                    <span className="difficulty-name">
                      {isActive && '▶ '}{info.name}:
                    </span>
                    <span className="difficulty-rating">{info.rating}</span>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};

export default DDSStatusIndicator;
