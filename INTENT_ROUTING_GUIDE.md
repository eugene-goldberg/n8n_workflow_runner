# Intent-Based Routing Guide

This guide explains how to implement and use the intent-based routing workflow in n8n.

## Overview

The intent-based routing workflow uses AI to classify user messages and automatically route them to appropriate handlers based on the detected intent.

## Workflow Components

### 1. Intent Classification
Uses OpenAI GPT-4 to analyze messages and classify them into:
- **TECHNICAL_SUPPORT**: Login issues, bugs, technical problems
- **BILLING_QUESTION**: Payment, invoices, subscription queries
- **FEATURE_REQUEST**: Suggestions for new features or improvements
- **COMPLAINT**: Negative feedback, service issues
- **GENERAL_INQUIRY**: Everything else (fallback)

### 2. Expression-Based Switch Node
```javascript
const intent = $json.intent;
const urgency = $json.urgency;

// Special handling for high-priority complaints
if (intent === 'COMPLAINT' && urgency === 'HIGH') {
  return 5; // Executive escalation
}

// Standard routing
const intentMap = {
  'TECHNICAL_SUPPORT': 0,
  'BILLING_QUESTION': 1,
  'FEATURE_REQUEST': 2,
  'COMPLAINT': 3
};

return intentMap[intent] ?? 4; // Fallback to general
```

### 3. Specialized Handlers

Each intent type has a dedicated handler that:
- Processes the specific request type
- Takes appropriate actions
- Generates tailored responses
- Creates reference/ticket IDs

## Configuration

### Switch Node Setup
1. Mode: **Expression**
2. Number of Outputs: **6**
3. Output connections:
   - 0 → Technical Support Handler
   - 1 → Billing Handler
   - 2 → Feature Request Handler
   - 3 → Complaint Handler
   - 4 → General Inquiry Handler
   - 5 → Urgent Complaint Handler

### Intent Evaluation Format
```json
{
  "intent": "TECHNICAL_SUPPORT",
  "confidence": 0.95,
  "entities": ["login", "password reset"],
  "urgency": "MEDIUM",
  "suggestedAction": "Reset user password and provide login instructions"
}
```

## Example Responses

### Technical Support
```
We've received your technical support request. A support ticket has been created and our technical team will assist you shortly. 
Your ticket ID is: TECH-1732698234567
```

### Urgent Complaint
```
We take your concern extremely seriously. This has been immediately escalated to our executive team. A senior manager will contact you within 30 minutes. 
Priority Case ID: URGENT-1732698234567
```

## Testing the Workflow

### Test Messages
1. **Technical**: "I can't log into my account"
2. **Billing**: "Why was I charged twice?"
3. **Feature**: "Can you add dark mode?"
4. **Complaint**: "Your service is terrible!" (with HIGH urgency)
5. **General**: "What are your business hours?"

### Expected Routing
- Message 1 → Output 0 (Technical Support)
- Message 2 → Output 1 (Billing)
- Message 3 → Output 2 (Feature Request)
- Message 4 → Output 5 (Urgent Complaint)
- Message 5 → Output 4 (General Inquiry)

## Customization

### Adding New Intent Types
1. Update the AI agent's system message to include the new intent
2. Add the intent to the `intentMap` object
3. Increase the number of outputs if needed
4. Create a new handler node
5. Connect the appropriate output

### Modifying Urgency Logic
The current logic escalates HIGH urgency complaints. You can extend this:
```javascript
// Example: Escalate high-urgency technical issues too
if (urgency === 'HIGH' && 
    (intent === 'COMPLAINT' || intent === 'TECHNICAL_SUPPORT')) {
  return 5; // Escalation path
}
```

## Integration Tips

1. **Ticket Systems**: Replace mock ticket IDs with actual API calls
2. **Notifications**: Add Slack/email notifications for urgent cases
3. **Analytics**: Log intent classifications for insights
4. **Feedback Loop**: Track accuracy and refine classifications

## Troubleshooting

### Common Issues
1. **"Output index not allowed"**: Ensure Number of Outputs matches your expression range
2. **Wrong routing**: Check the intent classification output
3. **Missing handlers**: Verify all outputs are connected to handler nodes

### Debug Tips
- Add console.log in Prepare for Routing node
- Check execution history in n8n
- Test with known intent examples first