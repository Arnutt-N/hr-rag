"""
Neo4j Graph Service - Production-ready Neo4j integration for HR-RAG
Compatible with existing GraphRAGService
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from neo4j import GraphDatabase, Driver, Session
from langchain_core.documents import Document

from app.services.llm.langchain_service import get_llm_service


@dataclass
class Neo4jConfig:
    """Neo4j configuration - all values from environment."""
    uri: str = ""
    user: str = ""
    password: str = ""
    database: str = "neo4j"
    
    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Create config from environment variables."""
        return cls(
            uri=os.getenv("NEO4J_URI", ""),
            user=os.getenv("NEO4J_USER", ""),
            password=os.getenv("NEO4J_PASSWORD", ""),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        )


class Neo4jGraphService:
    """
    Neo4j-based Graph Service for HR-RAG.
    
    Replaces in-memory graph with Neo4j for production use.
    Compatible with existing GraphRAGService interface.
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        self.config = config or Neo4jConfig.from_env()
        self._driver: Optional[Driver] = None
        self._connected = False
        self.llm_service = get_llm_service()
    
    def _get_driver(self) -> Driver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
        return self._driver
    
    def connect(self) -> bool:
        """Test connection to Neo4j."""
        try:
            driver = self._get_driver()
            driver.verify_connectivity()
            self._connected = True
            return True
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            self._connected = False
            return False
    
    def close(self):
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            self._connected = False
    
    def ensure_schema(self):
        """Create indexes and constraints."""
        with self._get_driver().session(database=self.config.database) as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint creation warning: {e}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "CREATE INDEX document_source IF NOT EXISTS FOR (d:Document) ON (d.source)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    print(f"Index creation warning: {e}")
    
    async def build_graph_from_documents(self, documents: List[Document]):
        """Build knowledge graph from documents in Neo4j."""
        if not self.connect():
            raise ConnectionError("Cannot connect to Neo4j")
        
        self.ensure_schema()
        
        print(f"Building Neo4j graph from {len(documents)} documents...")
        
        with self._get_driver().session(database=self.config.database) as session:
            for i, doc in enumerate(documents):
                doc_id = f"doc_{i}"
                
                # Create document node
                session.run("""
                    MERGE (d:Document {id: $doc_id})
                    SET d.content = $content,
                        d.source = $source,
                        d.index = $index
                """, doc_id=doc_id, content=doc.page_content[:1000],
                     source=doc.metadata.get("source", "unknown"), index=i)
                
                # Extract and create entities
                entities = await self._extract_entities(doc.page_content)
                
                for entity in entities:
                    entity_id = f"{entity['type']}_{entity['name']}"
                    
                    # Create entity node
                    session.run("""
                        MERGE (e:Entity {id: $entity_id})
                        SET e.name = $name,
                            e.type = $type,
                            e.mentions = coalesce(e.mentions, 0) + 1
                    """, entity_id=entity_id, name=entity['name'], type=entity['type'])
                    
                    # Link entity to document
                    session.run("""
                        MATCH (d:Document {id: $doc_id})
                        MATCH (e:Entity {id: $entity_id})
                        MERGE (e)-[:APPEARS_IN]->(d)
                    """, doc_id=doc_id, entity_id=entity_id)
                
                # Extract and create relations
                relations = await self._extract_relations(doc.page_content, entities)
                
                for rel in relations:
                    source_id = f"{rel['source_type']}_{rel['source']}"
                    target_id = f"{rel['target_type']}_{rel['target']}"
                    
                    session.run("""
                        MATCH (s:Entity {id: $source_id})
                        MATCH (t:Entity {id: $target_id})
                        MERGE (s)-[r:RELATES {type: $rel_type}]->(t)
                        SET r.weight = coalesce(r.weight, 0) + $weight
                    """, source_id=source_id, target_id=target_id,
                         rel_type=rel['relation'], weight=rel.get('weight', 1.0))
        
        print("Neo4j graph built successfully")
    
    async def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities from text."""
        import re
        import json
        
        prompt = f"""Extract entities from this HR document:

{text[:1000]}

Identify: PERSON, DEPARTMENT, POLICY, DOCUMENT, ROLE, LOCATION

Return JSON: [{{"name": "...", "type": "..."}}]"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                return entities if isinstance(entities, list) else []
            return []
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Entity extraction error: {e}")
            return []
    
    async def _extract_relations(self, text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Extract relations between entities."""
        import re
        import json
        
        if len(entities) < 2:
            return []
        
        entity_names = [e['name'] for e in entities]
        prompt = f"""Find relations: {', '.join(entity_names)}

Text: {text[:800]}

Return JSON: [{{"source": "...", "target": "...", "relation": "..."}}]"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                relations = json.loads(json_match.group())
                return relations if isinstance(relations, list) else []
            return []
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Relation extraction error: {e}")
            return []
    
    def get_neighbors(self, entity_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get neighboring entities from Neo4j."""
        with self._get_driver().session(database=self.config.database) as session:
            result = session.run("""
                MATCH (e:Entity {name: $name})-[*1..$depth]-(neighbor:Entity)
                RETURN DISTINCT neighbor.id AS id,
                       neighbor.name AS name,
                       neighbor.type AS type
            """, name=entity_name, depth=depth)
            
            return [dict(record) for record in result]
    
    def get_subgraph(self, entity_names: List[str], depth: int = 1) -> Dict[str, Any]:
        """Extract subgraph around given entities."""
        with self._get_driver().session(database=self.config.database) as session:
            # Get entities
            entities_result = session.run("""
                MATCH (e:Entity)
                WHERE e.name IN $names
                OPTIONAL MATCH (e)-[*1..$depth]-(related:Entity)
                RETURN DISTINCT e.id AS id, e.name AS name, e.type AS type
                UNION
                RETURN DISTINCT related.id AS id, related.name AS name, related.type AS type
            """, names=entity_names, depth=depth)
            
            entities = [dict(record) for record in entities_result]
            
            # Get relations
            relations_result = session.run("""
                MATCH (s:Entity)-[r:RELATES]->(t:Entity)
                WHERE s.name IN $names OR t.name IN $names
                RETURN s.name AS source, t.name AS target, r.type AS type
            """, names=entity_names)
            
            relations = [dict(record) for record in relations_result]
            
            return {'entities': entities, 'relations': relations}
    
    def search_by_entity(self, entity_name: str) -> List[str]:
        """Find documents containing entity."""
        with self._get_driver().session(database=self.config.database) as session:
            result = session.run("""
                MATCH (e:Entity {name: $name})-[:APPEARS_IN]->(d:Document)
                RETURN d.id AS doc_id, d.content AS content
            """, name=entity_name)
            
            return [record['content'] for record in result]
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get Neo4j graph statistics."""
        with self._get_driver().session(database=self.config.database) as session:
            # Count entities by type
            entity_types = session.run("""
                MATCH (e:Entity)
                RETURN e.type AS type, count(e) AS count
            """)
            
            types = {record['type']: record['count'] for record in entity_types}
            
            # Count total
            total_entities = session.run("MATCH (e:Entity) RETURN count(e) AS c").single()['c']
            total_relations = session.run("MATCH ()-[r:RELATES]->() RETURN count(r) AS c").single()['c']
            total_documents = session.run("MATCH (d:Document) RETURN count(d) AS c").single()['c']
            
            return {
                'connected': self._connected,
                'total_entities': total_entities,
                'total_relations': total_relations,
                'total_documents': total_documents,
                'entity_types': types
            }
    
    def clear_graph(self):
        """Clear all data from Neo4j."""
        with self._get_driver().session(database=self.config.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Neo4j graph cleared")


# Singleton
_neo4j_service: Optional[Neo4jGraphService] = None


def get_neo4j_service() -> Neo4jGraphService:
    """Get Neo4j service singleton."""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jGraphService()
    return _neo4j_service
