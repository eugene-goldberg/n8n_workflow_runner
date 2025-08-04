import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { groundedQuestionsByCategory } from './groundedBusinessQuestions';

interface QueryMetadata {
  agent_type: string;
  model: string;
  execution_time_seconds: number;
  routes_selected: string[];
  tools_used: string[];
  session_id?: string;
  timestamp: string;
  grounded: boolean;
  tokens_used?: number;
  cost_usd?: number;
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
  const [apiKey] = useState('test-key-123'); // In production, this should be securely managed
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

      // Use tools from metadata
      const toolsUsed = data.metadata.tools_used || [];

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
        <p>True agentic AI with multi-strategy retrieval and creative synthesis</p>
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
                      {' | '}
                      Grounded: {message.metadata.grounded ? '✅' : '❌'}
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
          <h3>Verified Business Questions (53 grounded answers - 88.3% success rate)</h3>
          <div className="business-questions-container">
            {Object.entries(groundedQuestionsByCategory).map(([category, subcategories]) => (
              <div key={category} className="question-category">
                <h4 className="category-title">{category}</h4>
                {Object.entries(subcategories).map(([subcategory, questions]) => (
                  <div key={subcategory} className="subcategory">
                    <h5 className="subcategory-title">{subcategory}</h5>
                    <div className="questions-list">
                      {questions.map((question, index) => (
                        <button
                          key={index}
                          className="question-button"
                          onClick={() => setQuery(question)}
                          title={question}
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ))}
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