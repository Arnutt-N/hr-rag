"""
Advanced Retrieval Service - Hybrid Search + Reranking + Context Compression
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from langchain_core.documents import Document

from app.services.vector_store_langchain import get_vector_store_service
from app.services.llm.langchain_service import get_llm_service


class AdvancedRetrievalService:
    """
    Advanced retrieval with:
    - Hybrid Search (Vector + Keyword)
    - Reranking (Cross-encoder)
    - Context Compression
    - Query Expansion
    """
    
    def __init__(self):
        self.vector_store = get_vector_store_service()
        self.llm_service = get_llm_service()
        
    async def hybrid_search(
        self,
        query: str,
        collection_name: str,
        k: int = 10,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and keyword search.
        
        Args:
            query: Search query
            collection_name: Collection to search
            k: Number of results
            keyword_weight: Weight for keyword search (0-1)
            vector_weight: Weight for vector search (0-1)
        
        Returns:
            Ranked documents with combined scores
        """
        # 1. Vector Search (Semantic)
        vector_results = await self.vector_store.similarity_search_with_score(
            collection_name=collection_name,
            query=query,
            k=k * 2  # Get more for reranking
        )
        
        # 2. Keyword Search (Lexical)
        keyword_results = await self._keyword_search(
            collection_name=collection_name,
            query=query,
            k=k * 2
        )
        
        # 3. Merge and score
        merged_results = self._merge_search_results(
            vector_results=vector_results,
            keyword_results=keyword_results,
            keyword_weight=keyword_weight,
            vector_weight=vector_weight
        )
        
        # 4. Rerank with cross-encoder
        reranked_results = await self._rerank_documents(query, merged_results[:k*2])
        
        return reranked_results[:k]
    
    async def _keyword_search(
        self,
        collection_name: str,
        query: str,
        k: int
    ) -> List[Tuple[Document, float]]:
        """
        Simple keyword-based search.
        
        Note: In production, use Elasticsearch or Meilisearch
        """
        # Get all documents (in production, use filtered search)
        # This is a simplified version
        all_docs = await self.vector_store.similarity_search(
            collection_name=collection_name,
            query=query,
            k=50  # Get more for keyword filtering
        )
        
        # Simple keyword matching score
        query_terms = query.lower().split()
        results = []
        
        for doc in all_docs:
            content = doc.page_content.lower()
            score = sum(1 for term in query_terms if term in content)
            score = score / len(query_terms) if query_terms else 0
            results.append((doc, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def _merge_search_results(
        self,
        vector_results: List[Tuple[Document, float]],
        keyword_results: List[Tuple[Document, float]],
        keyword_weight: float,
        vector_weight: float
    ) -> List[Dict[str, Any]]:
        """Merge and normalize scores from both search methods."""
        
        # Normalize scores to 0-1
        def normalize_scores(results: List[Tuple[Document, float]]) -> Dict[str, float]:
            if not results:
                return {}
            max_score = max(r[1] for r in results)
            min_score = min(r[1] for r in results)
            score_range = max_score - min_score if max_score != min_score else 1
            
            return {
                self._doc_id(r[0]): (r[1] - min_score) / score_range
                for r in results
            }
        
        vector_scores = normalize_scores(vector_results)
        keyword_scores = normalize_scores(keyword_results)
        
        # Combine scores
        all_doc_ids = set(vector_scores.keys()) | set(keyword_scores.keys())
        
        merged = []
        for doc_id in all_doc_ids:
            v_score = vector_scores.get(doc_id, 0)
            k_score = keyword_scores.get(doc_id, 0)
            
            combined_score = (vector_weight * v_score) + (keyword_weight * k_score)
            
            # Get document
            doc = None
            for d, _ in vector_results + keyword_results:
                if self._doc_id(d) == doc_id:
                    doc = d
                    break
            
            if doc:
                merged.append({
                    "document": doc,
                    "combined_score": combined_score,
                    "vector_score": v_score,
                    "keyword_score": k_score
                })
        
        # Sort by combined score
        merged.sort(key=lambda x: x["combined_score"], reverse=True)
        return merged
    
    async def _rerank_documents(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using LLM-based scoring.
        
        In production, use dedicated reranking model like:
        - Cohere Rerank
        - Cross-Encoder (sentence-transformers)
        - ColBERT
        """
        if not candidates:
            return candidates
        
        reranked = []
        
        for item in candidates:
            doc = item["document"]
            
            # Simple relevance scoring using LLM
            prompt = f"""Rate relevance (0-10):
Query: {query}
Document: {doc.page_content[:500]}

Relevance score (0-10):"""
            
            try:
                score_text = await self.llm_service.chat([
                    {"role": "user", "content": prompt}
                ])
                
                # Extract number
                import re
                numbers = re.findall(r'\d+', score_text)
                rerank_score = int(numbers[0]) if numbers else 5
                rerank_score = max(0, min(10, rerank_score)) / 10  # Normalize to 0-1
                
            except:
                rerank_score = item["combined_score"]
            
            # Combine original score with rerank score
            final_score = (0.7 * rerank_score) + (0.3 * item["combined_score"])
            
            reranked.append({
                **item,
                "rerank_score": rerank_score,
                "final_score": final_score
            })
        
        # Sort by final score
        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked
    
    async def compress_context(
        self,
        query: str,
        documents: List[Document],
        max_tokens: int = 4000
    ) -> str:
        """
        Compress multiple documents into focused context.
        
        Args:
            query: Original query
            documents: Retrieved documents
            max_tokens: Maximum tokens for context
        
        Returns:
            Compressed context string
        """
        if not documents:
            return ""
        
        # If short enough, return as-is
        total_length = sum(len(d.page_content) for d in documents)
        if total_length < max_tokens * 4:  # Rough estimate: 1 token ≈ 4 chars
            return "\n\n".join([f"[Doc {i+1}] {d.page_content}" 
                              for i, d in enumerate(documents)])
        
        # Compress each document to key points
        compressed_parts = []
        
        for i, doc in enumerate(documents[:5]):  # Limit to top 5
            prompt = f"""Extract key points relevant to: {query}

Document:
{doc.page_content[:1000]}

Key points (2-3 bullet points):"""
            
            try:
                key_points = await self.llm_service.chat([
                    {"role": "user", "content": prompt}
                ])
                
                compressed_parts.append(f"[Doc {i+1}] {key_points}")
                
            except:
                # Fallback to truncation
                compressed_parts.append(f"[Doc {i+1}] {doc.page_content[:500]}...")
        
        return "\n\n".join(compressed_parts)
    
    async def expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms.
        
        Improves recall by searching with multiple variations.
        """
        prompt = f"""Generate 3 alternative phrasings for:
"{query}"

Consider:
- Synonyms
- Different ways to ask
- Formal vs informal

Return only the queries, one per line:"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            # Parse variations
            variations = [line.strip() for line in response.split('\n') 
                         if line.strip() and not line.strip().startswith('-')]
            
            # Add original
            variations = [query] + variations[:3]
            
            return variations
            
        except:
            return [query]
    
    async def retrieve_with_expansion(
        self,
        query: str,
        collection_name: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve using query expansion for better recall.
        """
        # Expand query
        expanded_queries = await self.expand_query(query)
        
        # Search with each variation
        all_results = []
        for q in expanded_queries:
            results = await self.hybrid_search(
                query=q,
                collection_name=collection_name,
                k=k
            )
            all_results.extend(results)
        
        # Deduplicate and rerank
        seen_ids = set()
        unique_results = []
        
        for r in all_results:
            doc_id = self._doc_id(r["document"])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(r)
        
        # Sort by final score
        unique_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return unique_results[:k]
    
    def _doc_id(self, doc: Document) -> str:
        """Generate unique ID for document."""
        content_hash = hash(doc.page_content[:100])
        source = doc.metadata.get("source", "unknown")
        return f"{source}_{content_hash}"


# Singleton
_advanced_retrieval: Optional[AdvancedRetrievalService] = None


def get_advanced_retrieval_service() -> AdvancedRetrievalService:
    """Get advanced retrieval service singleton."""
    global _advanced_retrieval
    if _advanced_retrieval is None:
        _advanced_retrieval = AdvancedRetrievalService()
    return _advanced_retrieval
