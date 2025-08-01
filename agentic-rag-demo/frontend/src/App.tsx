import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Tool {
  name: string;
  purpose: string;
  query: string;
  call_id?: string;
}

interface RAGResponse {
  success: boolean;
  answer: string;
  session_id: string;
  timestamp: string;
  metadata: {
    search_type: string;
    response_time_ms?: number;
    tools_used_count: number;
  };
  tools_used: Tool[];
  sources?: any[];
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tools?: Tool[];
  metadata?: any;
}

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeTools, setActiveTools] = useState<Tool[]>([]);
  const [searchVisualization, setSearchVisualization] = useState<any>(null);
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  useEffect(() => {
    // Connect to WebSocket
    ws.current = new WebSocket(`ws://localhost:8001/ws`);
    
    ws.current.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'tool_used':
          setActiveTools(prev => [...prev, data.tool]);
          break;
        case 'response_complete':
          setActiveTools([]);
          break;
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.current?.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage: Message = {
      type: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setActiveTools([]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: RAGResponse = await response.json();
      
      if (!sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMessage: Message = {
        type: 'assistant',
        content: data.answer,
        timestamp: data.timestamp,
        tools: data.tools_used,
        metadata: data.metadata
      };

      setMessages(prev => [...prev, assistantMessage]);
      setQuery('');

    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'vector_search':
        return '🔍';
      case 'graph_search':
        return '🕸️';
      case 'hybrid_search':
        return '🔄';
      default:
        return '⚙️';
    }
  };

  const getToolColor = (toolName: string) => {
    switch (toolName) {
      case 'vector_search':
        return '#4CAF50';
      case 'graph_search':
        return '#2196F3';
      case 'hybrid_search':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Agentic RAG Demo - SpyroSolutions</h1>
        <p>Visual demonstration of hybrid search with tool transparency</p>
      </header>

      <div className="container">
        <div className="chat-section">
          <div className="messages-container">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.type}`}>
                <div className="message-header">
                  <span className="message-type">
                    {message.type === 'user' ? '👤 You' : '🤖 AI Assistant'}
                  </span>
                  <span className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-content">
                  {message.content}
                </div>
                {message.tools && message.tools.length > 0 && (
                  <div className="tools-used">
                    <h4>Tools Used:</h4>
                    {message.tools.map((tool, toolIndex) => (
                      <div 
                        key={toolIndex} 
                        className="tool-item"
                        style={{ borderColor: getToolColor(tool.name) }}
                      >
                        <span className="tool-icon">{getToolIcon(tool.name)}</span>
                        <div className="tool-details">
                          <strong>{tool.name}</strong>
                          <p>{tool.purpose}</p>
                          <code>{tool.query}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {message.metadata && (
                  <div className="metadata">
                    <small>
                      Search Type: {message.metadata.search_type} | 
                      Tools Used: {message.metadata.tools_used_count}
                    </small>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="loading-indicator">
                <div className="spinner"></div>
                <span>Processing your query...</span>
                {activeTools.length > 0 && (
                  <div className="active-tools">
                    <h4>Currently using:</h4>
                    {activeTools.map((tool, index) => (
                      <div key={index} className="active-tool">
                        {getToolIcon(tool.name)} {tool.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about SpyroSolutions customers, products, or risks..."
              disabled={loading}
              className="query-input"
            />
            <button type="submit" disabled={loading || !query.trim()}>
              Send
            </button>
          </form>
        </div>

        <div className="info-section">
          <h3>Example Queries</h3>
          <div className="example-queries">
            <button onClick={() => setQuery("What features does SpyroAnalytics include?")}>
              🔍 Vector Search Example
            </button>
            <button onClick={() => setQuery("Which products does Disney use and what risks do they have?")}>
              🕸️ Graph Search Example
            </button>
            <button onClick={() => setQuery("Show me all Enterprise tier customers and their risk scores")}>
              🔄 Hybrid Search Example
            </button>
          </div>

          <h3>How It Works</h3>
          <div className="how-it-works">
            <div className="step">
              <span className="step-number">1</span>
              <p>Your query is analyzed by the AI agent</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <p>Appropriate search tools are selected automatically</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <p>Results are synthesized into a comprehensive answer</p>
            </div>
          </div>

          <h3>Search Types</h3>
          <div className="search-types">
            <div className="search-type" style={{ borderColor: '#4CAF50' }}>
              <h4>🔍 Vector Search</h4>
              <p>Semantic similarity search for concepts and descriptions</p>
            </div>
            <div className="search-type" style={{ borderColor: '#2196F3' }}>
              <h4>🕸️ Graph Search</h4>
              <p>Relationship traversal for connected entities</p>
            </div>
            <div className="search-type" style={{ borderColor: '#FF9800' }}>
              <h4>🔄 Hybrid Search</h4>
              <p>Combines both methods for comprehensive results</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;