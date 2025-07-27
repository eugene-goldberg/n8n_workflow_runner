# AI Workflows Guide

This guide explains the different AI-powered n8n workflows available and how to use them.

## Available AI Workflows

### 1. Basic Chat Workflow
**File**: `n8n-ai-chat-workflow-working.json`
- Simulated responses for testing
- No AI service required
- Good for testing the infrastructure

### 2. OpenAI Integration Workflow
**File**: `n8n-ai-chat-workflow-with-agent.json`
- Uses OpenAI ChatGPT for responses
- Requires OpenAI API credentials
- Configurable model and parameters

**Key Components**:
- **AI Agent Node**: OpenAI chat completion
- **Format AI Response**: Extracts and formats the AI response
- Supports multiple response formats

### 3. Intent Evaluation Workflow
**File**: `n8n-intent-evaluation-fixed.json`
- Uses LangChain agent for intent analysis
- Returns structured JSON with intent classification
- Ideal for routing or understanding user requests

### 4. Intent-Based Routing Workflow
**File**: `n8n-intent-routing-workflow.json`
- Complete intent classification and routing system
- Expression-based Switch node with 6 outputs
- Specialized handlers for each intent type
- Priority escalation for urgent complaints

**Intent Types Handled**:
- TECHNICAL_SUPPORT (Output 0)
- BILLING_QUESTION (Output 1)
- FEATURE_REQUEST (Output 2)
- COMPLAINT (Output 3)
- GENERAL_INQUIRY (Output 4) - Fallback
- URGENT COMPLAINT (Output 5) - High priority escalation

**Output Format**:
```json
{
  "intent": "the primary intent",
  "confidence": 0.0-1.0,
  "entities": [],
  "suggestedAction": "what to do next"
}
```

## Key Technical Requirements

### LangChain Agent Configuration
LangChain agents require specific field names:
- Input must include `chatInput` field
- Prompt parameter: `{{ $json.chatInput }}`

### Process Message Node Updates
```javascript
return [{
  json: {
    chatInput: userMessage,  // Required for LangChain
    correlation_id: correlationId,
    user_id: userId,
    user_message: userMessage,
    callback_url: callbackUrl
  }
}];
```

### Format AI Response Handling
Different AI services return responses in different formats:
```javascript
// Handle various response formats
const aiMessage = 
  aiResponse.choices?.[0]?.message?.content ||  // OpenAI
  aiResponse.text ||                             // LangChain
  aiResponse.output ||                           // Other agents
  aiResponse.response ||                         // Generic
  "No response from AI";
```

## Setting Up AI Services

### OpenAI
1. Get API key from https://platform.openai.com
2. In n8n, add OpenAI credentials
3. Select model (gpt-3.5-turbo, gpt-4, etc.)
4. Configure temperature and max tokens

### LangChain
1. Add OpenAI credentials (used by LangChain)
2. Configure system message for specific behavior
3. Enable output parser if needed
4. Set fallback model if required

## Troubleshooting

### "No prompt specified" Error
- Ensure `chatInput` field is in the data
- Check prompt parameter in agent node
- Verify data flow between nodes

### Empty AI Responses
- Check API credentials
- Verify model availability
- Check rate limits
- Review error logs in n8n execution

### Callback Failures
- Ensure callback_payload is properly formatted
- Verify callback URL is accessible
- Check correlation_id tracking

## Best Practices

1. **Error Handling**: Add try-catch blocks in Format nodes
2. **Logging**: Use console.log for debugging
3. **Timeouts**: Configure appropriate timeouts for AI calls
4. **Rate Limiting**: Implement rate limiting for production
5. **Cost Management**: Monitor API usage and costs

## Example Use Cases

### Customer Support Bot
Use intent evaluation to route queries:
- Technical issues → Support workflow
- Billing questions → Finance workflow
- General queries → FAQ workflow

### Content Generation
Use OpenAI integration for:
- Email drafts
- Documentation
- Code suggestions
- Creative writing

### Data Analysis
Combine with other n8n nodes:
- Extract data → AI analysis → Store results
- Monitor trends → AI insights → Send alerts