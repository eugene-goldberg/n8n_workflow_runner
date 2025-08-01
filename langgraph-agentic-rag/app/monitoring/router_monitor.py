"""
Router monitoring and logging system for tracking decisions vs actual tool usage
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from app.schemas.routing import RetrievalStrategy


@dataclass
class RoutingDecisionLog:
    """Log entry for a routing decision"""
    timestamp: str
    query: str
    strategy: str
    confidence: float
    detected_entities: List[str]
    reasoning: str
    tools_expected: List[str]
    tools_actual: Optional[List[str]] = None
    match: Optional[bool] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class RouterMonitor:
    """Monitor and log router decisions vs actual tool usage"""
    
    def __init__(self, log_file: str = "/root/langgraph-agentic-rag/logs/router_decisions.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("router_monitor")
        handler = logging.FileHandler("/root/langgraph-agentic-rag/logs/router_monitor.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Expected tools mapping
        self.expected_tools = {
            RetrievalStrategy.GRAPH: ['get_entity_relationships', 'graph_search'],
            RetrievalStrategy.VECTOR: ['vector_search'],
            RetrievalStrategy.HYBRID_SEQUENTIAL: ['vector_search', 'get_entity_relationships'],
            RetrievalStrategy.HYBRID_PARALLEL: ['vector_search', 'graph_search'],
            RetrievalStrategy.NO_RETRIEVAL: []
        }
        
    def log_routing_decision(self, query: str, routing_decision) -> str:
        """Log a routing decision and return a tracking ID"""
        
        log_entry = RoutingDecisionLog(
            timestamp=datetime.now().isoformat(),
            query=query[:200],  # Truncate long queries
            strategy=routing_decision.strategy.value,
            confidence=routing_decision.confidence,
            detected_entities=routing_decision.detected_entities,
            reasoning=routing_decision.reasoning,
            tools_expected=self.expected_tools.get(routing_decision.strategy, [])
        )
        
        # Write to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(asdict(log_entry)) + '\n')
            
        # Log to standard logger
        self.logger.info(f"Router Decision - Query: '{query[:50]}...' Strategy: {log_entry.strategy} Confidence: {log_entry.confidence}")
        
        return log_entry.timestamp
        
    def log_actual_usage(self, tracking_id: str, tools_used: List[str], response_time_ms: float = None, error: str = None):
        """Update log with actual tool usage"""
        
        # Read all logs
        logs = []
        with open(self.log_file, 'r') as f:
            for line in f:
                logs.append(json.loads(line))
                
        # Find and update the matching log
        for i, log in enumerate(logs):
            if log['timestamp'] == tracking_id:
                log['tools_actual'] = tools_used
                log['response_time_ms'] = response_time_ms
                log['error'] = error
                
                # Check if tools match expectation
                expected = set(log['tools_expected'])
                actual = set(tools_used)
                log['match'] = bool(expected.intersection(actual)) if expected else (len(actual) == 0)
                
                logs[i] = log
                
                # Log mismatch
                if not log['match']:
                    self.logger.warning(
                        f"Tool Mismatch - Query: '{log['query'][:50]}...' "
                        f"Expected: {log['tools_expected']} Actual: {tools_used}"
                    )
                    
                break
                
        # Rewrite the file
        with open(self.log_file, 'w') as f:
            for log in logs:
                f.write(json.dumps(log) + '\n')
                
    def get_statistics(self) -> Dict:
        """Calculate statistics from logged decisions"""
        
        logs = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    continue
                    
        if not logs:
            return {"total": 0, "message": "No logs found"}
            
        total = len(logs)
        completed = len([l for l in logs if l.get('tools_actual') is not None])
        matches = len([l for l in logs if l.get('match') is True])
        
        # Strategy breakdown
        strategy_stats = {}
        for strategy in RetrievalStrategy:
            strategy_logs = [l for l in logs if l['strategy'] == strategy.value]
            strategy_matches = [l for l in strategy_logs if l.get('match') is True]
            
            strategy_stats[strategy.value] = {
                'total': len(strategy_logs),
                'matches': len(strategy_matches),
                'accuracy': len(strategy_matches) / len(strategy_logs) if strategy_logs else 0
            }
            
        # Average confidence by match/mismatch
        matched_logs = [l for l in logs if l.get('match') is True]
        mismatched_logs = [l for l in logs if l.get('match') is False]
        
        avg_confidence_match = sum(l['confidence'] for l in matched_logs) / len(matched_logs) if matched_logs else 0
        avg_confidence_mismatch = sum(l['confidence'] for l in mismatched_logs) / len(mismatched_logs) if mismatched_logs else 0
        
        # Response time stats
        response_times = [l['response_time_ms'] for l in logs if l.get('response_time_ms')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_queries': total,
            'completed_queries': completed,
            'matching_tool_usage': matches,
            'overall_accuracy': matches / completed if completed else 0,
            'strategy_breakdown': strategy_stats,
            'avg_confidence_when_matched': avg_confidence_match,
            'avg_confidence_when_mismatched': avg_confidence_mismatch,
            'avg_response_time_ms': avg_response_time,
            'errors': len([l for l in logs if l.get('error')])
        }
        
    def generate_report(self) -> str:
        """Generate a human-readable report"""
        
        stats = self.get_statistics()
        
        if stats['total_queries'] == 0:
            return "No routing decisions logged yet."
            
        report = f"""
Router Monitoring Report
========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overall Statistics:
------------------
Total Queries: {stats['total_queries']}
Completed: {stats['completed_queries']}
Tool Usage Matches: {stats['matching_tool_usage']} ({stats['overall_accuracy']:.1%})
Errors: {stats['errors']}
Avg Response Time: {stats['avg_response_time_ms']:.1f}ms

Strategy Breakdown:
------------------"""
        
        for strategy, data in stats['strategy_breakdown'].items():
            report += f"\n{strategy}:"
            report += f"\n  Total: {data['total']}"
            report += f"\n  Matches: {data['matches']} ({data['accuracy']:.1%})"
            
        report += f"\n\nConfidence Analysis:"
        report += f"\n-------------------"
        report += f"\nAvg Confidence (Matched): {stats['avg_confidence_when_matched']:.2f}"
        report += f"\nAvg Confidence (Mismatched): {stats['avg_confidence_when_mismatched']:.2f}"
        
        return report
        

# Create a global monitor instance
monitor = RouterMonitor()


def integrate_with_spyro_agent():
    """Example integration code for SpyroSolutions agent"""
    
    integration_code = '''
# Add to SpyroSolutions agent

from app.monitoring.router_monitor import monitor
from app.agent.router import DeterministicRouter

router = DeterministicRouter()

# When processing a query
def process_query_with_monitoring(query: str):
    # Get routing decision
    decision = router.route(query)
    
    # Log the decision
    tracking_id = monitor.log_routing_decision(query, decision)
    
    try:
        # Process query with your agent
        start_time = datetime.now()
        result = agent.process(query)  # Your existing agent
        
        # Extract tools used from result
        tools_used = extract_tools_from_result(result)  # Implement this
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log actual usage
        monitor.log_actual_usage(tracking_id, tools_used, response_time)
        
        return result
        
    except Exception as e:
        # Log error
        monitor.log_actual_usage(tracking_id, [], error=str(e))
        raise
        
# To view statistics
print(monitor.generate_report())
'''
    
    return integration_code