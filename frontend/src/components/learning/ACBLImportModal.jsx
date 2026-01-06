/**
 * ACBLImportModal.jsx
 *
 * Modal component for importing ACBL PBN tournament files.
 * Provides:
 * - Drag & drop or file picker for PBN files
 * - Import progress tracking
 * - Tournament list with analysis status
 * - Quick navigation to hand analysis
 *
 * Integration points:
 * - Uses /api/import/pbn endpoint
 * - Links to HandReviewModal for individual hand analysis
 * - Shows TournamentComparisonTable for audit results
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import TournamentComparisonTable from './TournamentComparisonTable';
import './ACBLImportModal.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

/**
 * File Drop Zone Component
 */
const FileDropZone = ({ onFileSelect, isUploading, pendingBwsData, onClearPendingBws }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragActive(true);
    }
  }, []);

  const handleDragOut = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const filename = file.name.toLowerCase();
      if (filename.endsWith('.pbn') || filename.endsWith('.bws') || file.type === 'text/plain') {
        onFileSelect(file);
      } else {
        alert('Please select a PBN (.pbn) or BWS (.bws) file');
      }
    }
  }, [onFileSelect]);

  const handleFileInput = useCallback((e) => {
    console.log('File input triggered', e.target.files);
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      console.log('Selected file:', file.name, file.type, file.size);
      onFileSelect(file);
    }
  }, [onFileSelect]);

  return (
    <div
      className={`drop-zone ${isDragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pbn,.bws,text/plain"
        onChange={handleFileInput}
        style={{ display: 'none' }}
      />
      {isUploading ? (
        <div className="drop-zone-content">
          <div className="spinner"></div>
          <p>Importing...</p>
        </div>
      ) : pendingBwsData ? (
        <div className="drop-zone-content pending-merge">
          <div className="drop-icon">+</div>
          <p><strong>BWS loaded:</strong> {pendingBwsData.data?.board_count || 0} boards</p>
          <p>Now drop the matching PBN hand record file</p>
          <button
            className="btn-clear-pending"
            onClick={(e) => {
              e.stopPropagation();
              onClearPendingBws();
            }}
          >
            Cancel merge
          </button>
        </div>
      ) : (
        <div className="drop-zone-content">
          <div className="drop-icon">+</div>
          <p>Drop file here or click to browse</p>
          <span className="drop-hint">Supports PBN (hand records) and BWS (ACBLscore results)</span>
          <span className="drop-hint tip">
            Tip: Import BWS first, then PBN to merge contract results with hand records
          </span>
        </div>
      )}
    </div>
  );
};

FileDropZone.propTypes = {
  onFileSelect: PropTypes.func.isRequired,
  isUploading: PropTypes.bool,
  pendingBwsData: PropTypes.object,
  onClearPendingBws: PropTypes.func
};

/**
 * Tournament Card Component
 */
const TournamentCard = ({ tournament, onSelect, onDelete, onAnalyze }) => {
  const statusColors = {
    complete: 'status-complete',
    processing: 'status-ready',
    analyzing: 'status-analyzing',
    failed: 'status-failed'
  };

  // Map internal status to user-friendly display text
  const statusDisplay = {
    complete: 'Analyzed',
    processing: 'Ready',
    analyzing: 'Analyzing...',
    failed: 'Failed'
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown date';
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="tournament-card" onClick={() => onSelect(tournament)}>
      <div className="tournament-header">
        <h4>{tournament.event_name || 'Imported Tournament'}</h4>
        <span className={`status-badge ${statusColors[tournament.import_status] || ''}`}>
          {statusDisplay[tournament.import_status] || tournament.import_status}
        </span>
      </div>

      <div className="tournament-meta">
        <span className="meta-item">
          {formatDate(tournament.event_date)}
        </span>
        <span className="meta-item">
          {tournament.total_hands} hands
        </span>
        {tournament.source && (
          <span className="meta-item source-tag">
            {tournament.source.toUpperCase()}
          </span>
        )}
      </div>

      {tournament.import_status === 'complete' && (
        <div className="tournament-stats">
          <div className="stat">
            <span className="stat-value">
              {tournament.alignment_rate?.toFixed(1) || 0}%
            </span>
            <span className="stat-label">Aligned</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              {tournament.hands_analyzed || 0}
            </span>
            <span className="stat-label">Analyzed</span>
          </div>
          {tournament.total_potential_savings > 0 && (
            <div className="stat savings">
              <span className="stat-value">
                +{tournament.total_potential_savings}
              </span>
              <span className="stat-label">Potential</span>
            </div>
          )}
        </div>
      )}

      <div className="tournament-actions">
        {tournament.import_status === 'processing' && (
          <button
            className="btn-analyze"
            onClick={(e) => {
              e.stopPropagation();
              onAnalyze(tournament.id);
            }}
            title="Compare tournament bids against V3 engine"
          >
            Analyze Bids
          </button>
        )}
        <button
          className="btn-delete"
          onClick={(e) => {
            e.stopPropagation();
            if (window.confirm('Delete this tournament and all imported hands?')) {
              onDelete(tournament.id);
            }
          }}
        >
          Delete
        </button>
      </div>
    </div>
  );
};

TournamentCard.propTypes = {
  tournament: PropTypes.object.isRequired,
  onSelect: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onAnalyze: PropTypes.func.isRequired
};

/**
 * Hand List Item Component
 */
const HandListItem = ({ hand, onSelect }) => {
  const getCategoryColor = (category) => {
    const colors = {
      lucky_overbid: 'category-lucky',
      penalty_trap: 'category-penalty',
      logic_aligned: 'category-aligned',
      rule_violation: 'category-violation'
    };
    return colors[category] || '';
  };

  return (
    <div className="hand-list-item" onClick={() => onSelect(hand)}>
      <div className="hand-board">
        Board {hand.board_number}
      </div>
      <div className="hand-contract">
        {hand.contract_level}{hand.contract_strain}
        {hand.contract_doubled > 0 && 'X'.repeat(hand.contract_doubled)}
      </div>
      <div className="hand-score">
        {hand.score_ns > 0 ? '+' : ''}{hand.score_ns}
      </div>
      {hand.audit_category && (
        <div className={`hand-category ${getCategoryColor(hand.audit_category)}`}>
          {hand.audit_category.replace('_', ' ')}
        </div>
      )}
      {hand.is_falsified === 1 && (
        <span className="falsified-badge" title="Tournament beat engine logic">!</span>
      )}
    </div>
  );
};

HandListItem.propTypes = {
  hand: PropTypes.object.isRequired,
  onSelect: PropTypes.func.isRequired
};

/**
 * Main ACBL Import Modal Component
 */
const ACBLImportModal = ({ isOpen, onClose, userId, onHandSelect }) => {
  const [view, setView] = useState('list'); // 'list', 'tournament', 'hand'
  const [tournaments, setTournaments] = useState([]);
  const [selectedTournament, setSelectedTournament] = useState(null);
  const [tournamentHands, setTournamentHands] = useState([]);
  const [selectedHand, setSelectedHand] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  // Track pending BWS data for merging with next PBN import
  const [pendingBwsData, setPendingBwsData] = useState(null);

  // Load tournaments on mount
  useEffect(() => {
    if (isOpen && userId) {
      loadTournaments();
    }
  }, [isOpen, userId]);

  const loadTournaments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE}/api/tournaments?user_id=${userId}&limit=50`
      );
      const data = await response.json();
      if (data.tournaments) {
        setTournaments(data.tournaments);
      }
    } catch (err) {
      setError('Failed to load tournaments');
      console.error('Load tournaments error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = async (file) => {
    console.log('handleFileSelect called with:', file.name);
    setIsUploading(true);
    setError(null);

    const filename = file.name.toLowerCase();
    const isBwsFile = filename.endsWith('.bws');
    console.log('File type detection:', { filename, isBwsFile });

    try {
      let response;
      let data;

      if (isBwsFile) {
        console.log('Processing BWS file...');
        // BWS files are binary - use FormData for upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);

        response = await fetch(`${API_BASE}/api/import/bws`, {
          method: 'POST',
          body: formData
        });

        data = await response.json();

        if (!response.ok) {
          // Check for mdbtools not installed
          if (response.status === 501) {
            throw new Error(data.message || 'BWS parsing requires mdbtools (server configuration needed)');
          }
          throw new Error(data.error || 'BWS import failed');
        }

        // Store BWS data for merging with PBN
        setPendingBwsData({
          filename: file.name,
          data: data,
          file: file  // Keep original file for merge endpoint
        });

        // Prompt user to also import PBN
        alert(`BWS file loaded: ${data.board_count} boards, ${data.contract_count} contracts.\n\nNow import the matching PBN hand record file to see full analysis with DDS comparison.`);

      } else {
        // PBN files are text - read and send as JSON
        const content = await file.text();

        // Check if we have pending BWS data to merge
        if (pendingBwsData) {
          console.log('Merging with pending BWS data...');
          // Use merge endpoint
          const formData = new FormData();
          formData.append('pbn_file', new Blob([content], { type: 'text/plain' }), file.name);
          formData.append('bws_file', pendingBwsData.file);
          formData.append('user_id', userId);

          response = await fetch(`${API_BASE}/api/import/merge`, {
            method: 'POST',
            body: formData
          });

          data = await response.json();

          if (!response.ok) {
            throw new Error(data.error || 'Merge failed');
          }

          // Clear pending BWS data
          setPendingBwsData(null);

          // Show merge success
          alert(`Merged ${data.boards_merged} boards with ${data.total_contracts} contract results.\n\nDDS analysis available: ${data.has_dds_data ? 'Yes' : 'No'}`);
        } else {
          // Standard PBN import
          response = await fetch(`${API_BASE}/api/import/pbn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              pbn_content: content,
              filename: file.name
            })
          });

          data = await response.json();

          if (!response.ok) {
            throw new Error(data.error || 'PBN import failed');
          }

          // Show success message for PBN
          const hasDds = data.has_dds_data;
          alert(`Imported ${data.valid_hands} hands from "${data.event_name || file.name}"${hasDds ? ' with DDS analysis' : ''}`);
        }
      }

      // Refresh tournament list
      await loadTournaments();

    } catch (err) {
      setError(err.message);
      console.error('Import error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectTournament = async (tournament) => {
    setSelectedTournament(tournament);
    setView('tournament');
    setIsLoading(true);

    try {
      // Load tournament hands
      const response = await fetch(
        `${API_BASE}/api/tournaments/${tournament.id}/hands?user_id=${userId}&limit=100`
      );
      const data = await response.json();
      if (data.hands) {
        setTournamentHands(data.hands);
      }
    } catch (err) {
      setError('Failed to load hands');
      console.error('Load hands error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeTournament = async (tournamentId) => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/tournaments/${tournamentId}/analyze`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ hero_position: 'S' })
        }
      );
      const data = await response.json();

      if (data.status === 'complete') {
        alert(`Analysis complete! ${data.hands_analyzed} hands analyzed.`);
        await loadTournaments();
      }
    } catch (err) {
      setError('Analysis failed');
      console.error('Analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteTournament = async (tournamentId) => {
    try {
      await fetch(
        `${API_BASE}/api/tournaments/${tournamentId}?user_id=${userId}`,
        { method: 'DELETE' }
      );
      await loadTournaments();
    } catch (err) {
      setError('Delete failed');
      console.error('Delete error:', err);
    }
  };

  const handleSelectHand = (hand) => {
    setSelectedHand(hand);
    setView('hand');
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedTournament(null);
    setTournamentHands([]);
  };

  const handleBackToTournament = () => {
    setView('tournament');
    setSelectedHand(null);
  };

  if (!isOpen) return null;

  return (
    <div className="acbl-modal-overlay" onClick={onClose}>
      <div className="acbl-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="acbl-modal-header">
          <h2>
            {view === 'list' && 'ACBL Tournament Import'}
            {view === 'tournament' && (selectedTournament?.event_name || 'Tournament')}
            {view === 'hand' && `Board ${selectedHand?.board_number}`}
          </h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {/* Navigation breadcrumb */}
        {view !== 'list' && (
          <div className="breadcrumb">
            <button onClick={handleBackToList}>Tournaments</button>
            {view === 'hand' && (
              <>
                <span>/</span>
                <button onClick={handleBackToTournament}>
                  {selectedTournament?.event_name || 'Hands'}
                </button>
              </>
            )}
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)}>&times;</button>
          </div>
        )}

        {/* Main content */}
        <div className="acbl-modal-body">
          {/* Tournament List View */}
          {view === 'list' && (
            <>
              <FileDropZone
                onFileSelect={handleFileSelect}
                isUploading={isUploading}
                pendingBwsData={pendingBwsData}
                onClearPendingBws={() => setPendingBwsData(null)}
              />

              <h3>Imported Tournaments</h3>

              {isLoading ? (
                <div className="loading">Loading...</div>
              ) : tournaments.length === 0 ? (
                <div className="empty-state">
                  <p>No tournaments imported yet.</p>
                  <p>Drop a PBN file above to get started.</p>
                </div>
              ) : (
                <div className="tournament-list">
                  {tournaments.map((t) => (
                    <TournamentCard
                      key={t.id}
                      tournament={t}
                      onSelect={handleSelectTournament}
                      onDelete={handleDeleteTournament}
                      onAnalyze={handleAnalyzeTournament}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Tournament Detail View */}
          {view === 'tournament' && selectedTournament && (
            <>
              {/* Tournament summary */}
              <div className="tournament-summary">
                <div className="summary-stat">
                  <span className="value">{selectedTournament.total_hands}</span>
                  <span className="label">Total Hands</span>
                </div>
                <div className="summary-stat">
                  <span className="value">
                    {selectedTournament.alignment_rate?.toFixed(1) || 0}%
                  </span>
                  <span className="label">Logic Aligned</span>
                </div>
                <div className="summary-stat">
                  <span className="value">
                    {selectedTournament.total_potential_savings || 0}
                  </span>
                  <span className="label">Potential Savings</span>
                </div>
              </div>

              {/* Hand list */}
              <h3>Hands ({tournamentHands.length})</h3>

              {isLoading ? (
                <div className="loading">Loading hands...</div>
              ) : tournamentHands.length === 0 ? (
                <div className="empty-state">No hands found</div>
              ) : (
                <div className="hand-list">
                  {tournamentHands.map((hand) => (
                    <HandListItem
                      key={hand.id}
                      hand={hand}
                      onSelect={handleSelectHand}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Hand Detail View */}
          {view === 'hand' && selectedHand && (
            <div className="hand-detail">
              {/* Tournament vs Engine comparison table */}
              <TournamentComparisonTable
                acblData={{
                  tournament_bid: selectedHand.optimal_bid, // Use actual bid from auction
                  tournament_contract: `${selectedHand.contract_level}${selectedHand.contract_strain}${selectedHand.contract_doubled > 0 ? 'X'.repeat(selectedHand.contract_doubled) : ''}`,
                  tournament_score: selectedHand.score_ns,
                  tournament_tricks: selectedHand.tricks_taken,
                  panic_index: selectedHand.panic_index || 0
                }}
                engineData={{
                  optimal_bid: selectedHand.optimal_bid,
                  theoretical_score: selectedHand.theoretical_score,
                  survival_status: selectedHand.survival_status || 'SAFE',
                  rescue_action: selectedHand.rescue_action,
                  matched_rule: selectedHand.matched_rule,
                  audit_category: selectedHand.audit_category,
                  educational_feedback: selectedHand.educational_feedback,
                  dds_par_score: selectedHand.par_score,
                  dds_par_contract: selectedHand.par_contract,
                  quadrant: selectedHand.quadrant
                }}
                showDDS={true}
              />

              {/* Hand display */}
              {selectedHand.hand_south && (
                <div className="hand-display">
                  <h4>Your Hand (South)</h4>
                  <div className="hand-pbn">{selectedHand.hand_south}</div>
                </div>
              )}

              {/* Auction history */}
              {selectedHand.auction_history && (
                <div className="auction-display">
                  <h4>Auction</h4>
                  <div className="auction-sequence">
                    {Array.isArray(selectedHand.auction_history)
                      ? selectedHand.auction_history.join(' - ')
                      : selectedHand.auction_history}
                  </div>
                </div>
              )}

              {/* View in full analysis button */}
              {onHandSelect && (
                <button
                  className="btn-full-analysis"
                  onClick={() => onHandSelect(selectedHand)}
                >
                  Open Full Hand Review
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

ACBLImportModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  userId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onHandSelect: PropTypes.func
};

export default ACBLImportModal;
