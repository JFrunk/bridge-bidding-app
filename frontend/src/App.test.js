/**
 * App.test.js - Unit tests for main App component
 *
 * Tests cover basic rendering and core UI elements.
 * Note: App requires authentication context and shows login for unauthenticated users.
 */

import { render } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  test('renders bridge app without crashing', () => {
    const { container } = render(<App />);
    // The app should render without crashing
    // Check for the main app container
    const appElement = container.querySelector('.app-container');
    expect(appElement).toBeInTheDocument();
  });

  test('renders in initial state successfully', () => {
    // This test verifies the app mounts successfully
    const { container } = render(<App />);
    expect(container).toBeTruthy();
    // Container should have content
    expect(container.firstChild).toBeTruthy();
  });

  test('app container is present in DOM', () => {
    const { container } = render(<App />);
    // The app-container class should be present
    expect(container.querySelector('.app-container')).toBeTruthy();
  });
});
