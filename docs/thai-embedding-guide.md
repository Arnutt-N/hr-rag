# Thai Language Embedding Guide

## Overview

This guide covers embedding model selection and optimization for Thai language RAG applications. Thai presents unique challenges including word segmentation, character encoding, and context-dependent meanings.

## Thai Language Challenges

| Challenge | Description | Solution |
|-----------|-------------|----------|
| **Word Segmentation** | No spaces between words | PyThaiNLP tokenization |
| **Character Encoding** | Complex UTF-8 characters | Ensure proper UTF-8 |
| **Context** | Same word, different meanings | Semantic embeddings |
| **Mixed Content** | Thai + English + Numbers | Multilingual models |

## Recommended Embedding Models

### Top Choices for Thai (2025)

| Model | Languages | Dimensions | MTEB Thai | Best For |
|-------|-----------|------------|-----------|----------|
| **BAAI/bge-m3** | 100+ | 1024 | ⭐⭐⭐⭐⭐ | General Thai RAG |
| **intfloat/multilingual-e5-large** | 100+ | 1024 | ⭐⭐⭐⭐ | High accuracy |
| **sentence-transformers/paraphrase-multilingual-mpnet-base-v2** | 50+ | 768 | ⭐⭐⭐⭐ | Balanced |
| **intfloat/multilingual-e5-small** | 100+ | 384 | ⭐⭐⭐ | Fast inference |

### Model Comparison

```
Performance vs Speed Tradeoff:

bge-m3                    ████████████████████  (Best quality, slower)
multilingual-e5-large     ██████████████████    (Great quality)
mpnet-base-multilingual   ████████████████      (Good balance)
multilingual-e5-small     ████████████          (Fast, decent quality)
```

## Installation

```bash
# Install sentence-transformers
pip install sentence-transformers

# Install PyThaiNLP for Thai tokenization
pip install pythainlp

# Install additional dependencies
pip install numpy faiss-cpu  # or faiss-gpu for GPU
```

## Basic Usage

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Load model
model = SentenceTransformer('BAAI/bge-m3')

# Thai text examples
documents = [
    "นโยบายการลาของพนักงาน บริษัทอนุญาตให้ลาป่วยได้ 15 วันต่อปี",
    "การคำนวณโบนัสจะพิจารณาจากผลการปฏิบัติงาน",
    "วันและเวลาทำงานของบริษัทคือ จันทร์-ศุกร์ 09:00-18:00 น.",
    "Employee leave policy allows 15 days of sick leave per year",
    "Bonus calculation is based on performance review"
]

# Generate embeddings
embeddings = model.encode(documents, convert_to_numpy=True)

print(f"Embedding shape: {embeddings.shape}")
# Output: (5, 1024)

# Calculate similarity between Thai documents
from sklearn.metrics.pairwise import cosine_similarity

similarity_matrix = cosine_similarity(embeddings)
print(f"Thai-Thai similarity (0-1): {similarity_matrix[0][1]:.4f}")
# Output: ~0.85 (high similarity - same topic)
print(f"Thai-English similarity (0-3): {similarity_matrix[0][3]:.4f}")
# Output: ~0.75 (cross-lingual similarity)
```

## Thai Text Preprocessing

### Word Segmentation

```python
from pythainlp.tokenize import word_tokenize, sent_tokenize

def preprocess_thai_text(text: str) -> str:
    """
    Preprocess Thai text for better embedding quality
    """
    # Tokenize words
    words = word_tokenize(text, engine='newmm')
    
    # Join with spaces (helps model understand boundaries)
    processed = ' '.join(words)
    
    return processed

# Example
text = "การลากิจต้องแจ้งล่วงหน้าอย่างน้อย 3 วัน"
processed = preprocess_thai_text(text)
print(processed)
# Output: "การ ลา กิจ ต้อง แจ้ง ล่วงหน้า อย่างน้อย 3 วัน"
```

### Sentence Splitting

```python
def split_into_sentences(text: str) -> list[str]:
    """Split Thai text into sentences"""
    sentences = sent_tokenize(text)
    return sentences

# Example
document = """
นโยบายการลา บริษัทกำหนดให้พนักงานสามารถลาป่วยได้ 15 วันต่อปี 
ส่วนการลากิจอนุญาตให้ลาได้ 7 วันต่อปี
การลาพักร้อนจะต้องยื่นคำร้องล่วงหน้าอย่างน้อย 7 วัน
"""

sentences = split_into_sentences(document)
for i, s in enumerate(sentences):
    print(f"{i+1}. {s}")
```

## Chunking Strategies for Thai

### Strategy 1: Sentence-based Chunking (Recommended)

```python
from pythainlp.tokenize import sent_tokenize
import re

def chunk_by_sentences(
    text: str, 
    max_chars: int = 500, 
    overlap: int = 50
) -> list[dict]:
    """
    Chunk Thai text by sentences with overlap
    """
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        if current_length + sentence_length <= max_chars:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            if current_chunk:
                chunks.append({
                    'text': ' '.join(current_chunk),
                    'length': current_length,
                    'sentences': len(current_chunk)
                })
            
            # Handle overlap
            if overlap > 0 and len(current_chunk) >= 2:
                # Keep last N sentences for overlap
                overlap_text = ' '.join(current_chunk[-2:])
                current_chunk = [overlap_text, sentence]
                current_length = len(overlap_text) + sentence_length
            else:
                current_chunk = [sentence]
                current_length = sentence_length
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            'text': ' '.join(current_chunk),
            'length': current_length,
            'sentences': len(current_chunk)
        })
    
    return chunks
```

### Strategy 2: Fixed Size with Thai Tokenization

```python
from pythainlp.tokenize import word_tokenize

def chunk_by_tokens(
    text: str, 
    max_tokens: int = 256,
    overlap_tokens: int = 30
) -> list[dict]:
    """
    Chunk by Thai word tokens
    """
    words = word_tokenize(text, engine='newmm')
    chunks = []
    
    for i in range(0, len(words), max_tokens - overlap_tokens):
        chunk_words = words[i:i + max_tokens]
        chunk_text = ''.join(chunk_words)  # Join without spaces
        
        chunks.append({
            'text': chunk_text,
            'token_count': len(chunk_words),
            'start_index': i
        })
        
        if i + max_tokens >= len(words):
            break
    
    return chunks
```

### Strategy 3: Semantic Chunking (Advanced)

```python
def semantic_chunking(
    text: str,
    model,
    threshold: float = 0.7,
    min_chunk_size: int = 100
) -> list[dict]:
    """
    Split by semantic similarity using embeddings
    """
    sentences = sent_tokenize(text)
    
    if len(sentences) <= 1:
        return [{'text': text, 'sentences': 1}]
    
    # Get embeddings for all sentences
    embeddings = model.encode(sentences)
    
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Calculate similarity between consecutive sentences
    similarities = cosine_similarity(embeddings[:-1], embeddings[1:])
    
    # Find breakpoints (low similarity)
    breakpoints = [0]
    for i, sim in enumerate(similarities):
        if sim[0] < threshold:
            breakpoints.append(i + 1)
    breakpoints.append(len(sentences))
    
    # Create chunks
    chunks = []
    for i in range(len(breakpoints) - 1):
        start = breakpoints[i]
        end = breakpoints[i + 1]
        chunk_text = ' '.join(sentences[start:end])
        
        if len(chunk_text) >= min_chunk_size:
            chunks.append({
                'text': chunk_text,
                'sentences': end - start,
                'breakpoint_similarity': similarities[start] if start < len(similarities) else 1.0
            })
    
    return chunks
```

## Hybrid Search (Keyword + Semantic)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class ThaiHybridRetriever:
    """
    Hybrid search combining semantic and keyword search
    """
    
    def __init__(self, semantic_weight: float = 0.7):
        self.semantic_model = SentenceTransformer('BAAI/bge-m3')
        self.tfidf = TfidfVectorizer()
        self.documents = []
        self.embeddings = None
        self.tfidf_matrix = None
        self.semantic_weight = semantic_weight
    
    def index_documents(self, documents: list[str]):
        """Index documents for hybrid search"""
        self.documents = documents
        
        # Semantic embeddings
        self.embeddings = self.semantic_model.encode(documents)
        
        # TF-IDF for keyword search
        self.tfidf_matrix = self.tfidf.fit_transform(documents)
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search with hybrid scoring"""
        
        # Semantic search
        query_emb = self.semantic_model.encode([query])
        semantic_scores = cosine_similarity(query_emb, self.embeddings)[0]
        
        # Keyword search
        query_tfidf = self.tfidf.transform([query])
        keyword_scores = cosine_similarity(query_tfidf, self.tfidf_matrix)[0]
        
        # Combine scores
        final_scores = (
            self.semantic_weight * semantic_scores + 
            (1 - self.semantic_weight) * keyword_scores.toarray().flatten()
        )
        
        # Get top-k results
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        
        return [
            {
                'text': self.documents[i],
                'score': float(final_scores[i]),
                'semantic_score': float(semantic_scores[i]),
                'keyword_score': float(keyword_scores.toarray()[0][i])
            }
            for i in top_indices
        ]

# Usage
retriever = ThaiHybridRetriever(semantic_weight=0.7)
retriever.index_documents(documents)

results = retriever.search("นโยบายการลาป่วย")
for r in results:
    print(f"Score: {r['score']:.3f} | Text: {r['text'][:50]}...")
```

## Optimization Techniques

### 1. Caching Embeddings

```python
from functools import lru_cache
import hashlib

class EmbeddingCache:
    def __init__(self, model, max_size: int = 10000):
        self.model = model
        self.cache = {}
        self.max_size = max_size
    
    def _hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    def get_embedding(self, text: str) -> np.ndarray:
        text_hash = self._hash_text(text)
        
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        embedding = self.model.encode([text])[0]
        
        # Evict if full
        if len(self.cache) >= self.max_size:
            # Remove oldest (simple FIFO)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[text_hash] = embedding
        return embedding
    
    def get_embeddings_batch(self, texts: list[str]) -> list[np.ndarray]:
        """Get embeddings for multiple texts with caching"""
        results = []
        uncached = []
        uncached_indices = []
        
        # Check cache
        for i, text in enumerate(texts):
            text_hash = self._hash_text(text)
            if text_hash in self.cache:
                results.append((i, self.cache[text_hash]))
            else:
                uncached.append(text)
                uncached_indices.append(i)
        
        # Get uncached embeddings
        if uncached:
            new_embeddings = self.model.encode(uncached)
            
            for idx, emb, text in zip(uncached_indices, new_embeddings, uncached):
                text_hash = self._hash_text(text)
                self.cache[text_hash] = emb
                results.append((idx, emb))
        
        # Sort by original order
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
```

### 2. Batch Processing

```python
def process_documents_batch(
    documents: list[str],
    model,
    batch_size: int = 32
) -> np.ndarray:
    """
    Process documents in batches for efficiency
    """
    all_embeddings = []
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True)
        all_embeddings.append(batch_embeddings)
    
    return np.vstack(all_embeddings)
```

### 3. FAISS Index for Fast Search

```python
import faiss
import numpy as np

class FaissIndex:
    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.index = None
        self.documents = []
    
    def build_index(self, embeddings: np.ndarray, documents: list[str]):
        """Build FAISS index with normalized embeddings"""
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms
        
        # Use Inner Product (after normalization = cosine similarity)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(normaled)
        self.documents = documents
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        """Search for similar documents"""
        # Normalize query
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Search
        scores, indices = self.index.search(
            query_norm.reshape(1, -1), 
            top_k
        )
        
        return [
            {
                'text': self.documents[idx],
                'score': float(scores[0][i])
            }
            for i, idx in enumerate(indices[0])
            if idx < len(self.documents)
        ]
```

## Model Selection Guide

| Use Case | Recommended Model | Reasoning |
|----------|-------------------|-----------|
| **General HR Thai** | bge-m3 | Best overall Thai support |
| **High accuracy needed** | multilingual-e5-large | Highest MTEB scores |
| **Limited resources** | multilingual-e5-small | Fast inference |
| **Cross-lingual (TH-EN)** | bge-m3 or e5-large | Best cross-lingual |
| **Real-time chat** | e5-small + caching | Speed critical |

## Environment Variables

```bash
# .env
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_BATCH_SIZE=32
EMBEDDING_CACHE_SIZE=10000
EMBEDDING_DEVICE=cpu  # or cuda
```

## Performance Benchmarks

| Model | Thai MTEB | Latency (CPU) | Latency (GPU) | Memory |
|-------|-----------|---------------|---------------|--------|
| bge-m3 | 68.5 | ~200ms/doc | ~50ms/doc | 2.2GB |
| e5-large | 67.2 | ~180ms/doc | ~45ms/doc | 1.8GB |
| mpnet-base | 64.1 | ~100ms/doc | ~30ms/doc | 1.1GB |
| e5-small | 58.3 | ~30ms/doc | ~15ms/doc | 420MB |

---

*Generated for HR-RAG Project - Based on ToppLab Research*
