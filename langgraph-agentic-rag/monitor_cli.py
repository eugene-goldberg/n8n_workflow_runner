#!/usr/bin/env python3
"""
CLI tool for viewing router monitoring statistics
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.monitoring.router_monitor import RouterMonitor


def main():
    """View router monitoring statistics"""
    
    monitor = RouterMonitor()
    
    print("🔍 Router Monitoring Dashboard")
    print("=" * 60)
    
    # Check if log file exists
    if not monitor.log_file.exists():
        print("No logs found. Router decisions will be logged to:")
        print(f"  {monitor.log_file}")
        return
        
    # Generate and display report
    report = monitor.generate_report()
    print(report)
    
    # Show recent mismatches
    print("\n\nRecent Mismatches:")
    print("-" * 60)
    
    mismatches = []
    with open(monitor.log_file, 'r') as f:
        for line in f:
            try:
                log = json.loads(line)
                if log.get('match') is False:
                    mismatches.append(log)
            except:
                continue
                
    # Show last 5 mismatches
    for log in mismatches[-5:]:
        print(f"\nQuery: {log['query'][:80]}...")
        print(f"Expected: {log['tools_expected']}")
        print(f"Actual: {log.get('tools_actual', 'Unknown')}")
        print(f"Strategy: {log['strategy']} (confidence: {log['confidence']:.2f})")
        
    if not mismatches:
        print("No mismatches found! 🎉")
        
    # Show by hour statistics
    print("\n\nQueries by Hour (last 24h):")
    print("-" * 60)
    
    hourly_stats = {}
    with open(monitor.log_file, 'r') as f:
        for line in f:
            try:
                log = json.loads(line)
                timestamp = datetime.fromisoformat(log['timestamp'])
                hour = timestamp.strftime('%Y-%m-%d %H:00')
                
                if hour not in hourly_stats:
                    hourly_stats[hour] = {'total': 0, 'matches': 0}
                    
                hourly_stats[hour]['total'] += 1
                if log.get('match'):
                    hourly_stats[hour]['matches'] += 1
                    
            except:
                continue
                
    # Show last 10 hours
    sorted_hours = sorted(hourly_stats.keys())[-10:]
    for hour in sorted_hours:
        stats = hourly_stats[hour]
        accuracy = stats['matches'] / stats['total'] if stats['total'] else 0
        bar = '█' * int(accuracy * 20)
        print(f"{hour}: {stats['total']:3d} queries | {accuracy:5.1%} |{bar}")


if __name__ == "__main__":
    main()