"""
Document processor for RAG pipeline

This module provides:
- Document ingestion
- Chunking strategies
- Metadata extraction
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents for RAG pipeline"""

    def __init__(self):
        """Initialize document processor"""
        self.chunk_size = 1000
        self.chunk_overlap = 200

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        """
        Split text into chunks

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - chunk_overlap

        return chunks

    def extract_metadata(
        self,
        text: str,
        source: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from document

        Args:
            text: Document text
            source: Document source

        Returns:
            Metadata dictionary
        """
        return {
            "source": source,
            "word_count": len(text.split()),
            "character_count": len(text),
            "created_at": datetime.utcnow().isoformat()
        }

    async def process_document(
        self,
        text: str,
        source: str,
        chunk_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a document into chunks with metadata

        Args:
            text: Document text
            source: Document source
            chunk_size: Size of each chunk

        Returns:
            List of document chunks with metadata
        """
        chunks = self.chunk_text(text, chunk_size)
        metadata = self.extract_metadata(text, source)

        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                "id": f"{source}-chunk-{i}",
                "content": chunk,
                "chunk_index": i,
                "metadata": metadata
            })

        return processed_chunks