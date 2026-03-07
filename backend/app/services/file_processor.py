"""HR-RAG Backend - File Processing Service

Handles file uploads (PDF, DOC/DOCX, TXT) and extracts text.

Best-effort extraction:
- PDF: pdfplumber (good layout retention)
- DOCX: python-docx
- DOC: optional `textract` (requires system deps) -> if unavailable, raise a clear error
- TXT: utf-8 with fallback

Also includes Thai-friendly chunking strategy (sentence-based when possible).
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List, Tuple, Optional

from fastapi import UploadFile, HTTPException

from app.core.config import get_settings

settings = get_settings()


def _ext(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_upload(file: UploadFile) -> None:
    ext = _ext(file.filename or "")
    if ext not in set(settings.allowed_extensions):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


async def extract_text(file: UploadFile) -> Tuple[str, dict]:
    """Extract text from uploaded file.

    Returns:
      (text, meta) where meta may include page_count.
    """
    validate_upload(file)

    filename = file.filename or "uploaded"
    ext = _ext(filename)

    raw = await file.read()

    if len(raw) > settings.max_file_size:
        raise HTTPException(status_code=413, detail="File too large")

    if ext == ".txt":
        for enc in ("utf-8", "utf-8-sig", "cp874"):
            try:
                return raw.decode(enc), {}
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore"), {}

    if ext == ".pdf":
        try:
            import pdfplumber
        except Exception as e:
            raise HTTPException(status_code=500, detail="pdfplumber not installed")

        text_parts: List[str] = []
        page_count = 0
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            page_count = len(pdf.pages)
            for p in pdf.pages:
                t = p.extract_text() or ""
                if t.strip():
                    text_parts.append(t)
        return "\n\n".join(text_parts).strip(), {"page_count": page_count}

    if ext in (".docx",):
        try:
            import docx
        except Exception:
            raise HTTPException(status_code=500, detail="python-docx not installed")

        doc = docx.Document(io.BytesIO(raw))
        paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(paras).strip(), {}

    if ext in (".doc",):
        # DOC is legacy binary; extraction in pure python is unreliable.
        # textract sometimes works but needs system dependencies.
        try:
            import textract  # type: ignore
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=".doc extraction not supported in this build. Convert to .docx or .pdf. (Optional dependency: textract + system libs)"
            )
        try:
            text = textract.process(filename, input_encoding="utf-8", extension="doc", buffer=raw)
            return text.decode("utf-8", errors="ignore").strip(), {}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract .doc: {e}")

    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 150) -> List[str]:
    """Chunk text with Thai-friendly sentence segmentation when possible.

    Uses PyThaiNLP sent_tokenize if available; otherwise falls back to simple splitting.
    Chunking is character-based to handle Thai (no whitespace).
    """
    text = (text or "").strip()
    if not text:
        return []

    sentences: List[str]
    try:
        from pythainlp.tokenize import sent_tokenize  # type: ignore
        sentences = [s.strip() for s in sent_tokenize(text) if s and s.strip()]
    except Exception:
        # fallback: split on newlines and periods
        rough = text.replace("\r", "\n")
        parts = []
        for block in rough.split("\n"):
            block = block.strip()
            if not block:
                continue
            parts.extend([p.strip() for p in block.split(".") if p.strip()])
        sentences = parts or [text]

    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0

    def flush():
        nonlocal cur, cur_len
        if cur:
            chunks.append(" ".join(cur).strip())
        cur = []
        cur_len = 0

    for s in sentences:
        if not s:
            continue
        if cur_len + len(s) <= chunk_size:
            cur.append(s)
            cur_len += len(s)
        else:
            flush()
            # overlap: keep last ~2 sentences from previous chunk
            if overlap > 0 and chunks:
                prev = chunks[-1]
                overlap_text = prev[-overlap:]
                cur = [overlap_text, s]
                cur_len = len(overlap_text) + len(s)
            else:
                cur = [s]
                cur_len = len(s)

    flush()

    # drop tiny chunks
    chunks = [c for c in chunks if len(c.strip()) >= 20]
    return chunks
