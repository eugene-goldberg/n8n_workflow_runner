# Intent Routing with Tools - Knowledge Base Integration

## Overview
This workflow demonstrates how to integrate tools with the AI agent for enhanced intent classification. Specifically, it adds a Knowledge Base Search tool that the agent can use when handling technical support requests.

**Important**: Use the v2 workflow (`n8n-intent-routing-workflow-with-tools-v2.json`) which includes proper JSON output formatting and a Structured Output Parser to ensure reliable agent responses.

## Key Enhancement: Knowledge Base Tool

### What's New
1. **Knowledge Base Search Tool** - A custom code tool that simulates searching a technical knowledge base
2. **Enhanced System Prompt** - Instructs the agent to use the KB tool for technical issues
3. **Improved Response Format** - Includes KB search results in the classification
4. **Smart Solution Delivery** - Provides immediate solutions when available

### Tool Implementation
The Knowledge Base Search tool (`@n8n/n8n-nodes-langchain.toolCode`) contains:
- Simulated KB articles for common issues (password reset, login problems, etc.)
- Search algorithm that scores articles based on relevance
- Returns structured results the agent can use

## How It Works

### 1. User Message Processing
When a user sends a message like "I can't log into my account", the workflow:
1. Extracts the message via webhook
2. Passes it to the AI agent

### 2. Agent with Tool Access
The agent now:
1. Identifies this as a TECHNICAL_SUPPORT intent
2. **Automatically calls the Knowledge Base Search tool**
3. Searches for relevant articles using keywords from the message
4. Includes the search results in its response

### 3. Enhanced Response
The response now includes:
```json
{
  "intent": "TECHNICAL_SUPPORT",
  "confidence": 0.95,
  "entities": ["login", "account"],
  "urgency": "MEDIUM",
  "knowledgeBaseResults": {
    "articlesFound": 2,
    "topArticle": "Login Troubleshooting Guide",
    "solution": "1. Clear browser cache and cookies\n2. Try incognito mode..."
  }
}
```

### 4. Improved User Experience
The technical support handler now:
- Shows the KB solution immediately in the response
- Mentions that "89% of users found this helpful"
- Still creates a ticket if the solution doesn't work

## Example Scenarios

### Scenario 1: Login Issue
**User**: "I can't log in to my account"

**Agent Actions**:
1. Classifies as TECHNICAL_SUPPORT
2. Calls KB Search with query "can't log in account"
3. Finds "Login Troubleshooting Guide"
4. Returns solution in response

**User Sees**:
```
We've received your technical support request.

📚 Suggested Solution from Knowledge Base:
Login Troubleshooting Guide

1. Clear browser cache and cookies
2. Try incognito/private mode
3. Disable browser extensions
4. Check if account is locked
5. Verify correct username/email
6. Contact support if issue persists

This solution has helped 89% of users with similar issues.

If the suggested solution doesn't resolve your issue, our technical team will assist you shortly.
Your ticket ID is: TECH-1234567890
```

### Scenario 2: Password Reset
**User**: "I forgot my password"

**Agent Actions**:
1. Searches KB for "forgot password"
2. Finds "How to Reset Your Password"
3. Provides step-by-step instructions

### Scenario 3: No KB Match
**User**: "The app crashes when I click the blue button"

**Agent Actions**:
1. Searches KB but finds no relevant articles
2. Routes to tech support without KB solution
3. Creates high-priority ticket for uncommon issue

## Benefits of Tool Integration

1. **Immediate Help**: Users get solutions instantly for common issues
2. **Reduced Tickets**: Many issues resolved without human intervention
3. **Better Context**: Support agents see what solutions were already tried
4. **Learning System**: Can track which KB articles are most helpful

## Extending the Tool System

You can add more tools for different intents:

### Billing Intent → Account Balance Tool
```javascript
// Check user's current balance and subscription
const accountData = await checkAccountStatus(userId);
return {
  balance: accountData.balance,
  plan: accountData.subscriptionPlan,
  nextBillingDate: accountData.nextBilling
};
```

### Feature Request → Feature Database Tool
```javascript
// Check if feature already exists or is planned
const featureStatus = await searchFeatureDatabase(request);
return {
  exists: featureStatus.exists,
  planned: featureStatus.inRoadmap,
  alternativeSolution: featureStatus.workaround
};
```

## Implementation in n8n

### Setting Up the Tool
1. Import the workflow JSON (use v2 for best results)
2. The Knowledge Base Search Tool is a Code tool node
3. It's connected to the AI agent via the `ai_tool` connection type
4. The Structured Output Parser ensures JSON formatting
5. The agent automatically has access to call this tool

### Important Configuration Details

#### Tool Requirements
- **Node Name**: Must be alphanumeric only (no spaces or special characters)
- **Tool Name Parameter**: Use "KnowledgeBaseSearch" not "Knowledge Base Search"
- **Output Format**: Must return JSON string using `JSON.stringify()`

#### Agent Configuration
- **Agent Type**: Set to "toolsAgent" explicitly
- **Output Parser**: Must have `hasOutputParser: true`
- **System Prompt**: Must emphasize returning ONLY JSON, no conversational text

### Node Connections
```
Knowledge Base Search Tool --ai_tool--> Evaluate User Intent
Structured Output Parser --ai_outputParser--> Evaluate User Intent
OpenAI Chat Model --ai_languageModel--> Evaluate User Intent
Buffer Memory --ai_memory--> Evaluate User Intent
```

### System Prompt Configuration
The agent's system prompt must be strict:
- "CRITICAL: You MUST ONLY respond with a valid JSON object"
- "DO NOT include any conversational text"
- "REMEMBER: Output ONLY valid JSON, nothing else!"

## Testing the Workflow

1. **Basic Test**: "I need help logging in"
   - Should return KB article about login

2. **Specific Test**: "password reset not working"
   - Should find password reset guide

3. **No Match Test**: "my custom integration is broken"
   - Should route without KB solution

## Production Considerations

### Real KB Integration
Replace the simulated KB with actual API calls:
```javascript
const kbResponse = await fetch('https://api.yourcompany.com/kb/search', {
  method: 'POST',
  body: JSON.stringify({ query: $input.query }),
  headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
});
return await kbResponse.json();
```

### Caching
Consider caching popular KB articles to reduce API calls

### Analytics
Track which KB articles successfully resolve issues

### Continuous Improvement
- Add new KB articles based on unresolved tickets
- Update search algorithm based on user feedback
- Monitor tool usage patterns

## Common Issues and Solutions

### "Value is not a valid alphanumeric string" Error
**Problem**: Node IDs or tool names contain invalid characters
**Solution**: 
- Change node ID to use only letters, numbers, and underscores
- Remove spaces from tool name parameter
- Example: `kb-search-tool` → `kb_search_tool`

### "Wrong output type returned" Error
**Problem**: Tool returning JavaScript object instead of string
**Solution**: Always use `return JSON.stringify(result)` in your tool code

### Agent Returns Conversational Text Instead of JSON
**Problem**: Agent ignoring JSON-only instruction
**Solution**: 
1. Add Structured Output Parser node (required in v2)
2. Use the strict system prompt from v2
3. Set agent type to "toolsAgent"
4. Ensure `hasOutputParser: true` is set

### Routing Always Goes to General Inquiry
**Problem**: Agent's response not being parsed correctly
**Solution**: Check the "Prepare for Routing" node parsing logic matches v2

## Conclusion

This workflow demonstrates how adding tools to AI agents creates more intelligent and helpful automation. The Knowledge Base tool is just one example - you can add any tool that helps the agent better serve your users.

**Remember**: Always use the v2 workflow for production deployments. It has been thoroughly tested and includes all necessary fixes for reliable operation.