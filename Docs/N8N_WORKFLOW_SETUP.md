# n8n AI Chat Workflow Setup Guide

## Overview
This guide explains how to set up the n8n workflow for the AI chat system with proper data handling and callback configuration.

## Key Configuration Points

### 1. Webhook Data Access
In n8n, webhook POST data is nested in the body property:
```javascript
const webhookData = items[0].json.body;
```

### 2. Docker Network Configuration
Since n8n runs in Docker, use the Docker bridge network address:
```
http://172.17.0.1:8000
```

### 3. Callback Payload Preparation
Prepare the complete callback payload in the Code node to avoid template evaluation issues:
```javascript
const callbackPayload = {
  correlation_id: correlationId,
  user_id: userId,
  result: `${response}\n\n**Analysis:**\n- Message length: ${analysis.messageLength} characters`
};
```

## Workflow Components

### Webhook Trigger Node
- **HTTP Method**: POST
- **Path**: ai-chat-webhook
- **Response Mode**: Response Node

### Process Message Code Node
```javascript
// Get webhook data
const items = $input.all();
const webhookData = items[0].json.body;

// Extract values
const userMessage = webhookData.message || "No message provided";
const correlationId = webhookData.correlation_id || "no-correlation-id";
const userId = webhookData.user_id || "anonymous";
const callbackUrl = webhookData.callback_url || "";

// Process and prepare callback
const callbackPayload = {
  correlation_id: correlationId,
  user_id: userId,
  result: "Your processed response here"
};

// Return data
return [{
  json: {
    // ... other fields
    callback_payload: callbackPayload
  }
}];
```

### Send Callback HTTP Request Node
- **Method**: POST
- **URL**: `http://172.17.0.1:8000/api/n8n-callback`
- **Headers**: Content-Type: application/json
- **Body**: `{{$json.callback_payload}}`

### Respond to Webhook Node
- **Response Body**: `{{$json.webhook_response}}`

## Common Issues and Solutions

### Issue: Template strings not evaluated
**Solution**: Use expression mode or prepare data in Code node

### Issue: Connection refused to localhost
**Solution**: Use Docker bridge network address 172.17.0.1

### Issue: Correlation ID not found
**Solution**: Ensure callback_payload includes all required fields

### Issue: Webhook data undefined
**Solution**: Access data via `items[0].json.body`

## Testing the Workflow

1. Send a test message through the chat interface
2. Check n8n execution history for any errors
3. Monitor FastAPI logs: `sudo journalctl -u fastapi -f`
4. Verify callback is received with correct correlation_id

## Production Considerations

1. Replace simulated AI response with actual AI service integration
2. Add error handling for AI service failures
3. Implement retry logic for callback failures
4. Add monitoring and alerting for workflow failures