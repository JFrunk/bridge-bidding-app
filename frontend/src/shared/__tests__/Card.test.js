/**
 * Unit tests for Card component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Card from '../components/Card';

describe('Card Component', () => {
  it('renders card with rank and suit', () => {
    render(<Card rank="A" suit="♠" />);

    // Should show rank 'A'
    const ranks = screen.getAllByText('A');
    expect(ranks.length).toBeGreaterThan(0);

    // Should show spade symbol
    const suits = screen.getAllByText('♠');
    expect(suits.length).toBeGreaterThan(0);
  });

  it('converts Ten rank to 10', () => {
    render(<Card rank="T" suit="♥" />);

    const ranks = screen.getAllByText('10');
    expect(ranks.length).toBeGreaterThan(0);
  });

  it('applies red color for hearts and diamonds', () => {
    const { container } = render(<Card rank="K" suit="♥" />);
    const redElements = container.getElementsByClassName('suit-red');
    expect(redElements.length).toBeGreaterThan(0);
  });

  it('applies black color for spades and clubs', () => {
    const { container } = render(<Card rank="Q" suit="♠" />);
    const blackElements = container.getElementsByClassName('suit-black');
    expect(blackElements.length).toBeGreaterThan(0);
  });

  it('calls onClick when selectable and clicked', () => {
    const handleClick = jest.fn();
    const { container } = render(<Card rank="J" suit="♦" selectable={true} onClick={handleClick} />);

    const card = container.querySelector('.card');
    fireEvent.click(card);

    expect(handleClick).toHaveBeenCalledWith({ rank: 'J', suit: '♦' });
  });

  it('does not call onClick when not selectable', () => {
    const handleClick = jest.fn();
    const { container } = render(<Card rank="9" suit="♣" selectable={false} onClick={handleClick} />);

    const card = container.querySelector('.card');
    fireEvent.click(card);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies selected class when selected', () => {
    const { container } = render(<Card rank="A" suit="♠" selected={true} />);
    const card = container.querySelector('.card-selected');
    expect(card).toBeInTheDocument();
  });

  it('applies selectable class when selectable', () => {
    const { container } = render(<Card rank="K" suit="♥" selectable={true} />);
    const card = container.querySelector('.card-selectable');
    expect(card).toBeInTheDocument();
  });
});
