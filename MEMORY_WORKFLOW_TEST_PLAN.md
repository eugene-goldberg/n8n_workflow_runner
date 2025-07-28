# Memory-Enhanced Workflow Test Plan

## Overview
This document provides comprehensive test scenarios and procedures for validating the memory-enhanced intent routing workflow.

## Test Setup

### Prerequisites
1. n8n instance running with OpenAI credentials configured
2. FastAPI backend running on http://172.17.0.1:8000
3. Memory workflow imported and activated
4. Test user IDs: `test-user-1`, `test-user-2`, `test-user-3`

### Test Data Structure
```json
{
  "correlation_id": "test-{timestamp}",
  "user_id": "test-user-{number}",
  "message": "{test message}",
  "callback_url": "http://172.17.0.1:8000/api/n8n-callback"
}
```

## Test Scenarios

### Scenario 1: Basic Memory Retention
**Objective**: Verify that the system remembers previous conversations

**Test Steps**:
1. Send initial message:
   ```json
   {
     "user_id": "test-user-1",
     "message": "I can't log into my account"
   }
   ```
   Expected: TECHNICAL_SUPPORT intent, creates ticket TECH-XXX

2. Send follow-up message (within 5 minutes):
   ```json
   {
     "user_id": "test-user-1",
     "message": "It's still not working"
   }
   ```
   Expected: 
   - TECHNICAL_SUPPORT intent
   - `isFollowUp`: true
   - `contextFromHistory`: "Previous login issue reported"
   - `relatedTickets`: ["TECH-XXX"]

**Success Criteria**:
- System recognizes the follow-up
- Previous ticket is referenced
- Context is maintained

### Scenario 2: Issue Escalation
**Objective**: Test automatic escalation based on conversation patterns

**Test Steps**:
1. Initial technical issue:
   ```json
   {
     "user_id": "test-user-2",
     "message": "My password reset isn't working"
   }
   ```
   Expected: TECHNICAL_SUPPORT, normal priority

2. First follow-up (after 10 minutes):
   ```json
   {
     "user_id": "test-user-2",
     "message": "I've tried multiple times, still can't reset"
   }
   ```
   Expected: TECHNICAL_SUPPORT, HIGH urgency, isFollowUp: true

3. Frustration escalation:
   ```json
   {
     "user_id": "test-user-2",
     "message": "This is ridiculous! I've been locked out for hours!"
   }
   ```
   Expected: 
   - Intent changes to COMPLAINT
   - Routes to URGENT escalation (output 5)
   - `escalationReason`: "Technical issue unresolved, user frustrated"
   - All previous tickets referenced

**Success Criteria**:
- Progressive escalation works
- Intent evolution is tracked
- Executive escalation triggered appropriately

### Scenario 3: Context-Aware Responses
**Objective**: Verify the system understands contextual references

**Test Steps**:
1. Billing inquiry:
   ```json
   {
     "user_id": "test-user-3",
     "message": "What's my current account balance?"
   }
   ```
   Expected: BILLING_QUESTION

2. Contextual follow-up:
   ```json
   {
     "user_id": "test-user-3",
     "message": "Why is it so high?"
   }
   ```
   Expected:
   - BILLING_QUESTION
   - System understands "it" refers to balance
   - `contextFromHistory`: "User inquired about balance"

3. Further context:
   ```json
   {
     "user_id": "test-user-3",
     "message": "Can you explain the charges from last month?"
   }
   ```
   Expected:
   - BILLING_QUESTION
   - Maintains billing context
   - References previous balance inquiry

**Success Criteria**:
- Pronoun resolution works ("it", "that", etc.)
- Context carries through conversation
- Relevant history is included

### Scenario 4: Multi-User Isolation
**Objective**: Ensure memory doesn't leak between users

**Test Steps**:
1. User 1 technical issue:
   ```json
   {
     "user_id": "user-alpha",
     "message": "I forgot my password"
   }
   ```

2. User 2 different issue:
   ```json
   {
     "user_id": "user-beta",
     "message": "I want to cancel my subscription"
   }
   ```

3. User 1 follow-up:
   ```json
   {
     "user_id": "user-alpha",
     "message": "I still need help with this"
   }
   ```
   Expected: References password issue, NOT subscription

4. User 2 follow-up:
   ```json
   {
     "user_id": "user-beta",
     "message": "What about my refund?"
   }
   ```
   Expected: References subscription/billing, NOT password

**Success Criteria**:
- Each user has isolated memory
- No cross-contamination of contexts
- Correct history for each user

### Scenario 5: Memory Window Testing
**Objective**: Verify the 10-message window limit works correctly

**Test Steps**:
1. Send 12 messages from same user with different topics
2. Verify only last 10 are considered in context
3. Check that very old issues aren't referenced

**Success Criteria**:
- Only recent history affects classification
- Old messages roll off properly
- Performance remains good

### Scenario 6: Pattern Recognition
**Objective**: Test chronic issue detection

**Test Steps**:
1. Simulate recurring login issues over time:
   - Message 1: "Can't log in" (Day 1)
   - Message 2: "Login failed again" (Day 3)
   - Message 3: "Still having login problems" (Day 5)
   - Message 4: "This login issue is ongoing" (Day 7)
   - Message 5: "Login STILL broken!" (Day 10)

**Expected Result**:
- System detects pattern
- Automatic escalation after 3+ similar issues
- Suggests permanent solution
- Lists all related tickets

**Success Criteria**:
- Pattern detection triggers
- Appropriate escalation occurs
- Historical tickets are linked

### Scenario 7: Intent Evolution
**Objective**: Track how issues change over time

**Test Steps**:
1. Start with feature request:
   ```json
   {
     "message": "It would be nice to have dark mode"
   }
   ```
   Expected: FEATURE_REQUEST

2. Follow up with impatience:
   ```json
   {
     "message": "When will dark mode be available?"
   }
   ```
   Expected: Still FEATURE_REQUEST, but noted as follow-up

3. Escalate to complaint:
   ```json
   {
     "message": "You promised dark mode months ago!"
   }
   ```
   Expected: Changes to COMPLAINT, references feature request history

**Success Criteria**:
- Intent evolution is tracked
- Historical context preserved
- Appropriate routing changes

### Scenario 8: Session Timeout
**Objective**: Verify memory expires appropriately

**Test Steps**:
1. Send initial message
2. Wait for session timeout (configured timeout + 5 minutes)
3. Send follow-up message
4. Verify it's treated as new conversation

**Success Criteria**:
- Old sessions expire
- New session starts fresh
- No stale context used

## Automated Test Script

```python
import asyncio
import json
import time
from datetime import datetime
import aiohttp

class MemoryWorkflowTester:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.results = []
    
    async def send_message(self, user_id, message, delay=0):
        if delay > 0:
            await asyncio.sleep(delay)
        
        payload = {
            "correlation_id": f"test-{int(time.time()*1000)}",
            "user_id": user_id,
            "message": message,
            "callback_url": "http://172.17.0.1:8000/api/n8n-callback"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as response:
                result = await response.json()
                self.results.append({
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "message": message,
                    "response": result
                })
                return result
    
    async def run_scenario_1(self):
        print("Running Scenario 1: Basic Memory Retention")
        
        # Initial message
        result1 = await self.send_message(
            "test-user-1", 
            "I can't log into my account"
        )
        print(f"Initial response: {result1}")
        
        # Follow-up after 2 seconds
        result2 = await self.send_message(
            "test-user-1",
            "It's still not working",
            delay=2
        )
        print(f"Follow-up response: {result2}")
        
        # Verify follow-up was recognized
        assert result2.get('isFollowUp') == True, "Follow-up not recognized"
        assert len(result2.get('relatedTickets', [])) > 0, "No related tickets"
        
        print("✓ Scenario 1 passed")
    
    async def run_all_scenarios(self):
        await self.run_scenario_1()
        # Add more scenarios...
        
        # Save results
        with open('memory_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

# Usage
if __name__ == "__main__":
    tester = MemoryWorkflowTester("http://your-n8n-instance/webhook/xxx")
    asyncio.run(tester.run_all_scenarios())
```

## Manual Testing Checklist

- [ ] Basic memory retention works
- [ ] Issue escalation triggers correctly
- [ ] Context-aware responses are accurate
- [ ] Multi-user isolation is maintained
- [ ] Memory window limit functions properly
- [ ] Pattern recognition detects chronic issues
- [ ] Intent evolution is tracked
- [ ] Session timeout clears memory
- [ ] Related tickets are properly linked
- [ ] Escalation reasons are meaningful
- [ ] High-priority routing works
- [ ] Executive escalation triggers appropriately

## Performance Metrics

### Expected Response Times
- First message: 2-3 seconds
- Follow-up messages: 2-4 seconds (memory lookup adds ~1s)
- Complex patterns: 3-5 seconds

### Memory Usage
- Per user: ~2KB for 10-message history
- 1000 concurrent users: ~2MB memory overhead

### Success Metrics
- Memory accuracy: >95%
- Context relevance: >90%
- Pattern detection: >85%
- User isolation: 100%

## Troubleshooting

### Common Issues

1. **Memory not persisting**
   - Check Buffer Memory node configuration
   - Verify sessionKey uses user_id
   - Check memory node is connected

2. **Wrong context returned**
   - Verify memory window size
   - Check session timeout settings
   - Ensure user_id is consistent

3. **Escalation not triggering**
   - Check Switch node expression
   - Verify output count is 6
   - Test escalation conditions

4. **Performance degradation**
   - Monitor memory window size
   - Check for memory leaks
   - Consider reducing context window

## Reporting

### Test Report Template
```
Test Date: [DATE]
Tester: [NAME]
Workflow Version: [VERSION]

Scenarios Tested: X/8
Passed: X
Failed: X

Issues Found:
1. [Issue description]
   - Steps to reproduce
   - Expected vs Actual
   - Severity

Performance Metrics:
- Average response time: Xs
- Memory accuracy: X%
- Pattern detection rate: X%

Recommendations:
- [Improvement suggestions]
```

## Conclusion

This test plan ensures comprehensive validation of the memory-enhanced workflow. Regular testing using these scenarios will maintain system reliability and catch regressions early.