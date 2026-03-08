# ==================== KNOWLEDGE BASE MANAGEMENT ====================
# Central RAG repository for HR documents

class KnowledgeCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None


class KnowledgeCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    slug: str
    parent_id: Optional[int]
    is_active: bool
    document_count: int
    created_at: datetime


class KnowledgeDocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    doc_type: Optional[str] = None  # policy, handbook, guideline, procedure
    department: Optional[str] = None
    tags: List[str] = []
    is_public: bool = True
    allowed_roles: List[str] = ["admin", "member", "user"]
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    category_id: Optional[int]
    category_name: Optional[str]
    doc_type: Optional[str]
    department: Optional[str]
    tags: List[str]
    is_public: bool
    is_indexed: bool
    chunk_count: int
    language: str
    version: str
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseStats(BaseModel):
    total_documents: int
    total_categories: int
    indexed_documents: int
    total_chunks: int
    by_category: List[dict]
    by_doc_type: List[dict]


# -------------------- CATEGORY MANAGEMENT --------------------

@router.post("/knowledge/categories", response_model=KnowledgeCategoryResponse)
async def create_knowledge_category(
    payload: KnowledgeCategoryCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new knowledge category"""
    # Auto-generate slug if not provided
    slug = payload.slug or payload.name.lower().replace(" ", "-").replace("_", "-")
    
    # Check for duplicate slug
    existing = await db.scalar(select(KnowledgeCategory).where(KnowledgeCategory.slug == slug))
    if existing:
        raise HTTPException(status_code=400, detail="Category slug already exists")
    
    category = KnowledgeCategory(
        name=payload.name,
        description=payload.description,
        slug=slug,
        parent_id=payload.parent_id,
        is_active=True
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    # Count documents
    doc_count = await db.scalar(
        select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.category_id == category.id)
    )
    
    return KnowledgeCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        parent_id=category.parent_id,
        is_active=category.is_active,
        document_count=doc_count or 0,
        created_at=category.created_at
    )


@router.get("/knowledge/categories", response_model=List[KnowledgeCategoryResponse])
async def list_knowledge_categories(
    include_inactive: bool = False,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all knowledge categories"""
    query = select(KnowledgeCategory)
    if not include_inactive:
        query = query.where(KnowledgeCategory.is_active == True)
    query = query.order_by(KnowledgeCategory.name)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    response = []
    for cat in categories:
        doc_count = await db.scalar(
            select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.category_id == cat.id)
        )
        response.append(KnowledgeCategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            slug=cat.slug,
            parent_id=cat.parent_id,
            is_active=cat.is_active,
            document_count=doc_count or 0,
            created_at=cat.created_at
        ))
    
    return response


@router.put("/knowledge/categories/{category_id}", response_model=KnowledgeCategoryResponse)
async def update_knowledge_category(
    category_id: int,
    payload: KnowledgeCategoryCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a knowledge category"""
    result = await db.execute(
        select(KnowledgeCategory).where(KnowledgeCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category.name = payload.name
    category.description = payload.description
    if payload.slug:
        category.slug = payload.slug
    if payload.parent_id is not None:
        category.parent_id = payload.parent_id
    
    await db.commit()
    await db.refresh(category)
    
    doc_count = await db.scalar(
        select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.category_id == category.id)
    )
    
    return KnowledgeCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        parent_id=category.parent_id,
        is_active=category.is_active,
        document_count=doc_count or 0,
        created_at=category.created_at
    )


@router.delete("/knowledge/categories/{category_id}")
async def delete_knowledge_category(
    category_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge category (soft delete by setting inactive)"""
    result = await db.execute(
        select(KnowledgeCategory).where(KnowledgeCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has documents
    doc_count = await db.scalar(
        select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.category_id == category_id)
    )
    
    if doc_count > 0:
        # Soft delete - set inactive
        category.is_active = False
        await db.commit()
        return {"message": f"Category deactivated (has {doc_count} documents)"}
    else:
        # Hard delete if no documents
        await db.delete(category)
        await db.commit()
        return {"message": "Category deleted successfully"}


# -------------------- DOCUMENT MANAGEMENT --------------------

@router.get("/knowledge/documents", response_model=PaginatedResponse)
async def list_knowledge_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    doc_type: Optional[str] = None,
    department: Optional[str] = None,
    is_indexed: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all knowledge base documents"""
    query = select(KnowledgeDocument).options(selectinload(KnowledgeDocument.category))
    count_query = select(func.count(KnowledgeDocument.id))
    
    conditions = []
    if search:
        search_lower = search.lower()
        conditions.append(or_(
            func.lower(KnowledgeDocument.title).contains(search_lower),
            func.lower(KnowledgeDocument.description).contains(search_lower),
            func.lower(KnowledgeDocument.content).contains(search_lower)
        ))
    if category_id:
        conditions.append(KnowledgeDocument.category_id == category_id)
    if doc_type:
        conditions.append(KnowledgeDocument.doc_type == doc_type)
    if department:
        conditions.append(KnowledgeDocument.department == department)
    if is_indexed is not None:
        conditions.append(KnowledgeDocument.is_indexed == is_indexed)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    total = await db.scalar(count_query)
    
    offset = (page - 1) * page_size
    query = query.order_by(desc(KnowledgeDocument.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    items = []
    for doc in documents:
        items.append({
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "category_id": doc.category_id,
            "category_name": doc.category.name if doc.category else None,
            "doc_type": doc.doc_type,
            "department": doc.department,
            "tags": doc.tags or [],
            "is_public": doc.is_public,
            "is_indexed": doc.is_indexed,
            "chunk_count": doc.chunk_count,
            "language": doc.language,
            "version": doc.version,
            "effective_date": doc.effective_date,
            "expiry_date": doc.expiry_date,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })
    
    return paginate(items, total or 0, page, page_size)


@router.get("/knowledge/documents/{document_id}")
async def get_knowledge_document(
    document_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed knowledge document"""
    result = await db.execute(
        select(KnowledgeDocument).options(selectinload(KnowledgeDocument.category))
        .where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "filename": doc.filename,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "content": doc.content[:5000] if doc.content else None,  # Limit content preview
        "content_summary": doc.content_summary,
        "category_id": doc.category_id,
        "category_name": doc.category.name if doc.category else None,
        "doc_type": doc.doc_type,
        "department": doc.department,
        "tags": doc.tags or [],
        "is_public": doc.is_public,
        "allowed_roles": doc.allowed_roles or [],
        "is_indexed": doc.is_indexed,
        "chunk_count": doc.chunk_count,
        "vector_ids": doc.vector_ids or [],
        "language": doc.language,
        "version": doc.version,
        "effective_date": doc.effective_date,
        "expiry_date": doc.expiry_date,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }


@router.put("/knowledge/documents/{document_id}")
async def update_knowledge_document(
    document_id: int,
    payload: KnowledgeDocumentCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update knowledge document metadata"""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.title = payload.title
    doc.description = payload.description
    doc.category_id = payload.category_id
    doc.doc_type = payload.doc_type
    doc.department = payload.department
    doc.tags = payload.tags
    doc.is_public = payload.is_public
    doc.allowed_roles = payload.allowed_roles
    doc.effective_date = payload.effective_date
    doc.expiry_date = payload.expiry_date
    
    await db.commit()
    await db.refresh(doc)
    
    return {"message": "Document updated successfully", "document_id": doc.id}


@router.delete("/knowledge/documents/{document_id}")
async def delete_knowledge_document(
    document_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge document"""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # TODO: Also delete vectors from Qdrant
    # vector_store.delete_vectors(doc.vector_ids)
    
    await db.delete(doc)
    await db.commit()
    
    return {"message": "Document deleted successfully"}


# -------------------- STATISTICS & ANALYTICS --------------------

@router.get("/knowledge/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get knowledge base statistics"""
    total_docs = await db.scalar(select(func.count(KnowledgeDocument.id)))
    total_categories = await db.scalar(select(func.count(KnowledgeCategory.id)))
    indexed_docs = await db.scalar(
        select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.is_indexed == True)
    )
    total_chunks = await db.scalar(select(func.sum(KnowledgeDocument.chunk_count))) or 0
    
    # By category
    by_category = []
    cat_result = await db.execute(
        select(KnowledgeCategory.id, KnowledgeCategory.name, func.count(KnowledgeDocument.id))
        .outerjoin(KnowledgeDocument, KnowledgeDocument.category_id == KnowledgeCategory.id)
        .group_by(KnowledgeCategory.id, KnowledgeCategory.name)
    )
    for row in cat_result.all():
        by_category.append({
            "category_id": row[0],
            "category_name": row[1],
            "document_count": row[2] or 0
        })
    
    # By document type
    by_doc_type = []
    type_result = await db.execute(
        select(KnowledgeDocument.doc_type, func.count(KnowledgeDocument.id))
        .group_by(KnowledgeDocument.doc_type)
    )
    for row in type_result.all():
        if row[0]:  # Skip null
            by_doc_type.append({
                "doc_type": row[0],
                "document_count": row[1] or 0
            })
    
    return KnowledgeBaseStats(
        total_documents=total_docs or 0,
        total_categories=total_categories or 0,
        indexed_documents=indexed_docs or 0,
        total_chunks=total_chunks,
        by_category=by_category,
        by_doc_type=by_doc_type
    )


@router.get("/knowledge/doc-types")
async def list_document_types(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List available document types"""
    # Predefined types + custom types from database
    predefined = ["policy", "handbook", "guideline", "procedure", "regulation", 
                  "memo", "announcement", "training", "form", "other"]
    
    result = await db.execute(
        select(KnowledgeDocument.doc_type).distinct()
        .where(KnowledgeDocument.doc_type.isnot(None))
    )
    db_types = [row[0] for row in result.all() if row[0]]
    
    all_types = list(set(predefined + db_types))
    return {"doc_types": sorted(all_types)}


@router.get("/knowledge/departments")
async def list_departments(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List departments from documents"""
    predefined = ["HR", "IT", "Finance", "Legal", "Operations", "Marketing", 
                  "Sales", "Admin", "General"]
    
    result = await db.execute(
        select(KnowledgeDocument.department).distinct()
        .where(KnowledgeDocument.department.isnot(None))
    )
    db_depts = [row[0] for row in result.all() if row[0]]
    
    all_depts = list(set(predefined + db_depts))
    return {"departments": sorted(all_depts)}# -------------------- KNOWLEDGE BASE UPLOAD --------------------

from fastapi import File, Form, UploadFile
from app.services.knowledge_base import knowledge_base_service

@router.post("/knowledge/documents/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    doc_type: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    tags: str = Form(""),  # Comma-separated
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document to knowledge base"""
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    # Upload document
    doc = await knowledge_base_service.upload_document(
        file=file,
        title=title,
        description=description,
        category_id=category_id,
        doc_type=doc_type,
        department=department,
        tags=tag_list,
        created_by=admin.id,
        db=db
    )
    
    return {
        "message": "Document uploaded successfully",
        "document_id": doc.id,
        "title": doc.title,
        "file_size": doc.file_size,
        "is_indexed": doc.is_indexed
    }


@router.post("/knowledge/documents/{document_id}/index")
async def index_knowledge_document(
    document_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Index a document to vector database"""
    result = await knowledge_base_service.index_document(document_id, db)
    return result


@router.post("/knowledge/reindex-all")
async def reindex_all_knowledge_documents(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reindex all knowledge base documents"""
    result = await knowledge_base_service.reindex_all_documents(db)
    return result


@router.post("/knowledge/search")
async def search_knowledge_base(
    query: str,
    category_id: Optional[int] = None,
    doc_type: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    admin: User = Depends(require_admin)
):
    """Search knowledge base (admin only)"""
    results = await knowledge_base_service.search_knowledge_base(
        query=query,
        category_id=category_id,
        doc_type=doc_type,
        department=department,
        limit=limit,
        user_role="admin"
    )
    return {"query": query, "results": results}