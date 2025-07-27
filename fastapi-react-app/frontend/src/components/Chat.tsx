import React, { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import './Chat.css';

interface ChatProps {
  userId: string;
}

export const Chat: React.FC<ChatProps> = ({ userId }) => {
  const [inputMessage, setInputMessage] = useState('');
  const { messages, sendMessage, isConnected, connectionError, clearMessages } = useWebSocket(userId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (inputMessage.trim() && isConnected) {
      sendMessage(inputMessage.trim());
      setInputMessage('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getMessageClassName = (type: string) => {
    switch (type) {
      case 'user':
        return 'message user';
      case 'bot':
        return 'message bot';
      case 'system':
        return 'message system';
      case 'acknowledgment':
        return 'message acknowledgment';
      case 'error':
        return 'message error';
      default:
        return 'message';
    }
  };

  const renderMessageContent = (message: any) => {
    // For bot messages, we could add markdown rendering here
    // For now, just return plain text
    return message.content;
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">
          <h3>AI Assistant</h3>
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Connected' : '● Disconnected'}
          </span>
        </div>
        <button className="clear-button" onClick={clearMessages} title="Clear chat">
          Clear
        </button>
      </div>
      
      {connectionError && (
        <div className="connection-error">
          {connectionError}
        </div>
      )}
      
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Start a conversation with the AI assistant</p>
            <p className="hint">Type your message below and press Enter to send</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={getMessageClassName(message.type)}>
            {message.type === 'user' && (
              <div className="message-header">You</div>
            )}
            {message.type === 'bot' && (
              <div className="message-header">AI Assistant</div>
            )}
            
            <div className="message-content">
              {renderMessageContent(message)}
            </div>
            
            <div className="message-footer">
              <span className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </span>
              {message.correlationId && (
                <span className="correlation-id" title={`ID: ${message.correlationId}`}>
                  •
                </span>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-container">
        <textarea
          ref={textareaRef}
          value={inputMessage}
          onChange={handleTextareaChange}
          onKeyPress={handleKeyPress}
          placeholder={isConnected ? "Type your message..." : "Connecting..."}
          disabled={!isConnected}
          rows={1}
          className="message-input"
        />
        <button 
          onClick={handleSend} 
          disabled={!isConnected || !inputMessage.trim()}
          className="send-button"
        >
          Send
        </button>
      </div>
    </div>
  );
};