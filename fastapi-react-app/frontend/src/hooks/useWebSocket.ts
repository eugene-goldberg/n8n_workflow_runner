import { useEffect, useState, useCallback, useRef } from 'react';

export interface Message {
  id: string;
  type: 'user' | 'bot' | 'system' | 'acknowledgment' | 'error';
  content: string;
  timestamp: string;
  correlationId?: string;
}

interface WebSocketHook {
  messages: Message[];
  sendMessage: (message: string) => void;
  isConnected: boolean;
  connectionError: string | null;
  clearMessages: () => void;
}

export const useWebSocket = (userId: string): WebSocketHook => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const addUserMessage = useCallback((content: string) => {
    addMessage({
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date().toISOString()
    });
  }, [addMessage]);

  const addSystemMessage = useCallback((content: string) => {
    addMessage({
      id: `system-${Date.now()}`,
      type: 'system',
      content,
      timestamp: new Date().toISOString()
    });
  }, [addMessage]);

  const connect = useCallback(() => {
    try {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
      const fullUrl = `${wsUrl}/${userId}`;
      
      console.log('Connecting to WebSocket:', fullUrl);
      ws.current = new WebSocket(fullUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        
        // Set up ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received message:', data);
          
          switch (data.type) {
            case 'system':
              addSystemMessage(data.message);
              break;
              
            case 'acknowledgment':
              addMessage({
                id: `ack-${Date.now()}`,
                type: 'acknowledgment',
                content: data.message,
                timestamp: data.timestamp,
                correlationId: data.correlation_id
              });
              break;
              
            case 'chat_response':
              addMessage({
                id: `bot-${Date.now()}`,
                type: 'bot',
                content: data.message,
                timestamp: data.timestamp,
                correlationId: data.correlation_id
              });
              break;
              
            case 'error':
              addMessage({
                id: `error-${Date.now()}`,
                type: 'error',
                content: data.message,
                timestamp: data.timestamp,
                correlationId: data.correlation_id
              });
              break;
              
            case 'pong':
              // Ignore pong responses
              break;
              
            default:
              console.warn('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Connection error occurred');
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        // Attempt to reconnect after 3 seconds
        if (!reconnectTimeoutRef.current) {
          addSystemMessage('Disconnected from server. Reconnecting...');
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setConnectionError('Failed to create connection');
    }
  }, [userId, addSystemMessage]);

  useEffect(() => {
    connect();

    return () => {
      // Clear intervals
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      // Close WebSocket
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      // Add user message to chat immediately
      addUserMessage(message);
      
      // Send to server
      ws.current.send(JSON.stringify({
        type: 'chat_message',
        message: message
      }));
    } else {
      setConnectionError('Not connected to server');
    }
  }, [addUserMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    sendMessage,
    isConnected,
    connectionError,
    clearMessages
  };
};