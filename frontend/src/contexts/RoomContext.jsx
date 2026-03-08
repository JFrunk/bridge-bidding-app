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

  // Coaching support
  beliefs: null,

  // Settings
  settings: {
    deal_type: 'random',
    convention_filter: null,
    ai_difficulty: 'advanced',
  },

  // Readiness (peer model)
  iAmReady: false,
  partnerReady: false,
  bothReady: false,

  // Chat
  chatMessages: [],

  // Disconnect detection
  partnerDisconnected: false,

  // Actions
  createRoom: async () => {},
  joinRoom: async () => {},
  leaveRoom: async () => {},
  updateSettings: async () => {},
  dealHands: async () => {},
  setReady: async () => {},
  setUnready: async () => {},
  sendChat: async () => {},
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
  const [partnerHand, setPartnerHand] = useState(null);
  const [partnerPosition, setPartnerPosition] = useState(null);
  const [auction, setAuction] = useState([]);
  const [dealer, setDealer] = useState('N');
  const [vulnerability, setVulnerability] = useState('None');
  const [currentBidder, setCurrentBidder] = useState(null);

  // Play state (shared for room play sync)
  const [playState, setPlayState] = useState(null);

  // Coaching support
  const [beliefs, setBeliefs] = useState(null);

  // Settings
  const [settings, setSettings] = useState({
    deal_type: 'random',
    convention_filter: null,
    ai_difficulty: 'advanced',
  });

  // Readiness state (peer model)
  const [iAmReady, setIAmReady] = useState(false);
  const [partnerReady, setPartnerReady] = useState(false);
  const [bothReady, setBothReady] = useState(false);

  // Chat state (ephemeral — session lifetime only)
  const [chatMessages, setChatMessages] = useState([]);

  // Partner disconnect detection
  const [partnerDisconnected, setPartnerDisconnected] = useState(false);

  // Polling state
  const [isPolling, setIsPolling] = useState(false);
  const pollIntervalRef = useRef(null);
  const pollRoomRef = useRef(null);

  // Error state
  const [error, setError] = useState(null);

  const clearError = useCallback(() => setError(null), []);

  // Track version with ref to prevent stale polls from overwriting fresher data
  const roomVersionRef = useRef(0);

  // Update room state from API response (poll or direct action)
  const updateFromRoomData = useCallback((data) => {
    if (!data || !data.room) return;

    const room = data.room;

    // Reject stale poll responses: if we already have a newer version,
    // skip this update to prevent race conditions (e.g., in-flight poll
    // returning old state after a ready/bid response already set newer state)
    if (room.version < roomVersionRef.current) {
      return;
    }
    roomVersionRef.current = room.version;

    setRoomData(room);
    setRoomCode(room.room_code);
    setIsHost(room.is_host);
    if (room.my_position) {
      setMyPosition(prev => {
        if (prev !== room.my_position) {
          console.log('Mapping User:', room.is_host ? 'Host' : 'Guest', 'my_position:', room.my_position, 'was:', prev);
        }
        return room.my_position;
      });
    }
    setPartnerConnected(room.partner_connected);
    setGamePhase(room.game_phase);
    setRoomVersion(room.version);
    setIsMyTurn(room.is_my_turn);
    setInRoom(true);

    if (room.my_hand) {
      setMyHand(room.my_hand);
    }
    // Hand review: partner's hand revealed when auction complete
    if (room.partner_hand) {
      setPartnerHand(room.partner_hand);
      setPartnerPosition(room.partner_position || null);
    } else if (room.game_phase === 'bidding' || room.game_phase === 'waiting') {
      setPartnerHand(null);
      setPartnerPosition(null);
    }
    if (room.auction_history !== undefined) {
      setAuction(room.auction_history);
    }
    if (room.dealer) {
      setDealer(room.dealer);
    }
    if (room.vulnerability) {
      setVulnerability(room.vulnerability);
    }
    // Clear currentBidder when not present (e.g., auction complete)
    setCurrentBidder(room.current_bidder || null);
    if (room.settings) {
      setSettings(room.settings);
    }
    // Update play state if present
    if (room.play_state) {
      setPlayState(room.play_state);
    } else if (room.game_phase !== 'playing') {
      setPlayState(null);
    }
    // Update beliefs for coaching support
    if (room.beliefs) {
      setBeliefs(room.beliefs);
    } else if (room.game_phase !== 'bidding') {
      setBeliefs(null);
    }
    // Update readiness state
    if (room.i_am_ready !== undefined) setIAmReady(room.i_am_ready);
    if (room.partner_ready !== undefined) setPartnerReady(room.partner_ready);
    if (room.both_ready !== undefined) setBothReady(room.both_ready);
    // Update chat messages
    if (room.chat_messages) setChatMessages(room.chat_messages);
    if (room.partner_disconnected !== undefined) setPartnerDisconnected(room.partner_disconnected);
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
    roomVersionRef.current = 0;
    setIsMyTurn(false);
    setInRoom(false);
    setRoomData(null);
    setMyHand(null);
    setPartnerHand(null);
    setPartnerPosition(null);
    setAuction([]);
    setDealer('N');
    setVulnerability('None');
    setCurrentBidder(null);
    setPlayState(null);
    setBeliefs(null);
    setIAmReady(false);
    setPartnerReady(false);
    setBothReady(false);
    setChatMessages([]);
    setError(null);
  }, []);

  // Update room settings (either peer)
  const updateSettings = useCallback(async (newSettings) => {
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

  // Signal readiness for next hand (peer model - either player can call)
  const setReady = useCallback(async () => {
    try {
      const response = await fetchWithSession(`${API_URL}/api/room/ready`, {
        method: 'POST',
        body: JSON.stringify({ ready: true }),
      });

      const data = await response.json();

      if (data.success) {
        setIAmReady(data.i_am_ready);
        setPartnerReady(data.partner_ready);
        setBothReady(data.both_ready);

        // If deal happened (both were ready), update game state
        if (data.action_taken === 'deal') {
          setMyHand(data.my_hand);
          setDealer(data.dealer);
          setVulnerability(data.vulnerability);
          setGamePhase(data.game_phase);
          setCurrentBidder(data.current_bidder);
          setIsMyTurn(data.is_my_turn);
          setRoomVersion(data.version);
          roomVersionRef.current = data.version; // Prevent stale polls from overwriting
          // Use auction from response (may include AI auto-bids after deal)
          setAuction(data.auction_history || []);
        }
        return { success: true, data };
      } else {
        setError(data.error || 'Failed to set ready');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Network error';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, []);

  // Retract readiness
  const setUnready = useCallback(async () => {
    try {
      const response = await fetchWithSession(`${API_URL}/api/room/unready`, {
        method: 'POST',
      });
      const data = await response.json();
      if (data.success) {
        setIAmReady(false);
        setPartnerReady(data.partner_ready);
        setBothReady(false);
      }
      return data;
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  // Send chat message
  const sendChat = useCallback(async (text) => {
    if (!text || !text.trim()) return { success: false, error: 'Empty message' };
    try {
      const response = await fetchWithSession(`${API_URL}/api/room/chat`, {
        method: 'POST',
        body: JSON.stringify({ text: text.trim() }),
      });
      const data = await response.json();
      return data;
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  // Deal new hands (either peer can call)
  const dealHands = useCallback(async (options = {}) => {
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
        roomVersionRef.current = data.version; // Prevent stale polls from overwriting
        // Use auction from response (may include AI auto-bids after deal)
        setAuction(data.auction_history || []);
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
        roomVersionRef.current = data.version; // Prevent stale polls from overwriting
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

  // Start play phase (either peer) - transitions from bidding complete to playing
  const startRoomPlay = useCallback(async () => {
    if (!inRoom) {
      return { success: false, error: 'Not in a room' };
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
        // Set play state immediately from response (prevents 304 loop)
        if (data.play_state) {
          setPlayState(data.play_state);
        }
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
  }, [inRoom]);

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

  // Keep ref in sync so setInterval always calls the latest pollRoom
  pollRoomRef.current = pollRoom;

  // Start polling
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return; // Already polling

    setIsPolling(true);
    pollIntervalRef.current = setInterval(() => {
      pollRoomRef.current();
    }, 1000); // Poll every 1 second
  }, []);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Check room status on mount (reconnection after page refresh)
  // Skip if room endpoints aren't registered on the backend yet
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
            if (data.my_position) {
              setMyPosition(data.my_position);
            }
            setPartnerConnected(data.partner_connected);
            setGamePhase(data.game_phase);
            setRoomVersion(data.version);
            setInRoom(true);

            // Resume polling
            startPolling();
          }
        }
      } catch {
        // Silently ignore -- room endpoints may not be registered
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
    partnerHand,
    partnerPosition,
    auction,
    dealer,
    vulnerability,
    currentBidder,

    // Play state
    playState,

    // Coaching support
    beliefs,

    // Settings
    settings,

    // Readiness (peer model)
    iAmReady,
    partnerReady,
    bothReady,

    // Chat
    chatMessages,

    // Disconnect detection
    partnerDisconnected,

    // Actions
    createRoom,
    joinRoom,
    leaveRoom,
    updateSettings,
    dealHands,
    setReady,
    setUnready,
    sendChat,
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
