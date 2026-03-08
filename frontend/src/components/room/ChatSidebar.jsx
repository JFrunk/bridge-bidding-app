/**
 * ChatSidebar - Collapsible chat panel for partner practice sessions
 *
 * Freeform text, visible only during active session.
 * Messages delivered via 1s polling (piggybacked on room poll).
 */

import React, { useState, useRef, useEffect } from 'react';
import { useRoom } from '../../contexts/RoomContext';
import './ChatSidebar.css';

export default function ChatSidebar() {
  const { chatMessages, sendChat, myPosition, inRoom } = useRoom();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const lastSeenCount = useRef(0);

  // Auto-open and scroll when a new partner message arrives
  useEffect(() => {
    if (chatMessages.length > lastSeenCount.current) {
      const newMessages = chatMessages.slice(lastSeenCount.current);
      const hasPartnerMessage = newMessages.some(msg => msg.sender !== myPosition);

      if (hasPartnerMessage && !isOpen) {
        setIsOpen(true);
      }

      if (isOpen) {
        // Mark as seen when panel is open
        lastSeenCount.current = chatMessages.length;
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [chatMessages.length, isOpen, myPosition, chatMessages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  if (!inRoom) return null;

  const unreadCount = isOpen ? 0 : Math.max(0, chatMessages.length - lastSeenCount.current);

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    setSending(true);
    const result = await sendChat(input);
    if (result.success) {
      setInput('');
    }
    setSending(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const positionLabel = (pos) => pos === myPosition ? 'You' : 'Partner';

  return (
    <>
      {/* Toggle button */}
      <button
        className={`chat-toggle-btn ${isOpen ? 'open' : ''} ${unreadCount > 0 ? 'has-unread' : ''}`}
        onClick={() => {
          const opening = !isOpen;
          setIsOpen(opening);
          if (opening) {
            lastSeenCount.current = chatMessages.length;
          }
        }}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
        title={isOpen ? 'Close chat' : 'Open chat'}
      >
        Chat
        {unreadCount > 0 && (
          <span className="chat-unread-badge">{unreadCount}</span>
        )}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div className="chat-sidebar">
          <div className="chat-header">
            <span className="chat-title">Chat</span>
            <button className="chat-close-btn" onClick={() => setIsOpen(false)} aria-label="Close chat">
              &times;
            </button>
          </div>

          <div className="chat-messages">
            {chatMessages.length === 0 && (
              <div className="chat-empty">No messages yet. Say hello!</div>
            )}
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-message ${msg.sender === myPosition ? 'mine' : 'theirs'}`}
              >
                <span className="chat-sender">{positionLabel(msg.sender)}</span>
                <span className="chat-text">{msg.text}</span>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-area">
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              maxLength={500}
              disabled={sending}
            />
            <button
              className="chat-send-btn"
              onClick={handleSend}
              disabled={!input.trim() || sending}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}
