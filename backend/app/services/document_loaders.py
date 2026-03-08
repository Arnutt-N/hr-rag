"""
Document Loaders Service - Load documents using LangChain loaders
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader,
)
from langchain_core.documents import Document


class DocumentLoaderService:
    """
    Load documents using LangChain loaders.
    Supports PDF, DOCX, TXT, MD, and other formats.
    """
    
    def __init__(self):
        """Initialize document loader service."""
        self.loaders = {
            "pdf": PyPDFLoader,
            "docx": Docx2txtLoader,
            "doc": Docx2txtLoader,
            "txt": TextLoader,
            "md": TextLoader,
            "markdown": TextLoader,
        }
        self.default_loader = UnstructuredFileLoader
    
    def get_loader_class(self, file_type: str):
        """
        Get loader class for file type.
        
        Args:
            file_type: File extension (without dot)
        
        Returns:
            Loader class
        """
        return self.loaders.get(file_type.lower(), self.default_loader)
    
    async def load(
        self,
        file_path: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Load document from file path.
        
        Args:
            file_path: Path to document file
            file_type: File type/extension (auto-detected if not provided)
            metadata: Additional metadata to add
        
        Returns:
            List of LangChain Document objects
        """
        # Auto-detect file type
        if file_type is None:
            file_type = Path(file_path).suffix.lstrip(".").lower()
        
        # Get loader
        loader_class = self.get_loader_class(file_type)
        
        # Load document
        try:
            if file_type in ["txt", "md", "markdown"]:
                # TextLoader needs encoding
                loader = loader_class(file_path, encoding="utf-8")
            else:
                loader = loader_class(file_path)
            
            # Load with async support
            documents = await loader.aload()
            
        except Exception as e:
            # Fallback to unstructured loader
            loader = self.default_loader(file_path)
            documents = await loader.aload()
        
        # Add metadata
        base_metadata = {
            "source": file_path,
            "file_type": file_type,
            "filename": Path(file_path).name,
            "loaded_at": datetime.utcnow().isoformat(),
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        # Update document metadata
        for doc in documents:
            doc.metadata.update(base_metadata)
        
        return documents
    
    async def load_bytes(
        self,
        content: bytes,
        filename: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Load document from bytes content.
        
        Args:
            content: File content as bytes
            filename: Original filename
            file_type: File type (auto-detected from filename)
            metadata: Additional metadata
        
        Returns:
            List of Document objects
        """
        import tempfile
        
        # Auto-detect file type
        if file_type is None:
            file_type = Path(filename).suffix.lstrip(".").lower()
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=f".{file_type}",
            delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Load from temp file
            documents = await self.load(
                file_path=tmp_path,
                file_type=file_type,
                metadata={"filename": filename, **(metadata or {})}
            )
            return documents
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def load_multiple(
        self,
        file_paths: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Load multiple documents.
        
        Args:
            file_paths: List of file paths
            metadata: Common metadata for all documents
        
        Returns:
            Combined list of Document objects
        """
        import asyncio
        
        tasks = [
            self.load(fp, metadata=metadata)
            for fp in file_paths
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter
        documents = []
        for result in results:
            if isinstance(result, list):
                documents.extend(result)
            elif isinstance(result, Exception):
                # Log error but continue
                print(f"Error loading document: {result}")
        
        return documents


# Singleton instance
_loader_service: Optional[DocumentLoaderService] = None


def get_loader_service() -> DocumentLoaderService:
    """Get or create document loader service singleton."""
    global _loader_service
    
    if _loader_service is None:
        _loader_service = DocumentLoaderService()
    
    return _loader_service
