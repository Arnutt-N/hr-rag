"""
Task Summarizer Skill - Summarize and manage tasks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


def summarize_tasks(
    tasks: List[Dict[str, Any]],
    group_by: str = "status",  # status, priority, assignee, date
    include_metrics: bool = True
) -> Dict[str, Any]:
    """
    สรุปรายการงาน (Task Summary)
    
    Args:
        tasks: รายการงาน [{"id", "title", "status", "priority", "assignee", "due_date", ...}]
        group_by: กลุ่มตาม (status, priority, assignee, date)
        include_metrics: รวมสถิติ
    
    Returns:
        สรุปงานพร้อมสถิติ
    """
    if not tasks:
        return {
            "success": True,
            "summary": "ไม่มีงาน",
            "total": 0,
            "grouped": {},
            "metrics": {}
        }
    
    # Group tasks
    grouped = defaultdict(list)
    for task in tasks:
        key = task.get(group_by, "unknown")
        grouped[key].append(task)
    
    # Calculate metrics
    metrics = {}
    if include_metrics:
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
        pending = sum(1 for t in tasks if t.get("status") == "pending")
        overdue = sum(1 for t in tasks if _is_overdue(t.get("due_date")))
        
        high_priority = sum(1 for t in tasks if t.get("priority") == "high")
        
        metrics = {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "overdue": overdue,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "high_priority_count": high_priority
        }
    
    # Generate summary text
    summary_text = _generate_summary_text(tasks, grouped, metrics)
    
    return {
        "success": True,
        "summary": summary_text,
        "total": len(tasks),
        "grouped_by": group_by,
        "groups": dict(grouped),
        "metrics": metrics
    }


def _is_overdue(due_date: Optional[str]) -> bool:
    """Check if task is overdue."""
    if not due_date:
        return False
    try:
        due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        return due < datetime.now()
    except:
        return False


def _generate_summary_text(
    tasks: List[Dict],
    grouped: Dict,
    metrics: Dict
) -> str:
    """Generate human-readable summary."""
    lines = [
        f"📊 สรุปงานทั้งหมด {metrics.get('total', len(tasks))} รายการ",
        ""
    ]
    
    if metrics:
        lines.extend([
            f"✅ เสร็จแล้ว: {metrics.get('completed', 0)} ({metrics.get('completion_rate', 0)}%)",
            f"🔄 กำลังทำ: {metrics.get('in_progress', 0)}",
            f"⏳ รอดำเนินการ: {metrics.get('pending', 0)}",
            f"⚠️ เลยกำหนด: {metrics.get('overdue', 0)}",
            f"🔴 ความสำคัญสูง: {metrics.get('high_priority_count', 0)}",
            ""
        ])
    
    lines.append("📋 แบ่งตามกลุ่ม:")
    for key, group_tasks in grouped.items():
        lines.append(f"  • {key}: {len(group_tasks)} งาน")
    
    return "\n".join(lines)


def analyze_task_patterns(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    วิเคราะห์รูปแบบงาน (Task Pattern Analysis)
    
    Args:
        tasks: รายการงาน
    
    Returns:
        การวิเคราะห์รูปแบบ
    """
    if not tasks:
        return {"success": True, "patterns": "ไม่มีข้อมูล"}
    
    # Time analysis
    completion_times = []
    for task in tasks:
        if task.get("status") == "completed" and task.get("started_at") and task.get("completed_at"):
            try:
                started = datetime.fromisoformat(task["started_at"].replace("Z", "+00:00"))
                completed = datetime.fromisoformat(task["completed_at"].replace("Z", "+00:00"))
                duration = (completed - started).total_seconds() / 3600  # hours
                completion_times.append(duration)
            except:
                pass
    
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
    
    # Bottleneck analysis
    bottleneck_status = None
    max_count = 0
    for status, group in _group_by(tasks, "status").items():
        if len(group) > max_count and status != "completed":
            max_count = len(group)
            bottleneck_status = status
    
    # Recommendations
    recommendations = []
    if metrics := _calculate_metrics(tasks):
        if metrics.get("overdue", 0) > 3:
            recommendations.append("มีงานเลยกำหนดหลายรายการ ควรรีบดำเนินการ")
        if metrics.get("completion_rate", 0) < 50:
            recommendations.append("อัตราการเสร็จต่ำ ควรตรวจสอบข้อจำกัด")
        if bottleneck_status:
            recommendations.append(f"สถานะ '{bottleneck_status}' มีงานค้างมาก ควรเร่งรัด")
    
    return {
        "success": True,
        "patterns": {
            "avg_completion_time_hours": round(avg_completion_time, 1),
            "bottleneck_status": bottleneck_status,
            "bottleneck_count": max_count if bottleneck_status else 0
        },
        "recommendations": recommendations,
        "insights": f"งานใช้เวลาเฉลี่ย {round(avg_completion_time, 1)} ชั่วโมง"
    }


def _group_by(tasks: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """Group tasks by key."""
    grouped = defaultdict(list)
    for task in tasks:
        grouped[task.get(key, "unknown")].append(task)
    return dict(grouped)


def _calculate_metrics(tasks: List[Dict]) -> Dict[str, Any]:
    """Calculate task metrics."""
    total = len(tasks)
    if total == 0:
        return {}
    
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    overdue = sum(1 for t in tasks if _is_overdue(t.get("due_date")))
    
    return {
        "total": total,
        "completed": completed,
        "completion_rate": round(completed / total * 100, 1),
        "overdue": overdue
    }


def generate_daily_report(tasks: List[Dict[str, Any]], date: Optional[str] = None) -> Dict[str, Any]:
    """
    สร้างรายงานประจำวัน (Daily Report)
    
    Args:
        tasks: รายการงาน
        date: วันที่ (YYYY-MM-DD)
    
    Returns:
        รายงานประจำวัน
    """
    report_date = date or datetime.now().strftime("%Y-%m-%d")
    
    # Filter tasks for the date
    today_tasks = [
        t for t in tasks
        if t.get("updated_at", "").startswith(report_date) or
           t.get("created_at", "").startswith(report_date)
    ]
    
    completed_today = [t for t in today_tasks if t.get("status") == "completed"]
    new_tasks = [t for t in today_tasks if t.get("created_at", "").startswith(report_date)]
    
    report = f"""📅 รายงานประจำวัน {report_date}

📝 งานวันนี้:
• งานใหม่: {len(new_tasks)} รายการ
• เสร็จสิ้น: {len(completed_today)} รายการ
• อัพเดท: {len(today_tasks)} รายการ

🏆 ความสำเร็จ:
{chr(10).join([f"  ✅ {t.get('title', 'Untitled')}" for t in completed_today[:5]])}

📋 งานพรุ่งนี้:
(ดูรายละเอียดในระบบ)
"""
    
    return {
        "success": True,
        "date": report_date,
        "report": report,
        "new_tasks": len(new_tasks),
        "completed_today": len(completed_today),
        "total_updated": len(today_tasks)
    }


# Skill info for registry
def get_info() -> Dict[str, str]:
    """Get skill information."""
    return {
        "name": "Task Summarizer",
        "version": "1.0.0",
        "description": "สรุปและวิเคราะห์รายการงาน (Task Summary & Analysis)",
        "author": "HR-RAG Team",
        "functions": [
            "summarize_tasks",
            "analyze_task_patterns",
            "generate_daily_report"
        ]
    }
