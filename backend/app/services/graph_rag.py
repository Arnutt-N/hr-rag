"""
Graph RAG - Knowledge Graph-based Retrieval

Builds a knowledge graph from documents and traverses it for better context.
Now with Neo4j support - falls back to in-memory when Neo4j unavailable.
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from langchain_core.documents import Document
from app.services.llm.langchain_service import get_llm_service
from app.services.advanced_retrieval import get_advanced_retrieval_service

# Optional Neo4j import
try:
    from app.services.neo4j_graph import Neo4jGraphService, get_neo4j_service
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


@dataclass
class Entity:
    """Knowledge graph entity."""
    id: str
    name: str
    type: str  # person, department, policy, document, etc.
    mentions: int = 0
    documents: Set[str] = field(default_factory=set)


@dataclass
class Relation:
    """Relation between entities."""
    source: str
    target: str
    relation_type: str
    weight: float = 1.0


class KnowledgeGraph:
    """In-memory knowledge graph for RAG."""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.entity_relations: Dict[str, List[Relation]] = defaultdict(list)
    
    def add_entity(self, entity_id: str, name: str, entity_type: str, doc_id: str):
        """Add or update entity."""
        if entity_id in self.entities:
            self.entities[entity_id].mentions += 1
            self.entities[entity_id].documents.add(doc_id)
        else:
            self.entities[entity_id] = Entity(
                id=entity_id,
                name=name,
                type=entity_type,
                mentions=1,
                documents={doc_id}
            )
    
    def add_relation(self, source: str, target: str, relation_type: str, weight: float = 1.0):
        """Add relation between entities."""
        relation = Relation(source, target, relation_type, weight)
        self.relations.append(relation)
        self.entity_relations[source].append(relation)
        self.entity_relations[target].append(relation)
    
    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[Entity]:
        """Get neighboring entities."""
        if depth == 0 or entity_id not in self.entities:
            return []
        
        neighbors = []
        visited = {entity_id}
        
        for relation in self.entity_relations.get(entity_id, []):
            other_id = relation.target if relation.source == entity_id else relation.source
            if other_id not in visited and other_id in self.entities:
                neighbors.append(self.entities[other_id])
                visited.add(other_id)
                
                # Recursive for deeper traversal
                if depth > 1:
                    neighbors.extend(self.get_neighbors(other_id, depth - 1))
        
        return neighbors
    
    def get_subgraph(self, entity_ids: List[str], depth: int = 1) -> Dict[str, Any]:
        """Extract subgraph around given entities."""
        subgraph_entities = set(entity_ids)
        subgraph_relations = []
        
        for entity_id in entity_ids:
            if entity_id not in self.entities:
                continue
            
            for relation in self.entity_relations.get(entity_id, []):
                other_id = relation.target if relation.source == entity_id else relation.source
                
                if depth > 1:
                    # Add neighbors of neighbors
                    for rel2 in self.entity_relations.get(other_id, []):
                        subgraph_entities.add(rel2.source)
                        subgraph_entities.add(rel2.target)
                
                subgraph_entities.add(other_id)
                subgraph_relations.append(relation)
        
        return {
            'entities': [self.entities[eid].__dict__ for eid in subgraph_entities if eid in self.entities],
            'relations': [{'source': r.source, 'target': r.target, 'type': r.relation_type} 
                         for r in subgraph_relations]
        }


class GraphRAGService:
    """
    Graph RAG: Use knowledge graph for enhanced retrieval.
    
    Uses Neo4j when available, falls back to in-memory graph.
    """
    
    def __init__(self):
        self.graph = KnowledgeGraph()
        self.llm_service = get_llm_service()
        self.retrieval_service = get_advanced_retrieval_service()
        self._built = False
        
        # Try to use Neo4j
        self.neo4j_service: Optional[Any] = None
        self.use_neo4j = False
        
        if NEO4J_AVAILABLE:
            try:
                self.neo4j_service = get_neo4j_service()
                if self.neo4j_service.connect():
                    self.use_neo4j = True
                    print("Using Neo4j for Graph RAG")
                else:
                    print("Neo4j not available, using in-memory graph")
            except Exception as e:
                print(f"Neo4j initialization failed: {e}, using in-memory graph")
    
    async def build_graph_from_documents(self, documents: List[Document]):
        """Build knowledge graph from documents."""
        if self.use_neo4j and self.neo4j_service:
            await self.neo4j_service.build_graph_from_documents(documents)
            self._built = True
        else:
            # Fall back to in-memory
            await self._build_in_memory_graph(documents)
    
    async def _build_in_memory_graph(self, documents: List[Document]):
        
        for i, doc in enumerate(documents):
            doc_id = f"doc_{i}"
            
            # Extract entities
            entities = await self._extract_entities(doc.page_content)
            
            # Add to graph
            for entity in entities:
                entity_id = f"{entity['type']}_{entity['name']}"
                self.graph.add_entity(
                    entity_id=entity_id,
                    name=entity['name'],
                    entity_type=entity['type'],
                    doc_id=doc_id
                )
            
            # Extract relations
            relations = await self._extract_relations(doc.page_content, entities)
            for rel in relations:
                source_id = f"{rel['source_type']}_{rel['source']}"
                target_id = f"{rel['target_type']}_{rel['target']}"
                self.graph.add_relation(
                    source=source_id,
                    target=target_id,
                    relation_type=rel['relation'],
                    weight=rel.get('weight', 1.0)
                )
        
        self._built = True
        print(f"Graph built: {len(self.graph.entities)} entities, {len(self.graph.relations)} relations")
    
    async def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities from text using LLM."""
        prompt = f"""Extract entities from this HR document:

{text[:1000]}

Identify these entity types:
- PERSON (names of people)
- DEPARTMENT (department names)
- POLICY (policy names)
- DOCUMENT (document types)
- ROLE (job titles)
- LOCATION (places)

Return as JSON list:
[{{"name": "...", "type": "..."}}]"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON
            import json
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                return entities if isinstance(entities, list) else []
            
            return []
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            print(f"Entity extraction error: {e}")
            return []
    
    async def _extract_relations(self, text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Extract relations between entities."""
        if len(entities) < 2:
            return []
        
        entity_names = [e['name'] for e in entities]
        prompt = f"""Find relations between these entities:

Entities: {', '.join(entity_names)}

Text: {text[:800]}

Return relations as JSON:
[{{"source": "...", "target": "...", "relation": "...", "source_type": "...", "target_type": "..."}}]

Common relations: manages, reports_to, belongs_to, governs, applies_to, located_in"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            import json
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                relations = json.loads(json_match.group())
                return relations if isinstance(relations, list) else []
            
            return []
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            print(f"Relation extraction error: {e}")
            return []
    
    async def retrieve(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        graph_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Graph-enhanced retrieval.
        """
        # Step 1: Extract entities from query
        query_entities = await self._extract_entities(query)
        
        # Step 2: Find matching entities in graph
        matched_entities = []
        for qe in query_entities:
            entity_id = f"{qe['type']}_{qe['name']}"
            if entity_id in self.graph.entities:
                matched_entities.append(entity_id)
        
        # Step 3: Traverse graph for related entities
        graph_context = []
        if matched_entities:
            subgraph = self.graph.get_subgraph(matched_entities, depth=graph_depth)
            
            # Build context from graph
            for entity_data in subgraph['entities']:
                entity = Entity(**{k: v for k, v in entity_data.items() if k in Entity.__dataclass_fields__})
                graph_context.append({
                    'entity': entity.name,
                    'type': entity.type,
                    'related_docs': list(entity.documents)
                })
        
        # Step 4: Standard vector search
        vector_results = await self.retrieval_service.hybrid_search(
            query=query,
            collection_name=collection_name,
            k=k
        )
        
        # Step 5: Combine and rerank
        # Boost documents that appear in graph neighborhood
        combined_scores = {}
        
        for i, result in enumerate(vector_results):
            doc_id = f"doc_{i}"  # Simplified
            score = result.get('final_score', 0.5)
            
            # Boost if in graph context
            for ctx in graph_context:
                if doc_id in ctx['related_docs']:
                    score *= 1.2  # 20% boost
            
            combined_scores[i] = score
        
        # Sort by combined score
        sorted_indices = sorted(combined_scores.keys(), key=lambda i: combined_scores[i], reverse=True)
        
        return {
            'success': True,
            'query': query,
            'query_entities': query_entities,
            'matched_entities': matched_entities,
            'graph_context': graph_context,
            'results': [vector_results[i] for i in sorted_indices[:k]],
            'graph_stats': {
                'total_entities': len(self.graph.entities),
                'total_relations': len(self.graph.relations)
            }
        }
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        entity_types = defaultdict(int)
        for entity in self.graph.entities.values():
            entity_types[entity.type] += 1
        
        relation_types = defaultdict(int)
        for rel in self.graph.relations:
            relation_types[rel.relation_type] += 1
        
        return {
            'total_entities': len(self.graph.entities),
            'total_relations': len(self.graph.relations),
            'entity_types': dict(entity_types),
            'relation_types': dict(relation_types),
            'built': self._built
        }
    
    def export_graph(self) -> Dict[str, Any]:
        """Export graph for visualization."""
        return {
            'entities': [
                {
                    'id': e.id,
                    'name': e.name,
                    'type': e.type,
                    'mentions': e.mentions
                }
                for e in self.graph.entities.values()
            ],
            'relations': [
                {
                    'source': r.source,
                    'target': r.target,
                    'type': r.relation_type,
                    'weight': r.weight
                }
                for r in self.graph.relations
            ]
        }


# Singleton
_graph_rag: Optional[GraphRAGService] = None


def get_graph_rag_service() -> GraphRAGService:
    """Get Graph RAG service singleton."""
    global _graph_rag
    if _graph_rag is None:
        _graph_rag = GraphRAGService()
    return _graph_rag
