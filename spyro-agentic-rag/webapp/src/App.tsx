import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface QueryMetadata {
  agent_type: string;
  model: string;
  execution_time_seconds: number;
  tokens_used?: number;
  cost_usd?: number;
  tools_available: string[];
  session_id?: string;
  timestamp: string;
}

interface QueryResponse {
  query: string;
  answer: string;
  metadata: QueryMetadata;
  request_id: string;
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: QueryMetadata;
  toolsUsed?: string[];
}

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [apiKey] = useState('spyro-secret-key-123'); // In production, this should be securely managed
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    // No WebSocket for now - could be added later for real-time tool updates
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

    try {
      console.log('Sending query to:', `${API_URL}/query`);
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          question: query,
          session_id: sessionId
        }),
      });

      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: QueryResponse = await response.json();
      
      if (!sessionId && data.metadata.session_id) {
        setSessionId(data.metadata.session_id);
      }

      // Extract tool information from the answer (if mentioned)
      const toolsUsed = extractToolsFromAnswer(data.answer);

      const assistantMessage: Message = {
        type: 'assistant',
        content: data.answer,
        timestamp: data.metadata.timestamp,
        metadata: data.metadata,
        toolsUsed: toolsUsed
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

  const extractToolsFromAnswer = (answer: string): string[] => {
    // Simple extraction based on common patterns in responses
    const tools = [];
    if (answer.toLowerCase().includes('graph') || answer.toLowerCase().includes('cypher')) {
      tools.push('GraphQuery');
    }
    if (answer.toLowerCase().includes('vector') || answer.toLowerCase().includes('semantic')) {
      tools.push('VectorSearch');
    }
    if (answer.toLowerCase().includes('hybrid') || answer.toLowerCase().includes('combined')) {
      tools.push('HybridSearch');
    }
    return tools;
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'VectorSearch':
        return '🔍';
      case 'GraphQuery':
        return '🕸️';
      case 'HybridSearch':
        return '🔄';
      default:
        return '⚙️';
    }
  };

  const getToolColor = (toolName: string) => {
    switch (toolName) {
      case 'VectorSearch':
        return '#4CAF50';
      case 'GraphQuery':
        return '#2196F3';
      case 'HybridSearch':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 SpyroSolutions Agentic RAG</h1>
        <p>Autonomous AI agent with intelligent tool selection</p>
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
                {message.toolsUsed && message.toolsUsed.length > 0 && (
                  <div className="tools-used">
                    <h4>Tools Detected:</h4>
                    {message.toolsUsed.map((tool, toolIndex) => (
                      <div 
                        key={toolIndex} 
                        className="tool-item"
                        style={{ borderColor: getToolColor(tool) }}
                      >
                        <span className="tool-icon">{getToolIcon(tool)}</span>
                        <div className="tool-details">
                          <strong>{tool}</strong>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {message.metadata && (
                  <div className="metadata">
                    <small>
                      Model: {message.metadata.model} | 
                      Time: {message.metadata.execution_time_seconds.toFixed(2)}s
                      {message.metadata.tokens_used && ` | Tokens: ${message.metadata.tokens_used}`}
                    </small>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="loading-indicator">
                <div className="spinner"></div>
                <span>Processing your query...</span>
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
            <button onClick={() => setQuery("What features does SpyroCloud include?")}>
              🔍 Vector Search Example
            </button>
            <button onClick={() => setQuery("Which customers have subscriptions over $5M?")}>
              🕸️ Graph Search Example
            </button>
            <button onClick={() => setQuery("Tell me about SpyroAI capabilities")}>
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
              <p>Semantic similarity for conceptual questions</p>
            </div>
            <div className="search-type" style={{ borderColor: '#2196F3' }}>
              <h4>🕸️ Graph Query</h4>
              <p>Direct queries for entities and relationships</p>
            </div>
            <div className="search-type" style={{ borderColor: '#FF9800' }}>
              <h4>🔄 Hybrid Search</h4>
              <p>Product-specific information retrieval</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;