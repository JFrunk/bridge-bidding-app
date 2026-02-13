/**
 * RoomContext - State management for Team Practice Lobby
 *
 * Provides room state and actions for two human partners playing together
 * against AI opponents.
 *
 * Usage:
 *   import { RoomProvider, useRoom } from './contexts/RoomContext';
 *
 *   // In App.js:
 *   <RoomProvider>
 *     <App />
 *   </RoomProvider>
 *
 *   // In components:
 *   const { roomCode, isHost, myPosition, createRoom, joinRoom } = useRoom();
 */

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { getSessionHeaders, fetchWithSession } from '../utils/sessionHelper';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Default context values
const RoomContext = createContext({
  // Room state
  roomCode: null,
  isHost: false,
  myPosition: 'S',
  partnerConnected: false,
  gamePhase: 'waiting',
  roomVersion: 0,
  isMyTurn: false,
  inRoom: false,

  // Room data
  roomData: null,
  myHand: null,
  auction: [],
  dealer: 'N',
  vulnerability: 'None',
  currentBidder: null,

  // Play state (shared for room play sync)
  playState: null,

  // Settings
  settings: {
    deal_type: 'random',
    convention_filter: null,
    ai_difficulty: 'advanced',
  },

  // Actions
  createRoom: async () => {},
  joinRoom: async () => {},
  leaveRoom: async () => {},
  updateSettings: async () => {},
  dealHands: async () => {},
  pollRoom: async () => {},
  startRoomPlay: async () => {},
  playRoomCard: async () => {},

  // Polling control
  startPolling: () => {},
  stopPolling: () => {},
  isPolling: false,

  // Error state
  error: null,
  clearError: () => {},
});

export function RoomProvider({ children }) {
  // Room state
  const [roomCode, setRoomCode] = useState(null);
  const [isHost, setIsHost] = useState(false);
  const [myPosition, setMyPosition] = useState('S');
  const [partnerConnected, setPartnerConnected] = useState(false);
  const [gamePhase, setGamePhase] = useState('waiting');
  const [roomVersion, setRoomVersion] = useState(0);
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [inRoom, setInRoom] = useState(false);

  // Room data
  const [roomData, setRoomData] = useState(null);
  const [myHand, setMyHand] = useState(null);
  const [auction, setAuction] = useState([]);
  const [dealer, setDealer] = useState('N');
  const [vulnerability, setVulnerability] = useState('None');
  const [currentBidder, setCurrentBidder] = useState(null);

  // Play state (shared for room play sync)
  const [playState, setPlayState] = useState(null);

  // Settings
  const [settings, setSettings] = useState({
    deal_type: 'random',
    convention_filter: null,
    ai_difficulty: 'advanced',
  });

  // Polling state
  const [isPolling, setIsPolling] = useState(false);
  const pollIntervalRef = useRef(null);

  // Error state
  const [error, setError] = useState(null);

  const clearError = useCallback(() => setError(null), []);

  // Update room state from API response
  const updateFromRoomData = useCallback((data) => {
    if (!data || !data.room) return;

    const room = data.room;
    setRoomData(room);
    setRoomCode(room.room_code);
    setIsHost(room.is_host);
    setMyPosition(room.my_position || 'S');
    setPartnerConnected(room.partner_connected);
    setGamePhase(room.game_phase);
    setRoomVersion(room.version);
    setIsMyTurn(room.is_my_turn);
    setInRoom(true);

    if (room.my_hand) {
      setMyHand(room.my_hand);
    }
    if (room.auction_history) {
      setAuction(room.auction_history);
    }
    if (room.dealer) {
      setDealer(room.dealer);
    }
    if (room.vulnerability) {
      setVulnerability(room.vulnerability);
    }
    if (room.current_bidder) {
      setCurrentBidder(room.current_bidder);
    }
    if (room.settings) {
      setSettings(room.settings);
    }
    // Update play state if present
    if (room.play_state) {
      setPlayState(room.play_state);
    } else if (room.game_phase !== 'playing') {
      setPlayState(null);
    }
  }, []);

  // Create a new room
  const createRoom = useCallback(async (roomSettings = {}) => {
    try {
      const response = await fetchWithSession(`${API_URL}/api/room/create`, {
        method: 'POST',
        body: JSON.stringify(roomSettings),
      });

      const data = await response.json();

      if (data.success) {
        setRoomCode(data.room_code);
        setIsHost(true);
        setMyPosition('S');
        setInRoom(true);
        setGamePhase('waiting');
        setPartnerConnected(false);
        setError(null);

        // Start polling for partner
        startPolling();

        return { success: true, roomCode: data.room_code };
      } else {
        setError(data.error || 'Failed to create room');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, []);

  // Join an existing room
  const joinRoom = useCallback(async (code) => {
    try {
      const response = await fetchWithSession(`${API_URL}/api/room/join`, {
        method: 'POST',
        body: JSON.stringify({ room_code: code }),
      });

      const data = await response.json();

      if (data.success) {
        setRoomCode(data.room_code);
        setIsHost(false);
        setMyPosition('N');
        setInRoom(true);
        setGamePhase('waiting');
        setPartnerConnected(true); // Host is already there
        setError(null);

        // Start polling for game state
        startPolling();

        return { success: true, roomCode: data.room_code };
      } else {
        setError(data.error || 'Failed to join room');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, []);

  // Leave current room
  const leaveRoom = useCallback(async () => {
    stopPolling();

    try {
      await fetchWithSession(`${API_URL}/api/room/leave`, {
        method: 'POST',
      });
    } catch (err) {
      console.warn('Error leaving room:', err);
    }

    // Reset all room state
    setRoomCode(null);
    setIsHost(false);
    setMyPosition('S');
    setPartnerConnected(false);
    setGamePhase('waiting');
    setRoomVersion(0);
    setIsMyTurn(false);
    setInRoom(false);
    setRoomData(null);
    setMyHand(null);
    setAuction([]);
    setDealer('N');
    setVulnerability('None');
    setCurrentBidder(null);
    setPlayState(null);
    setError(null);
  }, []);

  // Update room settings (host only)
  const updateSettings = useCallback(async (newSettings) => {
    if (!isHost) {
      setError('Only host can change settings');
      return { success: false, error: 'Only host can change settings' };
    }

    try {
      const response = await fetchWithSession(`${API_URL}/api/room/settings`, {
        method: 'POST',
        body: JSON.stringify(newSettings),
      });

      const data = await response.json();

      if (data.success) {
        setSettings(data.settings);
        setRoomVersion(data.version);
        return { success: true };
      } else {
        setError(data.error || 'Failed to update settings');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [isHost]);

  // Deal new hands (host only)
  const dealHands = useCallback(async (options = {}) => {
    if (!isHost) {
      setError('Only host can deal');
      return { success: false, error: 'Only host can deal' };
    }

    try {
      const response = await fetchWithSession(`${API_URL}/api/room/deal`, {
        method: 'POST',
        body: JSON.stringify(options),
      });

      const data = await response.json();

      if (data.success) {
        setMyHand(data.my_hand);
        setDealer(data.dealer);
        setVulnerability(data.vulnerability);
        setGamePhase(data.game_phase);
        setCurrentBidder(data.current_bidder);
        setIsMyTurn(data.is_my_turn);
        setRoomVersion(data.version);
        setAuction([]);
        return { success: true, data };
      } else {
        setError(data.error || 'Failed to deal');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [isHost]);

  // Submit a bid in room mode
  const submitBid = useCallback(async (bid) => {
    if (!inRoom) {
      return { success: false, error: 'Not in a room' };
    }

    if (!isMyTurn) {
      return { success: false, error: 'Not your turn' };
    }

    try {
      const response = await fetchWithSession(`${API_URL}/api/room/bid`, {
        method: 'POST',
        body: JSON.stringify({ bid }),
      });

      const data = await response.json();

      if (data.success) {
        setAuction(data.auction_history);
        setCurrentBidder(data.current_bidder);
        setIsMyTurn(data.is_my_turn);
        setGamePhase(data.game_phase);
        setRoomVersion(data.version);
        return { success: true, data };
      } else {
        setError(data.error || 'Failed to submit bid');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [inRoom, isMyTurn]);

  // Start play phase (host only) - transitions from bidding complete to playing
  const startRoomPlay = useCallback(async () => {
    if (!inRoom) {
      return { success: false, error: 'Not in a room' };
    }

    if (!isHost) {
      return { success: false, error: 'Only host can start play' };
    }

    try {
      const response = await fetchWithSession(`${API_URL}/api/room/start-play`, {
        method: 'POST',
      });

      const data = await response.json();

      if (data.success) {
        setGamePhase('playing');
        setIsMyTurn(data.is_my_turn);
        setRoomVersion(data.version);
        // Play state will be updated via next poll
        return { success: true, data };
      } else {
        setError(data.error || 'Failed to start play');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [inRoom, isHost]);

  // Play a card in room mode
  const playRoomCard = useCallback(async (card) => {
    if (!inRoom) {
      return { success: false, error: 'Not in a room' };
    }

    if (!isMyTurn) {
      return { success: false, error: 'Not your turn' };
    }

    try {
      const response = await fetchWithSession(`${API_URL}/api/room/play-card`, {
        method: 'POST',
        body: JSON.stringify({ card }),
      });

      const data = await response.json();

      if (data.success) {
        setIsMyTurn(data.is_my_turn);
        setGamePhase(data.game_phase);
        setRoomVersion(data.version);
        // Play state will be updated via next poll
        return { success: true, data };
      } else {
        setError(data.error || 'Failed to play card');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [inRoom, isMyTurn]);

  // Poll room state
  const pollRoom = useCallback(async () => {
    if (!inRoom) return { success: false };

    try {
      const url = new URL(`${API_URL}/api/room/poll`);
      if (roomVersion > 0) {
        url.searchParams.set('version', roomVersion.toString());
      }

      const response = await fetch(url.toString(), {
        headers: getSessionHeaders(),
      });

      // 304 Not Modified - no changes
      if (response.status === 304) {
        // Clear any previous error on successful poll
        if (error) setError(null);
        return { success: true, unchanged: true };
      }

      if (!response.ok) {
        if (response.status === 404) {
          // Room not found - show reconnect option instead of auto-leaving
          // This allows user to reconnect after server restart
          setError('Room connection lost (404). Click Reconnect to try again.');
          return { success: false, error: 'Room connection lost' };
        }
        throw new Error(`Poll failed: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        // Clear any previous error on successful poll
        if (error) setError(null);
        updateFromRoomData(data);
        return { success: true, data };
      } else {
        if (!data.in_room) {
          // Room explicitly closed by host or expired
          setError('Room has been closed.');
          return { success: false, error: 'Room closed' };
        }
        return { success: false, error: data.error };
      }
    } catch (err) {
      console.warn('Poll error:', err);
      setError(`Connection error: ${err.message}`);
      return { success: false, error: err.message };
    }
  }, [inRoom, roomVersion, updateFromRoomData, error]);

  // Start polling
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return; // Already polling

    setIsPolling(true);
    pollIntervalRef.current = setInterval(() => {
      pollRoom();
    }, 1000); // Poll every 1 second
  }, [pollRoom]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Check room status on mount
  useEffect(() => {
    const checkRoomStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/room/status`, {
          headers: getSessionHeaders(),
        });

        if (response.ok) {
          const data = await response.json();
          if (data.in_room) {
            setRoomCode(data.room_code);
            setIsHost(data.is_host);
            setMyPosition(data.my_position);
            setPartnerConnected(data.partner_connected);
            setGamePhase(data.game_phase);
            setRoomVersion(data.version);
            setInRoom(true);

            // Resume polling
            startPolling();
          }
        }
      } catch (err) {
        console.warn('Could not check room status:', err);
      }
    };

    checkRoomStatus();

    // Cleanup polling on unmount
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  const value = {
    // Room state
    roomCode,
    isHost,
    myPosition,
    partnerConnected,
    gamePhase,
    roomVersion,
    isMyTurn,
    inRoom,

    // Room data
    roomData,
    myHand,
    auction,
    dealer,
    vulnerability,
    currentBidder,

    // Play state
    playState,

    // Settings
    settings,

    // Actions
    createRoom,
    joinRoom,
    leaveRoom,
    updateSettings,
    dealHands,
    submitBid,
    startRoomPlay,
    playRoomCard,
    pollRoom,

    // Polling control
    startPolling,
    stopPolling,
    isPolling,

    // Error state
    error,
    clearError,
  };

  return (
    <RoomContext.Provider value={value}>
      {children}
    </RoomContext.Provider>
  );
}

export function useRoom() {
  const context = useContext(RoomContext);
  if (!context) {
    throw new Error('useRoom must be used within a RoomProvider');
  }
  return context;
}

export default RoomContext;
