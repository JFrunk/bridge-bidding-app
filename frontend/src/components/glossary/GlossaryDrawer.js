/**
 * GlossaryDrawer Component
 *
 * A slide-in panel providing searchable access to bridge terminology.
 * Based on best practices from Duolingo, chess apps, and accessibility research.
 *
 * Features:
 * - Search with instant filtering
 * - Category filtering (tabs)
 * - Difficulty level badges
 * - Related terms navigation
 * - Mobile-responsive design
 * - Senior-friendly option with larger text
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './GlossaryDrawer.css';
import {
  glossaryTerms,
  CATEGORIES,
  DIFFICULTY_LEVELS,
  searchTerms,
  getTermsByCategory,
  getRelatedTerms,
  getGlossaryStats,
} from '../../data/bridgeGlossary';

const GlossaryDrawer = ({ isOpen, onClose, initialSearch = '', initialTermId = null, seniorMode = false }) => {
  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTerm, setSelectedTerm] = useState(null);
  const [filteredTerms, setFilteredTerms] = useState(glossaryTerms);
  const searchInputRef = useRef(null);
  const drawerRef = useRef(null);
  const termRefs = useRef({});

  // When drawer opens with an initial term, select and scroll to it
  useEffect(() => {
    if (isOpen && initialTermId) {
      const term = glossaryTerms.find(t => t.id === initialTermId);
      if (term) {
        // Clear search and set category to show the term
        setSearchQuery('');
        setSelectedCategory('all');
        setSelectedTerm(term);

        // Scroll to the term after a brief delay (to let the drawer render)
        setTimeout(() => {
          const termElement = termRefs.current[initialTermId];
          if (termElement) {
            termElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 150);
      }
    }
  }, [isOpen, initialTermId]);

  // Focus search input when drawer opens (only if no initial term)
  useEffect(() => {
    if (isOpen && searchInputRef.current && !initialTermId) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [isOpen, initialTermId]);

  // Handle escape key to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Filter terms based on search and category
  useEffect(() => {
    let results = glossaryTerms;

    // Apply category filter
    if (selectedCategory !== 'all') {
      results = getTermsByCategory(selectedCategory);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const searchResults = searchTerms(searchQuery);
      const searchIds = new Set(searchResults.map(t => t.id));
      results = results.filter(t => searchIds.has(t.id));
    }

    // Sort alphabetically
    results = [...results].sort((a, b) => a.term.localeCompare(b.term));

    setFilteredTerms(results);
  }, [searchQuery, selectedCategory]);

  // Handle term click
  const handleTermClick = useCallback((term) => {
    setSelectedTerm(selectedTerm?.id === term.id ? null : term);
  }, [selectedTerm]);

  // Handle related term click
  const handleRelatedTermClick = useCallback((termId) => {
    const term = glossaryTerms.find(t => t.id === termId);
    if (term) {
      setSelectedTerm(term);
      // Clear search to show term in context
      setSearchQuery('');
      setSelectedCategory(term.category);
    }
  }, []);

  // Get stats for display
  const stats = getGlossaryStats();

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="glossary-backdrop"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={`glossary-drawer ${seniorMode ? 'senior-mode' : ''}`}
        role="dialog"
        aria-label="Bridge Glossary"
        aria-modal="true"
      >
        {/* Header */}
        <div className="glossary-header">
          <div className="glossary-title-row">
            <h2>Bridge Glossary</h2>
            <button
              className="close-button"
              onClick={onClose}
              aria-label="Close glossary"
            >
              ×
            </button>
          </div>
          <p className="glossary-subtitle">
            {stats.total} terms to help you learn bridge
          </p>
        </div>

        {/* Search */}
        <div className="glossary-search">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search terms..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              aria-label="Search glossary terms"
            />
            {searchQuery && (
              <button
                className="clear-search"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search"
              >
                ×
              </button>
            )}
          </div>
        </div>

        {/* Category Tabs */}
        <div className="category-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={selectedCategory === 'all'}
            className={`category-tab ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            All ({stats.total})
          </button>
          {Object.entries(CATEGORIES).map(([key, category]) => (
            <button
              key={key}
              role="tab"
              aria-selected={selectedCategory === key}
              className={`category-tab ${selectedCategory === key ? 'active' : ''}`}
              onClick={() => setSelectedCategory(key)}
              title={category.description}
            >
              <span className="category-icon">{category.icon}</span>
              <span className="category-name">{category.name}</span>
            </button>
          ))}
        </div>

        {/* Results Count */}
        <div className="results-info">
          {filteredTerms.length === 0 ? (
            <span className="no-results">No terms found for "{searchQuery}"</span>
          ) : (
            <span>{filteredTerms.length} term{filteredTerms.length !== 1 ? 's' : ''}</span>
          )}
        </div>

        {/* Terms List */}
        <div className="terms-list" role="list">
          {filteredTerms.map((term) => (
            <div
              key={term.id}
              ref={(el) => { termRefs.current[term.id] = el; }}
              className={`term-item ${selectedTerm?.id === term.id ? 'expanded' : ''}`}
              role="listitem"
            >
              {/* Term Header - Always visible */}
              <button
                className="term-header"
                onClick={() => handleTermClick(term)}
                aria-expanded={selectedTerm?.id === term.id}
              >
                <div className="term-title-row">
                  <span className="term-name">{term.term}</span>
                  <span
                    className={`difficulty-badge ${term.difficulty}`}
                    title={DIFFICULTY_LEVELS[term.difficulty].description}
                  >
                    {DIFFICULTY_LEVELS[term.difficulty].label}
                  </span>
                </div>
                <span className="expand-icon">
                  {selectedTerm?.id === term.id ? '−' : '+'}
                </span>
              </button>

              {/* Expanded Content */}
              {selectedTerm?.id === term.id && (
                <div className="term-content">
                  <p className="term-definition">{term.definition}</p>

                  {term.example && (
                    <div className="term-example">
                      <span className="example-label">Example:</span>
                      <span className="example-text">{term.example}</span>
                    </div>
                  )}

                  {term.relatedTerms && term.relatedTerms.length > 0 && (
                    <div className="related-terms">
                      <span className="related-label">Related:</span>
                      <div className="related-links">
                        {getRelatedTerms(term.id).map((related) => (
                          <button
                            key={related.id}
                            className="related-link"
                            onClick={() => handleRelatedTermClick(related.id)}
                          >
                            {related.term}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="term-category">
                    <span className="category-chip">
                      {CATEGORIES[term.category]?.icon} {CATEGORIES[term.category]?.name}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Difficulty Legend (at bottom) */}
        <div className="difficulty-legend">
          <span className="legend-title">Difficulty:</span>
          {Object.entries(DIFFICULTY_LEVELS).map(([key, level]) => (
            <span key={key} className={`legend-item ${key}`}>
              <span className="legend-dot"></span>
              {level.label}
            </span>
          ))}
        </div>
      </div>
    </>
  );
};

export default GlossaryDrawer;
