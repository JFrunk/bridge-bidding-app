import { useState, useEffect, useCallback } from 'react';

/**
 * useDevMode - Developer mode hook with keyboard shortcut activation
 *
 * Activates with: Ctrl+Shift+D (or Cmd+Shift+D on Mac)
 *
 * Features controlled by dev mode:
 * - AI Review button visibility
 * - AI Difficulty Selector visibility
 * - V2 Schema toggle (experimental bidding engine)
 * - (Extensible: add more features as needed)
 *
 * The mode persists for the current session (sessionStorage)
 * and can also be activated via URL parameter: ?dev=true
 * V2 Schema can be activated via URL parameter: ?v2schema=true
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

  // V2 Schema toggle - separate from dev mode visibility
  const [useV2Schema, setUseV2Schema] = useState(() => {
    const stored = sessionStorage.getItem('bridge-use-v2-schema');
    if (stored === 'true') return true;

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('v2schema') === 'true') {
      sessionStorage.setItem('bridge-use-v2-schema', 'true');
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

  // V2 Schema toggle function
  const toggleV2Schema = useCallback(() => {
    setUseV2Schema(prev => {
      const newValue = !prev;
      if (newValue) {
        sessionStorage.setItem('bridge-use-v2-schema', 'true');
        console.log('🔷 V2 Schema ENABLED - Using experimental bidding engine');
      } else {
        sessionStorage.removeItem('bridge-use-v2-schema');
        console.log('🔶 V2 Schema DISABLED - Using standard bidding engine');
      }
      return newValue;
    });
  }, []);

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

    // V2 Schema controls
    window.toggleV2Schema = toggleV2Schema;
    window.enableV2Schema = () => {
      sessionStorage.setItem('bridge-use-v2-schema', 'true');
      setUseV2Schema(true);
      console.log('🔷 V2 Schema ENABLED');
    };
    window.disableV2Schema = () => {
      sessionStorage.removeItem('bridge-use-v2-schema');
      setUseV2Schema(false);
      console.log('🔶 V2 Schema DISABLED');
    };

    return () => {
      delete window.toggleDevMode;
      delete window.enableDevMode;
      delete window.disableDevMode;
      delete window.toggleV2Schema;
      delete window.enableV2Schema;
      delete window.disableV2Schema;
    };
  }, [toggleDevMode, toggleV2Schema]);

  return {
    isDevMode,
    toggleDevMode,
    useV2Schema,
    toggleV2Schema
  };
}

export default useDevMode;
