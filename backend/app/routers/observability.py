"""
Observability API Router - Monitoring and analytics dashboard
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.observability import get_observability_service

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/metrics")
async def get_metrics(time_window_hours: int = 24):
    """
    ดู metrics ระบบ (สำหรับ Dashboard)
    
    Get system metrics for dashboard.
    
    - success_rate: อัตราความสำเร็จ
    - avg_response_time: เวลาตอบสนองเฉลี่ย
    - answer_relevance: คะแนนความเกี่ยวข้อง
    - top_errors: ข้อผิดพลาดที่พบบ่อย
    """
    try:
        service = get_observability_service()
        metrics = service.get_metrics(time_window_hours)
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retrieval-analytics")
async def get_retrieval_analytics():
    """
    วิเคราะห์ประสิทธิภาพการค้นหา
    
    Analyze retrieval performance by strategy.
    """
    try:
        service = get_observability_service()
        analytics = service.get_retrieval_analytics()
        return {
            "success": True,
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces")
async def get_traces(limit: int = 100):
    """
    ดู traces ล่าสุด
    
    Get recent query traces.
    """
    try:
        service = get_observability_service()
        traces = service.traces[-limit:]
        return {
            "success": True,
            "total": len(traces),
            "traces": [t.to_dict() for t in traces]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_traces(format: str = "json"):
    """
    ส่งออก traces สำหรับวิเคราะห์
    
    Export traces for analysis.
    
    - format: json หรือ csv
    """
    try:
        service = get_observability_service()
        data = service.export_traces(format)
        return {
            "success": True,
            "format": format,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    ตรวจสอบสถานะระบบ
    
    System health check.
    """
    return {
        "status": "healthy",
        "timestamp": "2026-03-08T11:00:00",
        "version": "2.0.0",
        "features": {
            "hybrid_search": True,
            "reranking": True,
            "context_compression": True,
            "observability": True
        }
    }
