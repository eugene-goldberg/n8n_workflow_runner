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
    context_items?: number;
    retriever_type?: string;
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
  use_cypher?: boolean;
}

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeTools, setActiveTools] = useState<Tool[]>([]);
  const [useCypher, setUseCypher] = useState(false);
  const [graphStats, setGraphStats] = useState<any>(null);
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

    // Fetch graph statistics
    fetch(`${API_URL}/graph/stats`)
      .then(res => res.json())
      .then(data => setGraphStats(data))
      .catch(console.error);

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
  }, [API_URL]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage: Message = {
      type: 'user',
      content: query,
      timestamp: new Date().toISOString(),
      use_cypher: useCypher
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
          session_id: sessionId,
          use_cypher: useCypher
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
      case 'fulltext_search':
        return '📝';
      case 'text2cypher':
        return '🔗';
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
      case 'fulltext_search':
        return '#9C27B0';
      case 'text2cypher':
        return '#2196F3';
      case 'hybrid_search':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  const setExampleQuery = (query: string, cypher: boolean = false) => {
    setQuery(query);
    setUseCypher(cypher);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 SpyroSolutions RAG System</h1>
        <p>Hybrid search with neo4j-graphrag-python</p>
        {graphStats && (
          <div className="graph-stats">
            <span>📊 Nodes: {graphStats.total_nodes}</span>
            <span>🔗 Relationships: {graphStats.total_relationships}</span>
          </div>
        )}
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
                          {tool.query && <code>{tool.query}</code>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {message.metadata && (
                  <div className="metadata">
                    <small>
                      Type: {message.metadata.retriever_type || message.metadata.search_type} | 
                      Context Items: {message.metadata.context_items || 0} | 
                      Time: {message.metadata.response_time_ms}ms
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
            <div className="search-type-toggle">
              <label>
                <input
                  type="checkbox"
                  checked={useCypher}
                  onChange={(e) => setUseCypher(e.target.checked)}
                  disabled={loading}
                />
                Use Graph Query (Text2Cypher)
              </label>
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={useCypher ? "Ask about specific entities and relationships..." : "Ask about products, features, or concepts..."}
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
          
          <div className="example-category">
            <h4>🔍 Hybrid Search (Vector + Fulltext)</h4>
            <button onClick={() => setExampleQuery("What products does SpyroSolutions offer?")}>
              Product Overview
            </button>
            <button onClick={() => setExampleQuery("Tell me about the cloud infrastructure platform")}>
              SpyroCloud Details
            </button>
            <button onClick={() => setExampleQuery("What are the security capabilities?")}>
              Security Features
            </button>
          </div>

          <div className="example-category">
            <h4>🔗 Graph Queries (Text2Cypher)</h4>
            <button onClick={() => setExampleQuery("Which customers have which subscription plans and ARR?", true)}>
              Customer Subscriptions
            </button>
            <button onClick={() => setExampleQuery("Show me all teams and their product responsibilities", true)}>
              Team Assignments
            </button>
            <button onClick={() => setExampleQuery("Which customers are at risk and what's their revenue?", true)}>
              Risk Analysis
            </button>
            <button onClick={() => setExampleQuery("What are the operational costs for each project?", true)}>
              Project Costs
            </button>
          </div>

          <h3>How It Works</h3>
          <div className="how-it-works">
            <div className="step">
              <span className="step-number">1</span>
              <p>Choose search type: Hybrid or Graph Query</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <p>Your query is processed by the appropriate retriever</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <p>Results are returned from Neo4j knowledge graph</p>
            </div>
          </div>

          <h3>Search Types</h3>
          <div className="search-types">
            <div className="search-type" style={{ borderColor: '#FF9800' }}>
              <h4>🔄 Hybrid Search</h4>
              <p>Combines vector embeddings and fulltext search</p>
              <p className="small">Best for: Concepts, descriptions, features</p>
            </div>
            <div className="search-type" style={{ borderColor: '#2196F3' }}>
              <h4>🔗 Text2Cypher</h4>
              <p>Converts natural language to graph queries</p>
              <p className="small">Best for: Specific data, relationships, aggregations</p>
            </div>
          </div>

          <h3>SpyroSolutions Data Model</h3>
          <div className="data-model">
            <p><strong>Entities:</strong> Customer, Product, Project, Team, Subscription, Risk</p>
            <p><strong>Key Relationships:</strong> USES, SUBSCRIBES_TO, ASSIGNED_TO, HAS_RISK</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;