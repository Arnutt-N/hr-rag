"""
Text Splitters Service - Split documents into chunks using LangChain splitters
"""

from typing import List, Optional, Literal
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter,
)
from langchain_core.documents import Document


class TextSplitterService:
    """
    Split documents into chunks using various strategies.
    Supports recursive, token-based, and markdown-aware splitting.
    """
    
    def __init__(
        self,
        strategy: Literal["recursive", "token", "markdown"] = "recursive",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize text splitter service.
        
        Args:
            strategy: Splitting strategy
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = self._create_splitter(strategy)
    
    def _create_splitter(self, strategy: str):
        """
        Create splitter for strategy.
        
        Args:
            strategy: Strategy name
        
        Returns:
            TextSplitter instance
        """
        splitters = {
            "recursive": RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ".", " ", ""],
                length_function=len,
            ),
            "token": TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            ),
            "markdown": MarkdownTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            ),
        }
        
        return splitters.get(strategy, splitters["recursive"])
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
        
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of Document objects
        
        Returns:
            List of chunked Document objects
        """
        return self.splitter.split_documents(documents)
    
    async def split_and_index(
        self,
        documents: List[Document],
        vector_store,
        collection_name: str
    ) -> List[str]:
        """
        Split documents and add to vector store.
        
        Args:
            documents: Documents to split and index
            vector_store: Vector store instance
            collection_name: Collection name
        
        Returns:
            List of document IDs
        """
        # Split documents
        chunks = self.split_documents(documents)
        
        # Add to vector store
        if hasattr(vector_store, 'aadd_documents'):
            # Async
            ids = await vector_store.aadd_documents(chunks)
        else:
            # Sync fallback
            ids = vector_store.add_documents(chunks)
        
        return ids


class ThaiTextSplitterService(TextSplitterService):
    """
    Text splitter optimized for Thai language.
    Uses Thai-specific separators and tokenization.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize Thai text splitter.
        
        Args:
            chunk_size: Target chunk size (in characters)
            chunk_overlap: Overlap between chunks
        """
        # Thai-specific separators
        # Thai doesn't use spaces between words, so we split on:
        # - Paragraph breaks
        # - Sentence-ending particles (ค่ะ, ครับ, etc.)
        # - Newlines
        thai_separators = [
            "\n\n\n",  # Paragraph
            "\n\n",    # Double newline
            "\n",      # Single newline
            "ค่ะ",      # Sentence ender (female)
            "ครับ",     # Sentence ender (male)
            "คะ",      # Sentence ender (female question)
            "ครั้ง",    # Often ends sentences
            " ",       # Space (rare in Thai but possible)
            "",
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=thai_separators,
            length_function=len,
        )


def get_splitter(
    strategy: str = "recursive",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    thai_optimized: bool = False
) -> TextSplitterService:
    """
    Get text splitter service.
    
    Args:
        strategy: Splitting strategy
        chunk_size: Chunk size
        chunk_overlap: Chunk overlap
        thai_optimized: Use Thai-optimized splitter
    
    Returns:
        TextSplitterService instance
    """
    if thai_optimized:
        return ThaiTextSplitterService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    return TextSplitterService(
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
