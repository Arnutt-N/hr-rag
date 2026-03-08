"""
Observability Service - Monitoring, tracing, and evaluation for HR-RAG
Integrates with LangSmith for production monitoring
"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class QueryStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class QueryTrace:
    """Trace of a single query through the system."""
    trace_id: str
    timestamp: str
    query: str
    user_id: Optional[int]
    session_id: Optional[str]
    
    # Retrieval metrics
    retrieval_time_ms: float = 0
    documents_retrieved: int = 0
    retrieval_strategy: str = ""
    
    # Reranking metrics
    reranking_time_ms: float = 0
    rerank_score_before: float = 0
    rerank_score_after: float = 0
    
    # Generation metrics
    generation_time_ms: float = 0
    tokens_used: int = 0
    llm_provider: str = ""
    
    # Quality metrics
    answer_relevance_score: float = 0
    context_precision: float = 0
    context_recall: float = 0
    
    # Result
    status: QueryStatus = QueryStatus.SUCCESS
    error_message: Optional[str] = None
    final_answer: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'status': self.status.value,
            'timestamp': self.timestamp
        }


class ObservabilityService:
    """
    Observability service for monitoring HR-RAG performance.
    
    Features:
    - Query tracing
    - Performance metrics
    - Quality evaluation
    - Error tracking
    - Dashboard data
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.traces: List[QueryTrace] = []
        self.storage_path = storage_path or "/tmp/hr-rag-traces.jsonl"
        self.metrics_cache: Dict[str, Any] = {}
        
    def start_trace(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> QueryTrace:
        """Start a new query trace."""
        trace = QueryTrace(
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            query=query,
            user_id=user_id,
            session_id=session_id
        )
        return trace
    
    def end_trace(self, trace: QueryTrace):
        """End and save a trace."""
        self.traces.append(trace)
        self._persist_trace(trace)
    
    def _persist_trace(self, trace: QueryTrace):
        """Save trace to disk."""
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Failed to persist trace: {e}")
    
    def get_metrics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get system metrics for dashboard."""
        
        # Filter traces by time window
        cutoff_time = datetime.utcnow().timestamp() - (time_window_hours * 3600)
        recent_traces = [
            t for t in self.traces
            if datetime.fromisoformat(t.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_traces:
            return self._empty_metrics()
        
        total_queries = len(recent_traces)
        successful = sum(1 for t in recent_traces if t.status == QueryStatus.SUCCESS)
        failed = sum(1 for t in recent_traces if t.status == QueryStatus.FAILED)
        
        avg_retrieval_time = sum(t.retrieval_time_ms for t in recent_traces) / total_queries
        avg_generation_time = sum(t.generation_time_ms for t in recent_traces) / total_queries
        
        avg_relevance = sum(t.answer_relevance_score for t in recent_traces) / total_queries
        
        return {
            "time_window_hours": time_window_hours,
            "total_queries": total_queries,
            "success_rate": round(successful / total_queries * 100, 2),
            "failure_rate": round(failed / total_queries * 100, 2),
            "avg_retrieval_time_ms": round(avg_retrieval_time, 2),
            "avg_generation_time_ms": round(avg_generation_time, 2),
            "avg_answer_relevance": round(avg_relevance, 2),
            "total_tokens_used": sum(t.tokens_used for t in recent_traces),
            "top_errors": self._get_top_errors(recent_traces),
            "slow_queries": self._get_slow_queries(recent_traces),
            "low_quality_queries": self._get_low_quality_queries(recent_traces)
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "time_window_hours": 24,
            "total_queries": 0,
            "success_rate": 0,
            "failure_rate": 0,
            "avg_retrieval_time_ms": 0,
            "avg_generation_time_ms": 0,
            "avg_answer_relevance": 0,
            "total_tokens_used": 0,
            "top_errors": [],
            "slow_queries": [],
            "low_quality_queries": []
        }
    
    def _get_top_errors(self, traces: List[QueryTrace], n: int = 5) -> List[Dict]:
        """Get most common errors."""
        errors: Dict[str, int] = {}
        for t in traces:
            if t.error_message:
                errors[t.error_message] = errors.get(t.error_message, 0) + 1
        
        sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)
        return [{"error": e, "count": c} for e, c in sorted_errors[:n]]
    
    def _get_slow_queries(self, traces: List[QueryTrace], n: int = 5) -> List[Dict]:
        """Get slowest queries."""
        sorted_traces = sorted(
            traces,
            key=lambda t: t.retrieval_time_ms + t.generation_time_ms,
            reverse=True
        )
        
        return [
            {
                "query": t.query[:100] + "...",
                "total_time_ms": t.retrieval_time_ms + t.generation_time_ms,
                "trace_id": t.trace_id
            }
            for t in sorted_traces[:n]
        ]
    
    def _get_low_quality_queries(self, traces: List[QueryTrace], n: int = 5) -> List[Dict]:
        """Get queries with low relevance scores."""
        low_quality = [t for t in traces if t.answer_relevance_score < 0.5]
        sorted_traces = sorted(low_quality, key=lambda t: t.answer_relevance_score)
        
        return [
            {
                "query": t.query[:100] + "...",
                "relevance_score": t.answer_relevance_score,
                "trace_id": t.trace_id
            }
            for t in sorted_traces[:n]
        ]
    
    async def evaluate_answer_relevance(
        self,
        query: str,
        answer: str,
        context: str
    ) -> float:
        """
        Evaluate relevance of answer to query.
        
        Returns score 0-1
        """
        from app.services.llm.langchain_service import get_llm_service
        
        prompt = f"""Rate answer relevance (0-10):

Question: {query}
Answer: {answer}
Context: {context[:500]}

Relevance (0-10):"""
        
        try:
            llm = get_llm_service()
            response = await llm.chat([{"role": "user", "content": prompt}])
            
            # Extract score
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                score = int(numbers[0])
                return min(10, max(0, score)) / 10
            return 0.5
            
        except:
            return 0.5
    
    def get_retrieval_analytics(self) -> Dict[str, Any]:
        """Analyze retrieval performance."""
        if not self.traces:
            return {}
        
        strategies = {}
        for t in self.traces:
            strategy = t.retrieval_strategy or "unknown"
            if strategy not in strategies:
                strategies[strategy] = {"count": 0, "avg_time": 0, "avg_docs": 0}
            
            strategies[strategy]["count"] += 1
            strategies[strategy]["avg_time"] += t.retrieval_time_ms
            strategies[strategy]["avg_docs"] += t.documents_retrieved
        
        # Calculate averages
        for strategy in strategies:
            count = strategies[strategy]["count"]
            strategies[strategy]["avg_time"] /= count
            strategies[strategy]["avg_docs"] /= count
        
        return {
            "strategies": strategies,
            "total_traces": len(self.traces)
        }
    
    def export_traces(self, format: str = "json") -> str:
        """Export traces for analysis."""
        if format == "json":
            return json.dumps(
                [t.to_dict() for t in self.traces],
                ensure_ascii=False,
                indent=2
            )
        elif format == "csv":
            # Simple CSV format
            lines = ["trace_id,timestamp,query,status,retrieval_time_ms,generation_time_ms"]
            for t in self.traces:
                lines.append(f"{t.trace_id},{t.timestamp},{t.query[:50]},{t.status.value},{t.retrieval_time_ms},{t.generation_time_ms}")
            return "\n".join(lines)
        else:
            return ""


# Singleton
_observability: Optional[ObservabilityService] = None


def get_observability_service() -> ObservabilityService:
    """Get observability service singleton."""
    global _observability
    if _observability is None:
        _observability = ObservabilityService()
    return _observability
