# PostgreSQL Memory Integration Fix

## Key Issues Fixed

1. **Session Key Configuration**: The Postgres Chat Memory node now correctly uses `{{ $json.user_id }}` from the Process Message node, not from Send Callback
2. **Proper Node Connections**: Memory nodes are connected in the correct sequence
3. **Complete Memory Loop**: Added both user message and AI response storage

## Workflow Architecture

```
Webhook → Process Message → Chat Memory Insert User → Chat Memory Retrieve → AI Agent → Routing
                                         ↓                    ↓                           ↓
                                  Postgres Memory ←───────────┴───────────────────────────┘
                                                              (via Chat Memory Insert AI)
```

## Critical Configuration Points

### 1. Postgres Chat Memory Node
- **Session ID**: Define below
- **Key**: `{{ $json.user_id }}` (from Process Message flow)
- **Table Name**: `chat_sessions`
- **Context Window**: 10

### 2. Chat Memory Insert User
- Stores the user message immediately after processing
- Message: `{{ $json.user_message }}`

### 3. Chat Memory Retrieve
- Retrieves conversation history before AI agent processes
- Passes full context to the agent

### 4. Chat Memory Insert AI
- Stores AI response after routing handlers
- Message: `{{ $json.response_message }}`

## Testing Follow-up Detection

1. First message:
```bash
curl -X POST https://n8n.srv928466.hstgr.cloud/webhook/ai-chat-webhook \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "message": "I cannot login", "correlation_id": "test-001"}'
```

2. Follow-up message:
```bash
curl -X POST https://n8n.srv928466.hstgr.cloud/webhook/ai-chat-webhook \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "message": "I am still unable to login", "correlation_id": "test-002"}'
```

Expected: Second message should have `isFollowUp: true`

## Import Instructions

1. In n8n, go to Workflows
2. Click "Import"
3. Select `n8n-intent-routing-postgres-memory-fixed.json`
4. Configure PostgreSQL credentials:
   - Host: `172.18.0.4` (or your PostgreSQL container IP)
   - Database: `chat_memory`
   - User: `n8n_memory`
   - Password: `your_secure_password`
5. Activate the workflow

## Debugging Tips

- Check PostgreSQL data:
```bash
docker exec -it n8n_postgres_memory psql -U n8n_memory -d chat_memory \
  -c "SELECT * FROM chat_sessions WHERE session_id = 'test-user' ORDER BY id DESC LIMIT 4;"
```

- The AI agent system prompt includes explicit follow-up detection rules
- The agent now outputs `conversationHistory` to show what it sees from memory