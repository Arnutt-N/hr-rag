"""
Thai Advanced Chunking - Semantic chunking optimized for Thai language
"""

import re
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document


class ThaiSemanticChunker:
    """
    Advanced chunking for Thai documents using semantic boundaries.
    
    Unlike fixed-size chunking, this preserves:
    - Complete sentences
    - Paragraph boundaries
    - Topic sections
    - Thai linguistic features
    """
    
    # Thai sentence-ending particles
    THAI_END_PARTICLES = ['ค่ะ', 'ครับ', 'คะ', 'คร๊าบ', 'จ้ะ', 'จ๊ะ', 'เจ้า', 
                          'นะ', 'นะคะ', 'นะครับ', 'เลย', 'เถอะ', 'น่ะ', 'แหละ']
    
    # Section indicators in Thai documents
    SECTION_MARKERS = [
        'บทที่', 'หมวดที่', 'ข้อที่', 'หัวข้อ',
        '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.',
        '1)', '2)', '3)', '4)', '5)',
        'ก.', 'ข.', 'ค.', 'ง.', 'จ.',
        'ก)', 'ข)', 'ค)', 'ง)', 'จ)'
    ]
    
    def __init__(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 800,
        overlap: int = 50
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents using semantic chunking."""
        result = []
        
        for doc in documents:
            chunks = self._split_text(doc.page_content)
            
            for i, chunk_text in enumerate(chunks):
                # Create new document with chunk
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata={
                        **doc.metadata,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'chunk_strategy': 'semantic_thai'
                    }
                )
                result.append(chunk_doc)
        
        return result
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into semantic chunks."""
        # Step 1: Identify semantic boundaries
        boundaries = self._find_boundaries(text)
        
        # Step 2: Create chunks respecting boundaries
        chunks = []
        current_chunk = []
        current_size = 0
        
        for start, end, boundary_type in boundaries:
            segment = text[start:end]
            segment_size = len(segment)
            
            # Check if adding this segment exceeds max size
            if current_size + segment_size > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ''.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap(''.join(current_chunk))
                current_chunk = [overlap_text, segment]
                current_size = len(overlap_text) + segment_size
            else:
                current_chunk.append(segment)
                current_size += segment_size
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ''.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
        
        return chunks if chunks else [text]
    
    def _find_boundaries(self, text: str) -> List[tuple]:
        """Find semantic boundaries in text."""
        boundaries = []
        
        # Find paragraph boundaries (double newlines)
        paragraphs = re.split(r'\n\s*\n', text)
        pos = 0
        for para in paragraphs:
            if para.strip():
                boundaries.append((pos, pos + len(para), 'paragraph'))
            pos += len(para) + 2  # +2 for \n\n
        
        # Find section boundaries
        for marker in self.SECTION_MARKERS:
            pattern = f'(?:^|\n)\s*{re.escape(marker)}'
            for match in re.finditer(pattern, text):
                boundaries.append((match.start(), match.end(), 'section'))
        
        # Find sentence boundaries (Thai particles)
        for particle in self.THAI_END_PARTICLES:
            pattern = f'{re.escape(particle)}(?:\s|$)'
            for match in re.finditer(pattern, text):
                end_pos = match.end()
                # Look for next sentence start
                next_start = end_pos
                while next_start < len(text) and text[next_start] in ' \n':
                    next_start += 1
                if next_start < len(text):
                    boundaries.append((match.start(), next_start, 'sentence'))
        
        # Sort by position and remove duplicates
        boundaries = sorted(set(boundaries), key=lambda x: x[0])
        
        # Merge overlapping boundaries
        merged = []
        for boundary in boundaries:
            if not merged or boundary[0] >= merged[-1][1]:
                merged.append(boundary)
            else:
                # Extend current boundary if needed
                merged[-1] = (merged[-1][0], max(merged[-1][1], boundary[1]), merged[-1][2])
        
        return merged
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from previous chunk."""
        # Get last sentence or paragraph
        for particle in self.THAI_END_PARTICLES:
            if particle in text:
                last_idx = text.rfind(particle)
                if last_idx > len(text) - self.overlap * 2:
                    return text[last_idx:]
        
        # Fallback: just take last N characters
        return text[-self.overlap:] if len(text) > self.overlap else text
    
    def analyze_chunk_quality(self, chunks: List[str]) -> Dict[str, Any]:
        """Analyze quality of chunks."""
        stats = {
            'total_chunks': len(chunks),
            'avg_size': sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
            'min_size': min(len(c) for c in chunks) if chunks else 0,
            'max_size': max(len(c) for c in chunks) if chunks else 0,
            'boundary_types': {}
        }
        
        # Check for incomplete sentences
        incomplete = 0
        for chunk in chunks:
            # Check if chunk ends mid-sentence
            last_chars = chunk[-20:] if len(chunk) > 20 else chunk
            if not any(p in last_chars for p in self.THAI_END_PARTICLES + ['.', '!', '?']):
                incomplete += 1
        
        stats['incomplete_chunks'] = incomplete
        stats['quality_score'] = (len(chunks) - incomplete) / len(chunks) * 100 if chunks else 0
        
        return stats


class QueryClassifier:
    """
    Classify queries to optimize retrieval strategy.
    """
    
    QUERY_TYPES = {
        'factual': 'คำถามเชิงข้อเท็จจริง',
        'procedural': 'คำถามขั้นตอน/วิธีการ',
        'comparative': 'คำถามเปรียบเทียบ',
        'multi_hop': 'คำถามหลายขั้น',
        'vague': 'คำถามคลุมเครือ'
    }
    
    def classify(self, query: str) -> Dict[str, Any]:
        """Classify query type."""
        query_lower = query.lower()
        
        # Check for comparative
        if any(word in query_lower for word in ['เปรียบเทียบ', 'ต่างกัน', 'vs', 'หรือ']):
            return {'type': 'comparative', 'confidence': 0.9}
        
        # Check for procedural
        if any(word in query_lower for word in ['ขั้นตอน', 'วิธี', 'ทำอย่างไร', 'ยังไง']):
            return {'type': 'procedural', 'confidence': 0.9}
        
        # Check for multi-hop (complex)
        if any(word in query_lower for word in ['และ', 'กับ', 'ที่เกี่ยวกับ']) and len(query) > 50:
            return {'type': 'multi_hop', 'confidence': 0.8}
        
        # Check for vague
        if len(query) < 10 or any(word in query_lower for word in ['อะไร', 'ยังไง', 'ที่ไหน']):
            return {'type': 'vague', 'confidence': 0.7}
        
        # Default: factual
        return {'type': 'factual', 'confidence': 0.8}
    
    def get_retrieval_strategy(self, query_type: str) -> Dict[str, Any]:
        """Get optimal retrieval strategy for query type."""
        strategies = {
            'factual': {
                'k': 3,
                'use_hybrid': True,
                'rerank': True,
                'expand_query': False
            },
            'procedural': {
                'k': 5,
                'use_hybrid': True,
                'rerank': True,
                'expand_query': True
            },
            'comparative': {
                'k': 10,
                'use_hybrid': True,
                'rerank': True,
                'expand_query': True,
                'multi_document': True
            },
            'multi_hop': {
                'k': 5,
                'use_hybrid': True,
                'rerank': True,
                'expand_query': True,
                'multi_hop': True
            },
            'vague': {
                'k': 5,
                'use_hybrid': True,
                'rerank': True,
                'expand_query': True,
                'clarify': True
            }
        }
        
        return strategies.get(query_type, strategies['factual'])
