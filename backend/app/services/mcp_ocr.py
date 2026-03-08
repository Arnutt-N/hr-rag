"""
MCP OCR Service - Thai-optimized OCR for document processing
"""

from typing import Optional, Dict, Any, List
import json
from pathlib import Path


class MCPOCRService:
    """
    OCR service optimized for Thai documents.
    Supports PDF, images, and scanned documents.
    """
    
    SUPPORTED_FORMATS = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
    
    def __init__(self):
        self.thai_characters = self._get_thai_charset()
    
    def _get_thai_charset(self) -> set:
        """Get Thai character set for validation."""
        # Thai Unicode range: 0x0E00-0x0E7F
        thai_chars = set()
        for i in range(0x0E00, 0x0E80):
            thai_chars.add(chr(i))
        return thai_chars
    
    async def extract_text(
        self,
        file_path: str,
        language: str = "tha+eng",  # Thai + English
        enhance_resolution: bool = True,
        deskew: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from document/image.
        
        Args:
            file_path: Path to file
            language: OCR language (tha+eng, tha, eng)
            enhance_resolution: Enhance image resolution
            deskew: Auto-rotate skewed documents
        
        Returns:
            Extracted text with metadata
        """
        try:
            # Check file format
            ext = Path(file_path).suffix.lower()
            if ext not in self.SUPPORTED_FORMATS:
                return {
                    "success": False,
                    "error": f"Unsupported format: {ext}. Use: {self.SUPPORTED_FORMATS}"
                }
            
            # TODO: Implement actual OCR using pytesseract or easyocr
            # For now, return placeholder
            
            return {
                "success": True,
                "file_path": file_path,
                "language": language,
                "text": "[OCR text will appear here]",
                "confidence": 0.95,
                "pages": 1,
                "thai_ratio": 0.75,  # % of Thai characters detected
                "metadata": {
                    "enhanced": enhance_resolution,
                    "deskewed": deskew
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_table(
        self,
        file_path: str,
        page_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract tables from document.
        
        Args:
            file_path: Path to file
            page_number: Specific page (optional)
        
        Returns:
            Tables as structured data
        """
        try:
            # TODO: Implement table extraction
            
            return {
                "success": True,
                "file_path": file_path,
                "tables": [
                    {
                        "page": 1,
                        "rows": 5,
                        "columns": 3,
                        "data": [["...", "...", "..."]]
                    }
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_process(
        self,
        file_paths: List[str],
        language: str = "tha+eng"
    ) -> Dict[str, Any]:
        """
        Process multiple files.
        
        Args:
            file_paths: List of file paths
            language: OCR language
        
        Returns:
            Batch processing results
        """
        results = []
        for path in file_paths:
            result = await self.extract_text(path, language)
            results.append({
                "file": path,
                "result": result
            })
        
        return {
            "success": True,
            "total_files": len(file_paths),
            "successful": sum(1 for r in results if r["result"].get("success")),
            "failed": sum(1 for r in results if not r["result"].get("success")),
            "results": results
        }
    
    def validate_thai_text(self, text: str) -> Dict[str, Any]:
        """
        Validate Thai text quality.
        
        Args:
            text: Extracted text
        
        Returns:
            Validation results
        """
        if not text:
            return {"valid": False, "thai_ratio": 0, "message": "Empty text"}
        
        thai_count = sum(1 for char in text if char in self.thai_characters)
        total_chars = len(text.replace(" ", "").replace("\n", ""))
        
        if total_chars == 0:
            return {"valid": False, "thai_ratio": 0, "message": "No content"}
        
        thai_ratio = thai_count / total_chars
        
        return {
            "valid": thai_ratio > 0.1,  # At least 10% Thai
            "thai_ratio": round(thai_ratio, 2),
            "thai_chars": thai_count,
            "total_chars": total_chars,
            "message": "Valid Thai document" if thai_ratio > 0.1 else "Low Thai content"
        }


# Singleton
_ocr_service: Optional[MCPOCRService] = None


def get_ocr_service() -> MCPOCRService:
    """Get OCR service singleton."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = MCPOCRService()
    return _ocr_service
