"""Admin Router - System Administration & Management

Protected endpoints for system administration:
- User Management (list, view, enable/disable, reset password, view history)
- System Analytics (stats, charts, most active users)
- Content Management (projects, documents, logs)
- Settings Management (LLM, rate limits, feature flags)
- Security (login attempts, auth tracking, API key usage)

Requires: Admin role
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr

from app.models.database import (
    User, Project, Document, ChatSession, ChatMessage,
    get_db, UserRole
)
from app.core.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ==================== DEPENDENCIES ====================

async def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role to access admin endpoints"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ==================== PAGINATION SCHEMA ====================

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


def paginate(items: List, total: int, page: int, page_size: int) -> PaginatedResponse:
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


# ==================== USER MANAGEMENT ====================

class UserDetailResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_member: bool
    is_active: bool
    preferred_llm_provider: str
    preferred_embedding_model: str
    created_at: datetime
    last_login: Optional[datetime]
    api_keys_count: int
    projects_count: int
    chat_sessions_count: int


class UserListItem(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_member: bool
    is_active: bool
    created_at: datetime
    projects_count: int
    chat_sessions_count: int


class PasswordResetRequest(BaseModel):
    user_id: int
    new_password: str


class UserStatusUpdate(BaseModel):
    user_id: int
    is_active: bool


@router.get("/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination and filters"""
    query = select(User)
    count_query = select(func.count(User.id))
    
    # Apply filters
    conditions = []
    if search:
        # Use parameterized query to prevent SQL injection
        search_lower = search.lower()
        conditions.append(or_(
            func.lower(User.email).contains(search_lower),
            func.lower(User.username).contains(search_lower),
            func.lower(User.full_name).contains(search_lower)
        ))
    if role:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total = await db.scalar(count_query)
    
    # Get paginated results with counts
    offset = (page - 1) * page_size
    query = query.order_by(desc(User.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get counts for each user
    user_items = []
    for user in users:
        # Count projects
        projects_count = await db.scalar(
            select(func.count(Project.id)).where(Project.owner_id == user.id)
        )
        # Count chat sessions
        sessions_count = await db.scalar(
            select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
        )
        
        user_items.append({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value if user.role else "user",
            "is_member": user.is_member,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "projects_count": projects_count or 0,
            "chat_sessions_count": sessions_count or 0,
        })
    
    return paginate(user_items, total or 0, page, page_size)


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_details(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user information"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count projects
    projects_count = await db.scalar(
        select(func.count(Project.id)).where(Project.owner_id == user.id)
    )
    
    # Count chat sessions
    sessions_count = await db.scalar(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
    )
    
    # For API keys count - would need to check keys table
    # Assuming 0 for now unless there's a keys relationship
    api_keys_count = 0
    
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value if user.role else "user",
        is_member=user.is_member,
        is_active=user.is_active,
        preferred_llm_provider=user.preferred_llm_provider.value if user.preferred_llm_provider else "openai",
        preferred_embedding_model=user.preferred_embedding_model,
        created_at=user.created_at,
        last_login=user.updated_at,  # Using updated_at as proxy for last activity
        api_keys_count=api_keys_count,
        projects_count=projects_count or 0,
        chat_sessions_count=sessions_count or 0,
    )


@router.post("/users/reset-password")
async def reset_user_password(
    payload: PasswordResetRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reset user password"""
    result = await db.execute(
        select(User).where(User.id == payload.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/users/toggle-status")
async def toggle_user_status(
    payload: UserStatusUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Enable or disable a user"""
    result = await db.execute(
        select(User).where(User.id == payload.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = payload.is_active
    await db.commit()
    
    return {"message": f"User {'enabled' if payload.is_active else 'disabled'}"}


@router.get("/users/{user_id}/chat-sessions", response_model=PaginatedResponse)
async def get_user_chat_sessions(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat history"""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get sessions
    count_query = select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
    total = await db.scalar(count_query)
    
    offset = (page - 1) * page_size
    query = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    session_items = []
    for session in sessions:
        # Get last message preview
        last_msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        
        # Count messages
        msg_count = await db.scalar(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        
        session_items.append({
            "id": session.id,
            "title": session.title,
            "project_id": session.project_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": msg_count or 0,
            "last_message": last_msg.content[:100] if last_msg else None,
        })
    
    return paginate(session_items, total or 0, page, page_size)


@router.get("/users/{user_id}/projects", response_model=PaginatedResponse)
async def get_user_projects(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user's projects"""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    
    count_query = select(func.count(Project.id)).where(Project.owner_id == user_id)
    total = await db.scalar(count_query)
    
    offset = (page - 1) * page_size
    query = (
        select(Project)
        .where(Project.owner_id == user_id)
        .order_by(desc(Project.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    projects = result.scalars().all()
    
    project_items = []
    for project in projects:
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(Document.project_id == project.id)
        )
        session_count = await db.scalar(
            select(func.count(ChatSession.id)).where(ChatSession.project_id == project.id)
        )
        
        project_items.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "is_public": project.is_public,
            "vector_collection": project.vector_collection,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "document_count": doc_count or 0,
            "chat_session_count": session_count or 0,
        })
    
    return paginate(project_items, total or 0, page, page_size)


# ==================== SYSTEM ANALYTICS ====================

class SystemStats(BaseModel):
    total_users: int
    total_members: int
    total_projects: int
    total_documents: int
    total_chat_sessions: int
    total_chat_messages: int


class DailyStat(BaseModel):
    date: str
    queries: int
    sessions: int
    new_users: int
    new_documents: int


class AnalyticsOverview(BaseModel):
    stats: SystemStats
    daily_stats: List[DailyStat]
    top_active_users: List[dict]
    top_llm_providers: List[dict]


@router.get("/analytics", response_model=AnalyticsOverview)
async def get_system_analytics(
    days: int = Query(30, ge=7, le=90),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system analytics overview"""
    
    # Basic stats
    total_users = await db.scalar(select(func.count(User.id)))
    total_members = await db.scalar(select(func.count(User.id)).where(User.is_member == True))
    total_projects = await db.scalar(select(func.count(Project.id)))
    total_documents = await db.scalar(select(func.count(Document.id)))
    total_chat_sessions = await db.scalar(select(func.count(ChatSession.id)))
    total_chat_messages = await db.scalar(select(func.count(ChatMessage.id)))
    
    stats = SystemStats(
        total_users=total_users or 0,
        total_members=total_members or 0,
        total_projects=total_projects or 0,
        total_documents=total_documents or 0,
        total_chat_sessions=total_chat_sessions or 0,
        total_chat_messages=total_chat_messages or 0,
    )
    
    # Daily stats for the past N days
    daily_stats = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Count queries (chat messages from users)
        queries = await db.scalar(
            select(func.count(ChatMessage.id))
            .where(
                and_(
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= start_of_day,
                    ChatMessage.created_at < end_of_day
                )
            )
        )
        
        # Count sessions
        sessions = await db.scalar(
            select(func.count(ChatSession.id))
            .where(
                and_(
                    ChatSession.created_at >= start_of_day,
                    ChatSession.created_at < end_of_day
                )
            )
        )
        
        # Count new users
        new_users = await db.scalar(
            select(func.count(User.id))
            .where(
                and_(
                    User.created_at >= start_of_day,
                    User.created_at < end_of_day
                )
            )
        )
        
        # Count new documents
        new_docs = await db.scalar(
            select(func.count(Document.id))
            .where(
                and_(
                    Document.created_at >= start_of_day,
                    Document.created_at < end_of_day
                )
            )
        )
        
        daily_stats.append(DailyStat(
            date=date_str,
            queries=queries or 0,
            sessions=sessions or 0,
            new_users=new_users or 0,
            new_documents=new_docs or 0,
        ))
    
    daily_stats.reverse()
    
    # Top active users (by chat messages)
    top_users_query = (
        select(User.id, User.username, User.email, func.count(ChatMessage.id).label("msg_count"))
        .join(ChatMessage, ChatMessage.user_id == User.id)
        .group_by(User.id, User.username, User.email)
        .order_by(desc("msg_count"))
        .limit(10)
    )
    result = await db.execute(top_users_query)
    top_users = []
    for row in result.all():
        top_users.append({
            "user_id": row.id,
            "username": row.username,
            "email": row.email,
            "message_count": row.msg_count,
        })
    
    # Top LLM providers (by chat messages)
    top_providers_query = (
        select(ChatMessage.llm_provider, func.count(ChatMessage.id).label("count"))
        .where(ChatMessage.llm_provider.isnot(None))
        .group_by(ChatMessage.llm_provider)
        .order_by(desc("count"))
    )
    result = await db.execute(top_providers_query)
    top_providers = []
    for row in result.all():
        if row.llm_provider:
            top_providers.append({
                "provider": row.llm_provider,
                "count": row.count,
            })
    
    return AnalyticsOverview(
        stats=stats,
        daily_stats=daily_stats,
        top_active_users=top_users,
        top_llm_providers=top_providers,
    )


@router.get("/analytics/queries")
async def get_query_stats(
    period: str = Query("day", regex="^(day|week|month)$"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get query statistics per day/week/month"""
    
    if period == "day":
        # Last 30 days hourly or daily
        days = 30
        date_format = "%Y-%m-%d"
    elif period == "week":
        # Last 12 weeks
        days = 84
        date_format = "%Y-W%W"
    else:
        # Last 12 months
        days = 365
        date_format = "%Y-%m"
    
    results = []
    for i in range(min(days, 30 if period == "day" else (12 if period == "week" else 12))):
        date = datetime.utcnow() - timedelta(days=i)
        
        if period == "day":
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            label = date.strftime("%Y-%m-%d")
        elif period == "week":
            start = date - timedelta(days=date.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            label = date.strftime("%Y-W%W")
        else:
            start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
            label = date.strftime("%Y-%m")
        
        count = await db.scalar(
            select(func.count(ChatMessage.id))
            .where(
                and_(
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= start,
                    ChatMessage.created_at < end
                )
            )
        )
        
        results.append({"period": label, "count": count or 0})
    
    results.reverse()
    return {"period": period, "data": results}


# ==================== CONTENT MANAGEMENT ====================

class ProjectListItem(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    owner_email: str
    is_public: bool
    vector_collection: str
    created_at: datetime
    document_count: int
    chat_session_count: int


class DocumentListItem(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    project_id: int
    project_name: str
    owner_email: str
    is_indexed: bool
    chunk_count: int
    created_at: datetime


@router.get("/projects", response_model=PaginatedResponse)
async def list_all_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all projects across all users"""
    query = (
        select(Project)
        .join(User, Project.owner_id == User.id)
        .options(selectinload(Project.owner))
    )
    count_query = select(func.count(Project.id))
    
    if search:
        # Use parameterized query to prevent SQL injection
        search_lower = search.lower()
        search_filter = or_(
            func.lower(Project.name).contains(search_lower),
            func.lower(Project.description).contains(search_lower),
            func.lower(User.email).contains(search_lower)
        )
        query = query.where(search_filter)
        count_query = count_query.join(User).where(search_filter)
    
    total = await db.scalar(count_query)
    
    offset = (page - 1) * page_size
    query = query.order_by(desc(Project.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    projects = result.scalars().all()
    
    items = []
    for project in projects:
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(Document.project_id == project.id)
        )
        session_count = await db.scalar(
            select(func.count(ChatSession.id)).where(ChatSession.project_id == project.id)
        )
        
        # Get owner email
        owner_result = await db.execute(select(User).where(User.id == project.owner_id))
        owner = owner_result.scalar_one_or_none()
        
        items.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "owner_email": owner.email if owner else "Unknown",
            "is_public": project.is_public,
            "vector_collection": project.vector_collection,
            "created_at": project.created_at,
            "document_count": doc_count or 0,
            "chat_session_count": session_count or 0,
        })
    
    return paginate(items, total or 0, page, page_size)


@router.get("/documents", response_model=PaginatedResponse)
async def list_all_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    file_type: Optional[str] = None,
    project_id: Optional[int] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all documents across all users"""
    query = (
        select(Document)
        .join(Project, Document.project_id == Project.id)
        .join(User, Project.owner_id == User.id)
    )
    count_query = select(func.count(Document.id))
    
    conditions = []
    if search:
        # Use parameterized query to prevent SQL injection
        search_lower = search.lower()
        conditions.append(or_(
            func.lower(Document.filename).contains(search_lower),
            func.lower(Document.original_filename).contains(search_lower),
            func.lower(Document.content).contains(search_lower)
        ))
    if file_type:
        conditions.append(Document.file_type == file_type)
    if project_id:
        conditions.append(Document.project_id == project_id)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.join(Project).where(and_(*conditions))
    
    total = await db.scalar(count_query)
    
    offset = (page - 1) * page_size
    query = query.order_by(desc(Document.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    items = []
    for doc in documents:
        # Get project and owner
        project_result = await db.execute(select(Project).where(Project.id == doc.project_id))
        project = project_result.scalar_one_or_none()
        
        owner_email = "Unknown"
        if project:
            owner_result = await db.execute(select(User).where(User.id == project.owner_id))
            owner = owner_result.scalar_one_or_none()
            owner_email = owner.email if owner else "Unknown"
        
        items.append({
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "project_id": doc.project_id,
            "project_name": project.name if project else "Unknown",
            "owner_email": owner_email,
            "is_indexed": doc.is_indexed,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at,
        })
    
    return paginate(items, total or 0, page, page_size)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}


# ==================== SYSTEM SETTINGS ====================

class SystemSettings(BaseModel):
    default_llm_provider: str
    default_embedding_model: str
    system_rate_limit: int
    maintenance_mode: bool
    feature_flags: dict


# In-memory settings (in production, store in database)
_system_settings = {
    "default_llm_provider": "openai",
    "default_embedding_model": "BAAI/bge-m3",
    "system_rate_limit": 100,
    "maintenance_mode": False,
    "feature_flags": {
        "guest_access": True,
        "public_projects": True,
        "api_key_management": True,
        "evaluation": True,
    }
}


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(
    admin: User = Depends(require_admin)
):
    """Get system settings"""
    return SystemSettings(**_system_settings)


@router.post("/settings")
async def update_system_settings(
    settings: SystemSettings,
    admin: User = Depends(require_admin)
):
    """Update system settings"""
    global _system_settings
    _system_settings = settings.dict()
    return {"message": "Settings updated successfully"}


# ==================== SECURITY & LOGS ====================

class LoginAttempt(BaseModel):
    id: int
    user_id: Optional[int]
    username: str
    success: bool
    ip_address: Optional[str]
    timestamp: datetime


class LogEntry(BaseModel):
    id: int
    level: str
    message: str
    user_id: Optional[int]
    endpoint: Optional[str]
    timestamp: datetime


# In-memory logs (in production, store in database)
_login_attempts: List[LoginAttempt] = []
_system_logs: List[LogEntry] = []


def log_login_attempt(username: str, success: bool, user_id: Optional[int] = None, ip: Optional[str] = None):
    """Log a login attempt - called from auth router"""
    attempt = LoginAttempt(
        id=len(_login_attempts) + 1,
        user_id=user_id,
        username=username,
        success=success,
        ip_address=ip,
        timestamp=datetime.utcnow()
    )
    _login_attempts.append(attempt)
    # Keep only last 1000 attempts
    if len(_login_attempts) > 1000:
        _login_attempts.pop(0)


def log_system_event(level: str, message: str, user_id: Optional[int] = None, endpoint: Optional[str] = None):
    """Log a system event"""
    entry = LogEntry(
        id=len(_system_logs) + 1,
        level=level,
        message=message,
        user_id=user_id,
        endpoint=endpoint,
        timestamp=datetime.utcnow()
    )
    _system_logs.append(entry)
    # Keep only last 1000 logs
    if len(_system_logs) > 1000:
        _system_logs.pop(0)


@router.get("/security/login-attempts", response_model=PaginatedResponse)
async def get_login_attempts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    success: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get login attempts log"""
    # For now, return in-memory logs
    # In production, query from database
    filtered = _login_attempts
    if success is not None:
        filtered = [a for a in filtered if a.success == success]
    
    total = len(filtered)
    offset = (page - 1) * page_size
    items = filtered[offset:offset + page_size]
    
    return paginate([a.dict() for a in items], total, page, page_size)


@router.get("/logs", response_model=PaginatedResponse)
async def get_system_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    level: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system logs"""
    filtered = _system_logs
    if level:
        filtered = [l for l in filtered if l.level == level]
    
    total = len(filtered)
    offset = (page - 1) * page_size
    items = filtered[offset:offset + page_size]
    
    return paginate([l.dict() for l in items], total, page, page_size)


# ==================== EXPORT DATA ====================

@router.get("/export/users")
async def export_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export all users as CSV"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    csv_lines = ["id,email,username,full_name,role,is_member,is_active,created_at"]
    for user in users:
        csv_lines.append(
            f"{user.id},{user.email},{user.username},{user.full_name or ''},"
            f"{user.role.value if user.role else 'user'},{user.is_member},{user.is_active},{user.created_at}"
        )
    
    return {"csv": "\n".join(csv_lines)}


@router.get("/export/documents")
async def export_documents(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export all documents as CSV"""
    result = await db.execute(
        select(Document)
        .join(Project)
        .join(User)
    )
    docs = result.scalars().all()
    
    csv_lines = ["id,filename,original_filename,file_type,file_size,project_id,owner_email,is_indexed,created_at"]
    for doc in docs:
        csv_lines.append(
            f"{doc.id},{doc.filename},{doc.original_filename},{doc.file_type},"
            f"{doc.file_size},{doc.project_id},{doc.owner_email if hasattr(doc, 'owner_email') else ''},"
            f"{doc.is_indexed},{doc.created_at}"
        )
    
    return {"csv": "\n".join(csv_lines)}
