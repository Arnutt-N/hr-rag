"""
Human-in-the-Loop Service - Feedback collection and active learning
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Feedback:
    """User feedback on AI response."""
    feedback_id: str
    query_id: str
    query: str
    answer: str
    rating: int  # 1-5
    feedback_type: str  # 'correct', 'partial', 'incorrect', 'hallucination'
    user_comment: Optional[str]
    timestamp: str
    user_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HumanInTheLoopService:
    """
    Human-in-the-loop for continuous improvement.
    
    Features:
    - Collect user feedback
    - Identify problematic queries
    - Active learning suggestions
    - Dataset curation
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.feedback_list: List[Feedback] = []
        self.storage_path = storage_path or "/tmp/hr-rag-feedback.jsonl"
    
    def submit_feedback(
        self,
        query_id: str,
        query: str,
        answer: str,
        rating: int,
        feedback_type: str,
        user_comment: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Submit user feedback.
        
        Args:
            query_id: ID of the query
            query: Original query
            answer: AI's answer
            rating: 1-5 rating
            feedback_type: Type of feedback
            user_comment: Optional comment
            user_id: User identifier
        
        Returns:
            Feedback confirmation
        """
        import uuid
        
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            query_id=query_id,
            query=query,
            answer=answer,
            rating=rating,
            feedback_type=feedback_type,
            user_comment=user_comment,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id
        )
        
        self.feedback_list.append(feedback)
        self._persist_feedback(feedback)
        
        return {
            'success': True,
            'feedback_id': feedback.feedback_id,
            'message': 'ขอบคุณสำหรับ feedback'
        }
    
    def _persist_feedback(self, feedback: Feedback):
        """Save feedback to disk."""
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feedback.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Failed to persist feedback: {e}")
    
    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback statistics."""
        # Filter recent feedback
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 3600)
        recent = [
            f for f in self.feedback_list
            if datetime.fromisoformat(f.timestamp).timestamp() > cutoff
        ]
        
        if not recent:
            return {'total': 0, 'message': 'No feedback in period'}
        
        total = len(recent)
        avg_rating = sum(f.rating for f in recent) / total
        
        type_counts = {}
        for f in recent:
            type_counts[f.feedback_type] = type_counts.get(f.feedback_type, 0) + 1
        
        # Identify problematic queries
        problematic = [f for f in recent if f.rating <= 2 or f.feedback_type == 'incorrect']
        
        return {
            'total_feedback': total,
            'average_rating': round(avg_rating, 2),
            'feedback_types': type_counts,
            'satisfaction_rate': sum(1 for f in recent if f.rating >= 4) / total * 100,
            'problematic_queries': [
                {'query': f.query, 'rating': f.rating, 'type': f.feedback_type}
                for f in problematic[:10]
            ],
            'improvement_suggestions': self._generate_suggestions(problematic)
        }
    
    def _generate_suggestions(self, problematic: List[Feedback]) -> List[str]:
        """Generate improvement suggestions from problematic feedback."""
        suggestions = []
        
        # Analyze patterns
        hallucination_count = sum(1 for f in problematic if f.feedback_type == 'hallucination')
        incorrect_count = sum(1 for f in problematic if f.feedback_type == 'incorrect')
        
        if hallucination_count > len(problematic) * 0.3:
            suggestions.append("พบ hallucination บ่อย ควรปรับปรุง context filtering")
        
        if incorrect_count > len(problematic) * 0.3:
            suggestions.append("พบคำตอบผิดบ่อย ควรปรับปรุง retrieval quality")
        
        # Check for common query patterns
        query_keywords = {}
        for f in problematic:
            for word in f.query.split():
                query_keywords[word] = query_keywords.get(word, 0) + 1
        
        common_issues = sorted(query_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
        for word, count in common_issues:
            if count > 2:
                suggestions.append(f"คำถามที่มีคำว่า '{word}' มักได้คำตอบไม่ดี")
        
        return suggestions
    
    def get_training_data(self, min_rating: int = 4) -> List[Dict[str, Any]]:
        """
        Get high-quality feedback for training.
        
        Returns feedback with good ratings for fine-tuning.
        """
        good_feedback = [
            f for f in self.feedback_list
            if f.rating >= min_rating and f.feedback_type == 'correct'
        ]
        
        return [
            {
                'query': f.query,
                'answer': f.answer,
                'rating': f.rating
            }
            for f in good_feedback
        ]
    
    def get_queries_needing_improvement(self) -> List[Dict[str, Any]]:
        """Get queries that need system improvement."""
        bad_feedback = [
            f for f in self.feedback_list
            if f.rating <= 2 or f.feedback_type in ['incorrect', 'hallucination']
        ]
        
        # Group similar queries
        from collections import defaultdict
        query_groups = defaultdict(list)
        
        for f in bad_feedback:
            # Simple grouping by first 20 chars
            key = f.query[:20]
            query_groups[key].append(f)
        
        # Return most problematic groups
        sorted_groups = sorted(query_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        return [
            {
                'query_pattern': pattern,
                'count': len(feedbacks),
                'examples': [f.query for f in feedbacks[:3]]
            }
            for pattern, feedbacks in sorted_groups[:10]
        ]
    
    def export_feedback_dataset(self, format: str = 'json') -> str:
        """Export feedback as dataset for training."""
        if format == 'json':
            return json.dumps(
                [f.to_dict() for f in self.feedback_list],
                ensure_ascii=False,
                indent=2
            )
        elif format == 'csv':
            lines = ['feedback_id,query,answer,rating,feedback_type,timestamp']
            for f in self.feedback_list:
                lines.append(f'"{f.feedback_id}","{f.query[:100]}","{f.answer[:100]}",{f.rating},{f.feedback_type},{f.timestamp}')
            return '\n'.join(lines)
        else:
            return ''


# Singleton
_hitl_service: Optional[HumanInTheLoopService] = None


def get_human_in_the_loop_service() -> HumanInTheLoopService:
    """Get HITL service singleton."""
    global _hitl_service
    if _hitl_service is None:
        _hitl_service = HumanInTheLoopService()
    return _hitl_service
