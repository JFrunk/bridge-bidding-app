/**
 * Unit tests for HandAnalysis component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import HandAnalysis from '../components/HandAnalysis';

const samplePoints = {
  hcp: 15,
  dist_points: 2,
  total_points: 17,
  suit_hcp: {
    '♠': 4,
    '♥': 3,
    '♦': 5,
    '♣': 3
  },
  suit_lengths: {
    '♠': 5,
    '♥': 3,
    '♦': 3,
    '♣': 2
  }
};

describe('HandAnalysis Component', () => {
  it('renders null when points is null', () => {
    const { container } = render(<HandAnalysis points={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('displays HCP and distribution points', () => {
    render(<HandAnalysis points={samplePoints} />);

    // Check for HCP, dist points, and total
    expect(screen.getByText(/HCP:/)).toBeInTheDocument();
    expect(screen.getByText(/Dist:/)).toBeInTheDocument();
    expect(screen.getByText(/Total: 17/)).toBeInTheDocument();
  });

  it('displays vulnerability when provided', () => {
    render(<HandAnalysis points={samplePoints} vulnerability="NS" />);
    expect(screen.getByText(/NS/)).toBeInTheDocument();
  });

  it('shows suit breakdown with HCP and lengths', () => {
    render(<HandAnalysis points={samplePoints} />);

    // Check that suit HCP and lengths are displayed
    expect(screen.getByText(/4 pts \(5\)/)).toBeInTheDocument(); // Spades
    expect(screen.getByText(/3 pts \(3\)/)).toBeInTheDocument(); // Hearts
    expect(screen.getByText(/5 pts \(3\)/)).toBeInTheDocument(); // Diamonds
    expect(screen.getByText(/3 pts \(2\)/)).toBeInTheDocument(); // Clubs
  });

  it('renders compact view correctly', () => {
    render(<HandAnalysis points={samplePoints} compact={true} />);

    // Should show HCP prominently
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('HCP')).toBeInTheDocument();

    // Should not show detailed suit breakdown in compact mode
    expect(screen.queryByText(/pts \(/)).not.toBeInTheDocument();
  });

  it('shows distribution points in compact view', () => {
    render(<HandAnalysis points={samplePoints} compact={true} />);

    // Should show +2 for distribution
    expect(screen.getByText(/\+2/)).toBeInTheDocument();
  });

  it('does not show distribution in compact view when zero', () => {
    const pointsNoDistribution = { ...samplePoints, dist_points: 0 };
    render(<HandAnalysis points={pointsNoDistribution} compact={true} />);

    expect(screen.queryByText(/\+/)).not.toBeInTheDocument();
  });
});
