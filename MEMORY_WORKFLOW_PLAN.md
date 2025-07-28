# Intent Routing Workflow with Memory - Implementation Plan

## Overview
This plan outlines the implementation of conversation memory in the intent routing workflow to enable context-aware intent classification and improved user experience.

## Phase 1: Create Copy with Memory Configuration

### 1.1 File Creation
- Create `n8n-intent-routing-workflow-with-memory.json`
- Base on existing `n8n-intent-routing-workflow.json`
- Preserve all nodes and connections

### 1.2 Memory Integration
- Add **Buffer Memory** node for conversation history
- Position between OpenAI Model and Evaluate User Intent
- Configure for per-user memory storage

### 1.3 Memory Configuration
```javascript
// Memory settings
{
  memoryKey: "{{ $json.user_id }}",  // Per-user memory
  windowSize: 10,                     // Last 10 messages
  sessionTTL: 3600,                   // 1 hour session timeout
  includeSystemMessages: true
}
```

## Phase 2: Enhanced Agent Configuration

### 2.1 Updated System Message
```
You are an intent classification assistant with memory of past interactions.

IMPORTANT: Consider the conversation history when classifying intent:
- If user references previous issues (e.g., "my previous issue", "as I mentioned"), check history
- If user says "same problem" or "still not working", relate to past tickets
- Track issue evolution (e.g., technical issue → complaint if unresolved)
- Remember user patterns and preferences

You MUST output a JSON object with this structure:
{
  "intent": "one of: TECHNICAL_SUPPORT, BILLING_QUESTION, FEATURE_REQUEST, GENERAL_INQUIRY, COMPLAINT",
  "confidence": 0.0-1.0,
  "entities": ["list of key entities mentioned"],
  "urgency": "LOW, MEDIUM, HIGH",
  "suggestedAction": "brief description of recommended action",
  "contextFromHistory": "relevant past context if any",
  "relatedTickets": ["list of related ticket IDs from history"],
  "isFollowUp": true/false,
  "escalationReason": "if escalating, explain why"
}
```

### 2.2 Enhanced Routing Logic
Update the Switch node expression to consider follow-ups and escalations:
```javascript
const intent = $json.intent;
const urgency = $json.urgency;
const isFollowUp = $json.isFollowUp;

// Escalate follow-up issues
if (isFollowUp && urgency === 'HIGH') {
  return 5; // Executive escalation
}

// Escalate repeated complaints
if (intent === 'COMPLAINT' && $json.relatedTickets?.length > 2) {
  return 5; // Pattern of complaints
}

// Standard routing...
```

## Phase 3: Demonstration Scenarios

### 3.1 Issue Evolution Scenario
```
User: "I can't log into my account"
Agent: TECHNICAL_SUPPORT → Creates TECH-12345
Memory: Stores login issue

User: "It's still not working"
Agent: TECHNICAL_SUPPORT (HIGH urgency)
- contextFromHistory: "Previous login issue reported"
- relatedTickets: ["TECH-12345"]
- isFollowUp: true

User: "This is ridiculous, I've been trying for hours!"
Agent: COMPLAINT (escalated)
- contextFromHistory: "Unresolved login issue from TECH-12345"
- escalationReason: "Technical issue unresolved, user frustrated"
```

### 3.2 Context Awareness Scenario
```
User: "What's my account balance?"
Agent: BILLING_QUESTION → Returns balance
Memory: Stores billing inquiry

User: "Why is it so high?"
Agent: BILLING_QUESTION
- contextFromHistory: "User inquired about balance"
- Understands "it" refers to previously mentioned balance
```

### 3.3 Pattern Recognition Scenario
```
After 5+ login issues over time:
Agent: TECHNICAL_SUPPORT (HIGH urgency)
- contextFromHistory: "Recurring login issues detected"
- suggestedAction: "Escalate to senior tech for permanent solution"
- relatedTickets: ["TECH-001", "TECH-045", "TECH-089", ...]
```

## Phase 4: Implementation Benefits

### 4.1 User Experience
- **Reduced Repetition**: No need to re-explain issues
- **Faster Resolution**: Context speeds up support
- **Personalization**: Tailored responses based on history

### 4.2 Operational Benefits
- **Better Routing**: Historical context improves accuracy
- **Automatic Escalation**: Patterns trigger escalation
- **Metrics Tracking**: Identify recurring issues

### 4.3 Advanced Features
- **Cross-Intent Tracking**: Technical → Billing correlations
- **Sentiment Evolution**: Track user satisfaction over time
- **Proactive Support**: Suggest solutions before asked

## Phase 5: Testing Strategy

### 5.1 Test Cases
1. Single session continuity
2. Multi-session memory (same user, different times)
3. Memory expiration after timeout
4. Different users isolation
5. Escalation triggers

### 5.2 Memory Validation
- Verify correct ticket references
- Check context accuracy
- Ensure memory doesn't leak between users
- Test memory size limits

## Implementation Checklist

- [ ] Copy workflow file
- [ ] Add Buffer Memory node
- [ ] Connect memory to agent
- [ ] Update system message
- [ ] Enhance routing logic
- [ ] Update handler nodes for context
- [ ] Test all scenarios
- [ ] Document memory behavior
- [ ] Create user guide