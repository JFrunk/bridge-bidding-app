import { useState, useEffect, useCallback } from 'react';

/**
 * useDevMode - Developer mode hook with keyboard shortcut activation
 *
 * Activates with: Ctrl+Shift+D (or Cmd+Shift+D on Mac)
 *
 * Features controlled by dev mode:
 * - AI Review button visibility
 * - AI Difficulty Selector visibility
 * - (Extensible: add more features as needed)
 *
 * The mode persists for the current session (sessionStorage)
 * and can also be activated via URL parameter: ?dev=true
 */
export function useDevMode() {
  const [isDevMode, setIsDevMode] = useState(() => {
    // Check sessionStorage first
    const stored = sessionStorage.getItem('bridge-dev-mode');
    if (stored === 'true') return true;

    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('dev') === 'true') {
      sessionStorage.setItem('bridge-dev-mode', 'true');
      return true;
    }

    return false;
  });

  const toggleDevMode = useCallback(() => {
    setIsDevMode(prev => {
      const newValue = !prev;
      if (newValue) {
        sessionStorage.setItem('bridge-dev-mode', 'true');
        console.log('🔧 Dev mode ENABLED - Developer tools visible');
      } else {
        sessionStorage.removeItem('bridge-dev-mode');
        console.log('🔧 Dev mode DISABLED - Developer tools hidden');
      }
      return newValue;
    });
  }, []);

  // Keyboard shortcut: Ctrl+Shift+D (or Cmd+Shift+D on Mac)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        toggleDevMode();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleDevMode]);

  // Also expose a global function for console access
  useEffect(() => {
    window.toggleDevMode = toggleDevMode;
    window.enableDevMode = () => {
      sessionStorage.setItem('bridge-dev-mode', 'true');
      setIsDevMode(true);
      console.log('🔧 Dev mode ENABLED');
    };
    window.disableDevMode = () => {
      sessionStorage.removeItem('bridge-dev-mode');
      setIsDevMode(false);
      console.log('🔧 Dev mode DISABLED');
    };

    return () => {
      delete window.toggleDevMode;
      delete window.enableDevMode;
      delete window.disableDevMode;
    };
  }, [toggleDevMode]);

  return {
    isDevMode,
    toggleDevMode
  };
}

export default useDevMode;
