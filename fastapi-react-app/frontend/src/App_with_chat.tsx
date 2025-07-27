import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Chat } from './components/Chat';
import './App.css';

interface Item {
  id?: number;
  title: string;
  description: string;
  completed: boolean;
  created_at?: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Generate or retrieve user ID
const getUserId = (): string => {
  let userId = localStorage.getItem('userId');
  if (!userId) {
    userId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('userId', userId);
  }
  return userId;
};

function App() {
  const [items, setItems] = useState<Item[]>([]);
  const [newItem, setNewItem] = useState<Item>({ title: '', description: '', completed: false });
  const [editingItem, setEditingItem] = useState<Item | null>(null);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [workflowResult, setWorkflowResult] = useState<any>(null);
  const [showChat, setShowChat] = useState(false);
  const userId = getUserId();

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/items`);
      setItems(response.data);
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  };

  const createItem = async () => {
    if (!newItem.title || !newItem.description) return;
    
    try {
      await axios.post(`${API_URL}/api/items`, newItem);
      setNewItem({ title: '', description: '', completed: false });
      fetchItems();
    } catch (error) {
      console.error('Error creating item:', error);
    }
  };

  const updateItem = async (item: Item) => {
    if (!item.id) return;
    
    try {
      await axios.put(`${API_URL}/api/items/${item.id}`, item);
      setEditingItem(null);
      fetchItems();
    } catch (error) {
      console.error('Error updating item:', error);
    }
  };

  const deleteItem = async (id: number) => {
    try {
      await axios.delete(`${API_URL}/api/items/${id}`);
      fetchItems();
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const toggleCompleted = async (item: Item) => {
    if (!item.id) return;
    
    try {
      await axios.put(`${API_URL}/api/items/${item.id}`, { ...item, completed: !item.completed });
      fetchItems();
    } catch (error) {
      console.error('Error toggling item:', error);
    }
  };

  const executeWorkflow = async () => {
    setWorkflowLoading(true);
    setWorkflowResult(null);
    
    try {
      const response = await axios.post(`${API_URL}/api/workflow/execute`);
      setWorkflowResult(response.data);
      alert('Workflow executed successfully!');
    } catch (error: any) {
      console.error('Error executing workflow:', error);
      alert(`Failed to execute workflow: ${error.response?.data?.detail || error.message}`);
    } finally {
      setWorkflowLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FastAPI + React Todo App with AI Chat</h1>
        
        <div className="app-controls">
          <button 
            className="chat-toggle-button"
            onClick={() => setShowChat(!showChat)}
          >
            {showChat ? '💬 Hide AI Chat' : '💬 Open AI Chat'}
          </button>
          
          <div className="workflow-section">
            <button 
              className="workflow-button"
              onClick={executeWorkflow}
              disabled={workflowLoading}
            >
              {workflowLoading ? 'Executing...' : 'Execute Workflow'}
            </button>
          </div>
        </div>

        {showChat && (
          <div className="chat-wrapper">
            <Chat userId={userId} />
          </div>
        )}
        
        <div className="todo-section">
          <div className="add-item-form">
            <input
              type="text"
              placeholder="Title"
              value={newItem.title}
              onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
            />
            <input
              type="text"
              placeholder="Description"
              value={newItem.description}
              onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
            />
            <button onClick={createItem}>Add Item</button>
          </div>

          <div className="items-list">
            {items.map(item => (
              <div key={item.id} className={`item ${item.completed ? 'completed' : ''}`}>
                {editingItem?.id === item.id && editingItem ? (
                  <div className="editing">
                    <input
                      type="text"
                      value={editingItem.title}
                      onChange={(e) => setEditingItem({ ...editingItem, title: e.target.value })}
                    />
                    <input
                      type="text"
                      value={editingItem.description}
                      onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                    />
                    <button onClick={() => updateItem(editingItem)}>Save</button>
                    <button onClick={() => setEditingItem(null)}>Cancel</button>
                  </div>
                ) : (
                  <>
                    <input
                      type="checkbox"
                      checked={item.completed}
                      onChange={() => toggleCompleted(item)}
                    />
                    <div className="item-content">
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                    </div>
                    <div className="item-actions">
                      <button onClick={() => setEditingItem(item)}>Edit</button>
                      <button onClick={() => item.id && deleteItem(item.id)}>Delete</button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;