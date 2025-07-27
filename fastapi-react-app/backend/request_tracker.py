from typing import Dict, Optional, List
from datetime import datetime, timedelta
import uuid
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RequestStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class RequestTracker:
    def __init__(self, timeout_minutes: int = 10):
        self.pending_requests: Dict[str, dict] = {}
        self.timeout_minutes = timeout_minutes
        
    def create_request(self, user_id: str, message: str, metadata: Optional[dict] = None) -> str:
        """Create a new request with correlation ID"""
        correlation_id = str(uuid.uuid4())
        
        self.pending_requests[correlation_id] = {
            "correlation_id": correlation_id,
            "user_id": user_id,
            "message": message,
            "metadata": metadata or {},
            "status": RequestStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "attempts": 0
        }
        
        logger.info(f"Created request {correlation_id} for user {user_id}")
        return correlation_id
        
    def get_request(self, correlation_id: str) -> Optional[dict]:
        """Get request by correlation ID"""
        return self.pending_requests.get(correlation_id)
        
    def update_status(self, correlation_id: str, status: RequestStatus, error: Optional[str] = None):
        """Update request status"""
        if correlation_id in self.pending_requests:
            self.pending_requests[correlation_id]["status"] = status.value
            self.pending_requests[correlation_id]["updated_at"] = datetime.now().isoformat()
            
            if error:
                self.pending_requests[correlation_id]["error"] = error
                
            logger.info(f"Updated request {correlation_id} status to {status.value}")
            
    def complete_request(self, correlation_id: str, result: str):
        """Mark request as completed with result"""
        if correlation_id in self.pending_requests:
            self.pending_requests[correlation_id]["status"] = RequestStatus.COMPLETED.value
            self.pending_requests[correlation_id]["result"] = result
            self.pending_requests[correlation_id]["completed_at"] = datetime.now().isoformat()
            self.pending_requests[correlation_id]["updated_at"] = datetime.now().isoformat()
            
            # Calculate processing time
            created_at = datetime.fromisoformat(self.pending_requests[correlation_id]["created_at"])
            processing_time = (datetime.now() - created_at).total_seconds()
            self.pending_requests[correlation_id]["processing_time_seconds"] = processing_time
            
            logger.info(f"Completed request {correlation_id} in {processing_time:.2f} seconds")
            
    def fail_request(self, correlation_id: str, error: str):
        """Mark request as failed"""
        if correlation_id in self.pending_requests:
            self.update_status(correlation_id, RequestStatus.FAILED, error)
            self.pending_requests[correlation_id]["failed_at"] = datetime.now().isoformat()
            
    def increment_attempts(self, correlation_id: str):
        """Increment retry attempts for a request"""
        if correlation_id in self.pending_requests:
            self.pending_requests[correlation_id]["attempts"] += 1
            self.pending_requests[correlation_id]["updated_at"] = datetime.now().isoformat()
            
    def get_user_requests(self, user_id: str, include_completed: bool = False) -> List[dict]:
        """Get all requests for a specific user"""
        requests = []
        for request in self.pending_requests.values():
            if request["user_id"] == user_id:
                if include_completed or request["status"] != RequestStatus.COMPLETED.value:
                    requests.append(request)
        return sorted(requests, key=lambda x: x["created_at"], reverse=True)
        
    def cleanup_old_requests(self):
        """Remove completed and timed out requests older than timeout"""
        current_time = datetime.now()
        to_remove = []
        
        for correlation_id, request in self.pending_requests.items():
            created_at = datetime.fromisoformat(request["created_at"])
            age_minutes = (current_time - created_at).total_seconds() / 60
            
            # Mark timed out requests
            if request["status"] == RequestStatus.PENDING.value and age_minutes > self.timeout_minutes:
                self.update_status(correlation_id, RequestStatus.TIMEOUT)
                
            # Remove old completed or failed requests
            if request["status"] in [RequestStatus.COMPLETED.value, RequestStatus.FAILED.value, RequestStatus.TIMEOUT.value]:
                if age_minutes > self.timeout_minutes * 2:  # Keep for 2x timeout period
                    to_remove.append(correlation_id)
                    
        for correlation_id in to_remove:
            del self.pending_requests[correlation_id]
            
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old requests")
            
    def get_pending_count(self) -> int:
        """Get count of pending requests"""
        return sum(1 for r in self.pending_requests.values() 
                  if r["status"] in [RequestStatus.PENDING.value, RequestStatus.PROCESSING.value])