"""
Graph RAG API Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.graph_rag import get_graph_rag_service
from app.services.vector_store_langchain import get_vector_store_service

router = APIRouter(prefix="/graph-rag", tags=["Graph RAG"])


class GraphQueryRequest(BaseModel):
    query: str
    collection_name: str = "hr_documents"
    k: int = 5
    graph_depth: int = 2


@router.post("/retrieve")
async def graph_retrieve(request: GraphQueryRequest):
    """
    Graph-enhanced retrieval
    
    ค้นหาด้วย Knowledge Graph
    """
    try:
        service = get_graph_rag_service()
        
        # Build graph if not built
        if not service._built:
            # Get documents from vector store
            vector_store = get_vector_store_service()
            # Note: In production, load documents properly
            # For now, return message
            return {
                'success': False,
                'message': 'Graph not built yet. Call /build first.'
            }
        
        result = await service.retrieve(
            query=request.query,
            collection_name=request.collection_name,
            k=request.k,
            graph_depth=request.graph_depth
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_graph(collection_name: str = "hr_documents"):
    """
    Build knowledge graph from documents
    
    สร้าง Knowledge Graph จากเอกสาร
    """
    try:
        service = get_graph_rag_service()
        
        # Get documents
        vector_store = get_vector_store_service()
        # Query to get all documents
        docs = await vector_store.similarity_search(
            collection_name=collection_name,
            query="document",
            k=100  # Limit for now
        )
        
        if not docs:
            return {
                'success': False,
                'message': 'No documents found'
            }
        
        # Build graph
        await service.build_graph_from_documents(docs)
        
        stats = service.get_graph_stats()
        return {
            'success': True,
            'message': 'Graph built successfully',
            'stats': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats():
    """
    Get knowledge graph statistics
    
    ดูสถิติ Knowledge Graph
    """
    try:
        service = get_graph_rag_service()
        stats = service.get_graph_stats()
        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_graph():
    """
    Export graph for visualization
    
    ส่งออก Graph สำหรับ visualization
    """
    try:
        service = get_graph_rag_service()
        graph_data = service.export_graph()
        return {
            'success': True,
            'graph': graph_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
