import os
import logging
from typing import Dict, List, Any, Optional, BinaryIO, Union
import mimetypes
from pathlib import Path
import tempfile
import uuid

from ..utils.schema import DocumentMetadata, ProcessedDocument
from ..memory.vector_store import VectorStoreInterface
from ..memory.mem0_memory import Mem0Memory

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Core document processing pipeline that handles various document types
    and extracts text and metadata for storage and retrieval.
    """
    
    def __init__(
        self, 
        vector_store: Optional[VectorStoreInterface] = None,
        mem0: Optional[Mem0Memory] = None
    ):
        """
        Initialize the document processor with vector storage and memory components.
        
        Args:
            vector_store: Vector storage for document embeddings
            mem0: Mem0 memory system for storing document information
        """
        self.vector_store = vector_store
        self.mem0 = mem0 or Mem0Memory(client_id="document_processor")
        
        # Register handlers (will be implemented by specialized modules)
        self.handlers = {}
        
        # Set up mime type detection
        mimetypes.init()
        
        logger.info("Document processor initialized")
    
    def register_handler(self, mime_type: str, handler_class):
        """Register a document handler for a specific mime type."""
        self.handlers[mime_type] = handler_class
        logger.info(f"Registered handler for mime type: {mime_type}")
    
    def detect_mime_type(self, file_path: Union[str, Path], file_content: Optional[BinaryIO] = None) -> str:
        """
        Detect the MIME type of a file.
        
        Args:
            file_path: Path to the file
            file_content: File content if already loaded
            
        Returns:
            str: Detected MIME type
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        # First try by extension
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # If that fails, try by examining the file content
        if not mime_type and file_content:
            # This would need to be expanded with more sophisticated detection
            # Potentially using python-magic or similar library
            pass
            
        if not mime_type:
            mime_type = "application/octet-stream"  # Default unknown type
            
        logger.debug(f"Detected mime type {mime_type} for {file_path}")
        return mime_type
    
    def process_document(
        self, 
        file_path: Union[str, Path], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessedDocument:
        """
        Process a document file and extract text and metadata.
        
        Args:
            file_path: Path to the document file
            metadata: Additional metadata for the document
            
        Returns:
            ProcessedDocument: Processed document with text and metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
            
        # Detect the mime type
        mime_type = self.detect_mime_type(file_path)
        
        # Get the appropriate handler
        handler_class = self.handlers.get(mime_type)
        if not handler_class:
            logger.warning(f"No handler registered for mime type: {mime_type}")
            raise ValueError(f"Unsupported document type: {mime_type}")
            
        # Create the handler and process the document
        handler = handler_class()
        document_text, extracted_metadata = handler.process(file_path)
        
        # Combine extracted metadata with provided metadata
        combined_metadata = extracted_metadata or {}
        if metadata:
            combined_metadata.update(metadata)
            
        # Create document metadata object
        doc_metadata = DocumentMetadata(
            document_id=str(uuid.uuid4()),
            file_name=file_path.name,
            file_path=str(file_path),
            mime_type=mime_type,
            creation_time=file_path.stat().st_ctime,
            modification_time=file_path.stat().st_mtime,
            metadata=combined_metadata
        )
        
        # Create processed document
        processed_document = ProcessedDocument(
            metadata=doc_metadata,
            content=document_text
        )
        
        # Store in vector store if available
        if self.vector_store:
            self.vector_store.add_document(
                document_id=processed_document.metadata.document_id,
                text=document_text,
                metadata=combined_metadata
            )
            
        # Store in Mem0 memory
        self.mem0.add_memory(
            text=f"Document: {file_path.name}\n\nContent: {document_text[:1000]}...",
            category="documents",
            metadata={
                "document_id": processed_document.metadata.document_id,
                "file_name": file_path.name,
                "mime_type": mime_type,
                **combined_metadata
            }
        )
        
        logger.info(f"Processed document: {file_path.name} ({mime_type})")
        return processed_document
        
    def search_documents(
        self, 
        query: str, 
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using the vector store.
        
        Args:
            query: Search query
            limit: Maximum number of results
            metadata_filter: Filter by metadata fields
            
        Returns:
            List of document search results
        """
        if not self.vector_store:
            logger.error("Vector store not available for document search")
            raise ValueError("Vector store not configured for document search")
            
        results = self.vector_store.search(
            query=query,
            limit=limit,
            metadata_filter=metadata_filter
        )
        
        return results 