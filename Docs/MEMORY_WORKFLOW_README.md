# Intent Routing with Memory - Setup Guide

## Overview
The memory-enhanced intent routing workflow adds conversation history tracking to the standard intent routing system, enabling:
- Context-aware responses
- Follow-up detection
- Intelligent escalation
- Pattern recognition
- Per-user conversation isolation

## Prerequisites
- n8n instance with LangChain nodes installed
- OpenAI API credentials configured
- FastAPI backend running on accessible network
- Basic understanding of the standard intent routing workflow

## Setup Instructions

### 1. Import the Workflow
1. Open your n8n instance
2. Go to Workflows → Import
3. Import `n8n-intent-routing-workflow-with-memory.json`
4. Save the workflow

### 2. Configure OpenAI Credentials
1. Click on the "OpenAI Chat Model" node
2. Select or create OpenAI credentials
3. Ensure GPT-4-mini or better is selected

### 3. Configure Memory Settings
The Buffer Memory node is pre-configured with:
```javascript
{
  "sessionKey": "={{ $json.user_id }}",  // Uses user_id for isolation
  "contextWindowLength": 10              // Stores last 10 messages
}
```

You can adjust these settings:
- **sessionKey**: Field used to separate user conversations
- **contextWindowLength**: Number of messages to remember (affects cost/performance)

### 4. Update Callback URL
In the HTTP Request node ("Send Callback"):
1. Update the URL to match your FastAPI instance
2. Default: `http://172.17.0.1:8000/api/n8n-callback` (Docker bridge)
3. For external: Use your server's actual address

### 5. Activate the Workflow
1. Toggle the workflow to Active
2. Copy the webhook URL from the Webhook Trigger node
3. Update your FastAPI backend with this URL

## How Memory Works

### Per-User Sessions
Each user gets their own conversation history based on `user_id`:
```json
{
  "user_id": "user-123",
  "message": "I need help with login"
}
```

### Context Window
The system remembers the last 10 messages per user:
- Older messages are automatically removed
- Prevents unlimited memory growth
- Maintains relevant context

### Follow-Up Detection
The AI agent detects when users reference previous issues:
- "It's still not working" → Links to previous technical issue
- "As I mentioned before" → Retrieves relevant context
- "Same problem as yesterday" → Finds related tickets

### Pattern Recognition
Identifies recurring issues:
- Multiple similar complaints → Automatic escalation
- Repeated technical issues → Suggests permanent fix
- Chronic problems → Routes to senior support

## Enhanced Response Format

The workflow returns additional context information:
```json
{
  "intent": "TECHNICAL_SUPPORT",
  "confidence": 0.95,
  "urgency": "HIGH",
  "isFollowUp": true,
  "contextFromHistory": "User reported login issues 3 times this week",
  "relatedTickets": ["TECH-001", "TECH-045"],
  "escalationReason": "Recurring technical issue",
  "suggestedAction": "Escalate to senior tech team"
}
```

## Routing Logic

The enhanced routing considers:
1. **Follow-ups with high urgency** → Executive escalation
2. **Multiple complaints** (3+) → Executive escalation  
3. **Standard routing** → Based on intent type

### Route Outputs
- 0: Technical Support
- 1: Billing Questions
- 2: Feature Requests
- 3: Complaints
- 4: General Inquiries
- 5: Executive Escalation (HIGH PRIORITY)

## Testing the Workflow

### Test Script
```bash
# First message
curl -X POST http://your-n8n-webhook-url \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-1",
    "message": "I cannot access my account",
    "correlation_id": "test-001",
    "callback_url": "http://172.17.0.1:8000/api/n8n-callback"
  }'

# Follow-up (shows memory)
sleep 5
curl -X POST http://your-n8n-webhook-url \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-1",
    "message": "Still having the same issue",
    "correlation_id": "test-002",
    "callback_url": "http://172.17.0.1:8000/api/n8n-callback"
  }'
```

### Expected Behavior
1. First message creates a new support ticket
2. Second message recognizes it as a follow-up
3. System links both messages together
4. Urgency may increase based on persistence

## Customization Options

### 1. Adjust Memory Window
Increase or decrease based on needs:
- Shorter (5): Faster, less context
- Longer (20): More context, slower

### 2. Modify System Prompt
Update the agent's instructions in "Evaluate User Intent" node to:
- Add new intent types
- Change escalation rules
- Adjust context interpretation

### 3. Custom Escalation Rules
Modify the Switch node expression to add conditions:
```javascript
// Add VIP user escalation
if ($json.user_tier === 'VIP' && $json.urgency !== 'LOW') {
  return 5; // Executive escalation
}
```

### 4. Memory Expiration
Add session timeout by modifying Buffer Memory:
- Set TTL for automatic session expiry
- Clear old sessions periodically

## Performance Considerations

### Response Times
- First message: ~3 seconds
- With memory lookup: ~4 seconds
- Complex patterns: ~5 seconds

### Memory Usage
- Per user: ~2KB for 10 messages
- 1000 active users: ~2MB total
- Scales linearly with users

### Optimization Tips
1. Reduce context window for faster responses
2. Use GPT-3.5 for lower cost (less accurate)
3. Implement caching for frequent queries
4. Monitor memory node performance

## Troubleshooting

### Memory Not Working
- Check Buffer Memory node is connected
- Verify user_id is being passed correctly
- Ensure memory node has correct session key

### Wrong Context Retrieved
- Check if user_id is consistent across requests
- Verify context window size is appropriate
- Look for session key collisions

### Escalation Not Triggering
- Test Switch node expression separately
- Verify output count is set to 6
- Check escalation conditions in logs

### Performance Issues
- Reduce context window size
- Check for memory leaks in n8n
- Monitor API response times

## Best Practices

1. **Consistent User IDs**: Always use the same user_id format
2. **Meaningful Context**: Include relevant details in messages
3. **Test Thoroughly**: Verify memory works before production
4. **Monitor Usage**: Track memory consumption and performance
5. **Regular Cleanup**: Clear old sessions periodically

## Support

For issues or questions:
1. Check n8n execution logs for errors
2. Verify all node connections are correct
3. Test with simple messages first
4. Review the test plan for validation steps

## Next Steps

1. Import and configure the workflow
2. Run test scenarios from the test plan
3. Customize for your specific needs
4. Monitor performance in production
5. Iterate based on user feedback