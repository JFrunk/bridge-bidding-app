/**
 * Unit tests for Card component (Tailwind/Physics v2.0)
 *
 * The Card component uses Tailwind utility classes:
 * - Color: text-suit-red / text-suit-black
 * - Selection: ring-2 ring-amber-500 -translate-y-[0.5em]
 * - Selectable: cursor-pointer + hover:-translate-y-[0.5em]
 * - Rank displayed as-is (no T→10 conversion)
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Card from '../components/Card';

describe('Card Component', () => {
  it('renders card with rank and suit', () => {
    const { container } = render(<Card rank="A" suit="♠" />);

    // Should render rank text
    expect(container.textContent).toContain('A');
    // Should render suit symbol
    expect(container.textContent).toContain('♠');
  });

  it('renders Ten rank as T (no conversion)', () => {
    const { container } = render(<Card rank="T" suit="♥" />);

    // Card displays rank as-is
    expect(container.textContent).toContain('T');
  });

  it('applies red color for hearts and diamonds', () => {
    const { container: heartsContainer } = render(<Card rank="K" suit="♥" />);
    const redElements = heartsContainer.querySelectorAll('.text-suit-red');
    expect(redElements.length).toBeGreaterThan(0);

    const { container: diamondsContainer } = render(<Card rank="Q" suit="♦" />);
    const redElements2 = diamondsContainer.querySelectorAll('.text-suit-red');
    expect(redElements2.length).toBeGreaterThan(0);
  });

  it('applies black color for spades and clubs', () => {
    const { container: spadesContainer } = render(<Card rank="Q" suit="♠" />);
    const blackElements = spadesContainer.querySelectorAll('.text-suit-black');
    expect(blackElements.length).toBeGreaterThan(0);

    const { container: clubsContainer } = render(<Card rank="J" suit="♣" />);
    const blackElements2 = clubsContainer.querySelectorAll('.text-suit-black');
    expect(blackElements2.length).toBeGreaterThan(0);
  });

  it('calls onClick when selectable and clicked', () => {
    const handleClick = jest.fn();
    const { container } = render(<Card rank="J" suit="♦" selectable={true} onClick={handleClick} />);

    // Card uses role="button" when selectable
    const card = container.querySelector('[role="button"]');
    fireEvent.click(card);

    expect(handleClick).toHaveBeenCalledWith({ rank: 'J', suit: '♦' });
  });

  it('does not call onClick when not selectable', () => {
    const handleClick = jest.fn();
    const { container } = render(<Card rank="9" suit="♣" selectable={false} onClick={handleClick} />);

    // Not selectable — no role="button"
    const card = container.firstChild;
    fireEvent.click(card);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies selected styling when selected', () => {
    const { container } = render(<Card rank="A" suit="♠" selected={true} />);
    const outerDiv = container.firstChild;
    expect(outerDiv.className).toContain('ring-2');
    expect(outerDiv.className).toContain('ring-amber-500');
  });

  it('applies selectable styling when selectable', () => {
    const { container } = render(<Card rank="K" suit="♥" selectable={true} />);
    const outerDiv = container.firstChild;
    expect(outerDiv.className).toContain('cursor-pointer');
  });

  it('renders hidden card back', () => {
    const { container } = render(<Card isHidden={true} />);
    // Hidden card has red-800 background
    const back = container.querySelector('.bg-red-800');
    expect(back).toBeInTheDocument();
  });
});
