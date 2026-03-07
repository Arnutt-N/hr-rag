"""
Evaluation Router for FastAPI
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from app.core.security import get_current_user
from app.models.schemas import User
from app.services.evaluation import (
    RAGEvaluator,
    TestCase,
    HR_TEST_DATASET,
    EvaluationMetrics,
)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class EvaluationRequest(BaseModel):
    """Request body สำหรับ run evaluation"""
    provider: str = "openai"  # openai, anthropic, google, groq
    test_dataset: Optional[str] = "hr_default"  # hr_default, custom
    custom_tests: Optional[List[Dict]] = None
    k: int = 5  # top-k for retrieval evaluation


class EvaluationResponse(BaseModel):
    """Response สำหรับ evaluation results"""
    evaluation_id: str
    metrics: Dict[str, float]
    overall_score: float
    test_cases_evaluated: int
    evaluation_time: float
    timestamp: str
    provider: str


class ComparisonRequest(BaseModel):
    """Request สำหรับเปรียบเทียบกับ baseline"""
    current_evaluation_id: str
    baseline_evaluation_id: str


class ComparisonResponse(BaseModel):
    """Response สำหรับ comparison"""
    changes: Dict[str, Any]
    drifts: List[Dict]
    has_drift: bool
    recommendations: List[str]


# In-memory storage สำหรับ evaluation results (ใช้ database จริงใน production)
evaluation_results: Dict[str, Dict] = {}


@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    รันการประเมินผล RAG แบบครบวงจร
    
    - ประเมิน Retrieval metrics (Precision@K, Recall@K, MRR, NDCG, Hit Rate)
    - ประเมิน Generation metrics (Faithfulness, Relevance, Hallucination)
    - ประเมิน Thai-specific metrics
    - คำนวณ Overall Score
    """
    from app.services.llm_providers import LLMProviderFactory
    from app.services.embeddings import EmbeddingService
    from app.services.vector_store import VectorStoreService
    
    # Load test dataset
    if request.test_dataset == "hr_default":
        test_cases = HR_TEST_DATASET
    elif request.custom_tests:
        test_cases = [TestCase(**t) for t in request.custom_tests]
    else:
        raise HTTPException(status_code=400, detail="Invalid test dataset")
    
    # Initialize services
    llm = LLMProviderFactory.get_provider(request.provider)
    embeddings = EmbeddingService()
    vector_store = VectorStoreService()
    
    # Initialize evaluator
    evaluator = RAGEvaluator(llm, embeddings, vector_store)
    
    # Mock RAG system for evaluation
    class MockRAGSystem:
        async def query(self, query: str):
            # This should be replaced with actual RAG system
            query_embedding = await embeddings.embed(query)
            contexts = await vector_store.search(query_embedding, top_k=request.k)
            
            # Generate answer using LLM
            context_text = "\n".join([c["text"] for c in contexts])
            prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"
            answer = await llm.complete(prompt)
            
            return {
                "answer": answer,
                "contexts": [c["text"] for c in contexts],
            }
    
    rag_system = MockRAGSystem()
    
    # Run evaluation
    start_time = datetime.now()
    result = await evaluator.run_full_evaluation(test_cases, rag_system)
    evaluation_time = (datetime.now() - start_time).total_seconds()
    
    # Create response
    evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
    
    response = EvaluationResponse(
        evaluation_id=evaluation_id,
        metrics=result["metrics"],
        overall_score=result["overall_score"],
        test_cases_evaluated=result["test_cases_evaluated"],
        evaluation_time=evaluation_time,
        timestamp=result["timestamp"],
        provider=request.provider,
    )
    
    # Store result
    evaluation_results[evaluation_id] = {
        "response": response.dict(),
        "details": result,
        "user_id": current_user.id,
    }
    
    return response


@router.get("/results/{evaluation_id}")
async def get_evaluation_result(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
):
    """ดึงผลการประเมินตาม ID"""
    if evaluation_id not in evaluation_results:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    result = evaluation_results[evaluation_id]
    
    # Check permission
    if result["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return result


@router.get("/history")
async def get_evaluation_history(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
):
    """ดึงประวัติการประเมินของผู้ใช้"""
    user_results = [
        {
            "evaluation_id": k,
            "overall_score": v["response"]["overall_score"],
            "timestamp": v["response"]["timestamp"],
            "provider": v["response"]["provider"],
        }
        for k, v in evaluation_results.items()
        if v["user_id"] == current_user.id
    ]
    
    # Sort by timestamp descending
    user_results.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return user_results[:limit]


@router.post("/compare", response_model=ComparisonResponse)
async def compare_evaluations(
    request: ComparisonRequest,
    current_user: User = Depends(get_current_user),
):
    """
    เปรียบเทียบผลการประเมิน 2 ครั้ง
    
    ใช้สำหรับตรวจจับ performance drift
    """
    if request.current_evaluation_id not in evaluation_results:
        raise HTTPException(status_code=404, detail="Current evaluation not found")
    
    if request.baseline_evaluation_id not in evaluation_results:
        raise HTTPException(status_code=404, detail="Baseline evaluation not found")
    
    current = evaluation_results[request.current_evaluation_id]
    baseline = evaluation_results[request.baseline_evaluation_id]
    
    # Check permissions
    if current["user_id"] != current_user.id or baseline["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Run comparison
    from app.services.evaluation import RAGEvaluator
    evaluator = RAGEvaluator(None, None, None)
    
    comparison = evaluator.compare_with_baseline(
        current["response"]["metrics"],
        baseline["response"]["metrics"],
    )
    
    # Generate recommendations
    recommendations = []
    for drift in comparison["drifts"]:
        metric = drift["metric"]
        change = drift["change"]
        
        if metric == "precision_at_k" and change < 0:
            recommendations.append("🔍 พิจารณาปรับปรุง embedding model หรือใช้ re-ranking")
        elif metric == "recall_at_k" and change < 0:
            recommendations.append("📄 เพิ่ม chunk overlap หรือใช้ hybrid search")
        elif metric == "faithfulness" and change < 0:
            recommendations.append("📝 ปรับปรุง prompt หรือลด context length")
        elif metric == "hallucination_rate" and change > 0:
            recommendations.append("⚠️ Hallucination เพิ่มขึ้น พิจารณาใช้ stricter prompting")
        elif metric == "response_time" and change > 0:
            recommendations.append("⏱️ Response time เพิ่มขึ้น พิจารณา optimize หรือ caching")
    
    return ComparisonResponse(
        changes=comparison["changes"],
        drifts=comparison["drifts"],
        has_drift=comparison["has_drift"],
        recommendations=recommendations,
    )


@router.get("/metrics/targets")
async def get_target_metrics():
    """
    ดึงค่าเป้าหมายสำหรับแต่ละ metric ตาม use case
    """
    return {
        "hr_policy": {
            "precision_at_k": {"target": 0.85, "min_acceptable": 0.75},
            "recall_at_k": {"target": 0.80, "min_acceptable": 0.70},
            "faithfulness": {"target": 0.90, "min_acceptable": 0.80},
            "answer_relevance": {"target": 0.85, "min_acceptable": 0.75},
            "hallucination_rate": {"target": 0.05, "max_acceptable": 0.15},
            "response_time": {"target": 2.0, "max_acceptable": 5.0},
        },
        "customer_support": {
            "precision_at_k": {"target": 0.80, "min_acceptable": 0.70},
            "recall_at_k": {"target": 0.70, "min_acceptable": 0.60},
            "faithfulness": {"target": 0.90, "min_acceptable": 0.80},
            "answer_relevance": {"target": 0.85, "min_acceptable": 0.75},
            "hallucination_rate": {"target": 0.05, "max_acceptable": 0.15},
            "response_time": {"target": 1.5, "max_acceptable": 3.0},
        },
        "legal": {
            "precision_at_k": {"target": 0.90, "min_acceptable": 0.85},
            "recall_at_k": {"target": 0.85, "min_acceptable": 0.80},
            "faithfulness": {"target": 0.95, "min_acceptable": 0.90},
            "answer_relevance": {"target": 0.90, "min_acceptable": 0.85},
            "hallucination_rate": {"target": 0.02, "max_acceptable": 0.05},
            "response_time": {"target": 3.0, "max_acceptable": 5.0},
        },
    }


@router.get("/test-datasets")
async def get_available_test_datasets():
    """ดึงรายการ test datasets ที่มี"""
    return {
        "hr_default": {
            "name": "HR Policy Default",
            "description": "ชุดข้อสอบสำหรับนโยบาย HR มาตรฐาน",
            "size": len(HR_TEST_DATASET),
            "categories": ["hr_policy", "benefits", "legal", "general"],
            "query_types": ["easy", "complex", "edge_case", "out_of_scope", "multi_hop"],
        },
        "custom": {
            "name": "Custom Dataset",
            "description": "สร้างชุดทดสอบเอง",
            "size": 0,
            "categories": [],
            "query_types": [],
        },
    }


@router.post("/test-datasets/custom")
async def create_custom_test_dataset(
    tests: List[Dict],
    current_user: User = Depends(get_current_user),
):
    """สร้าง custom test dataset"""
    # Validate test cases
    required_fields = ["id", "query", "query_type", "expected_answer", "category"]
    
    for test in tests:
        for field in required_fields:
            if field not in test:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
    
    # Store custom dataset (ใน production ควรเก็บใน database)
    dataset_id = f"custom_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "dataset_id": dataset_id,
        "size": len(tests),
        "message": "Custom test dataset created successfully",
    }


@router.get("/dashboard")
async def get_evaluation_dashboard(
    current_user: User = Depends(get_current_user),
):
    """
    ดึงข้อมูลสำหรับแสดงบน Dashboard
    """
    user_results = [
        v for k, v in evaluation_results.items()
        if v["user_id"] == current_user.id
    ]
    
    if not user_results:
        return {
            "message": "No evaluation data available",
            "total_evaluations": 0,
            "average_score": 0,
            "latest_metrics": {},
        }
    
    # Calculate statistics
    total_evaluations = len(user_results)
    average_score = sum(
        r["response"]["overall_score"] for r in user_results
    ) / total_evaluations
    
    # Get latest evaluation
    latest = max(user_results, key=lambda x: x["response"]["timestamp"])
    
    # Calculate trends (ถ้ามีอย่างน้อย 2 ครั้ง)
    trends = {}
    if total_evaluations >= 2:
        sorted_results = sorted(
            user_results,
            key=lambda x: x["response"]["timestamp"]
        )
        
        first = sorted_results[0]["response"]["metrics"]
        last = sorted_results[-1]["response"]["metrics"]
        
        for metric in first.keys():
            if metric in last:
                change = last[metric] - first[metric]
                trends[metric] = {
                    "change": change,
                    "trend": "improving" if change > 0 else "declining" if change < 0 else "stable",
                }
    
    return {
        "total_evaluations": total_evaluations,
        "average_score": average_score,
        "latest_metrics": latest["response"]["metrics"],
        "latest_evaluation_id": latest["response"]["evaluation_id"],
        "latest_timestamp": latest["response"]["timestamp"],
        "trends": trends,
    }
