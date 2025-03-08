"""
Docling Integration Module

This module provides integration between Docling and the WCC 2.0 vector store system,
allowing documents processed with Docling to be seamlessly stored in the same vector
database that agents have access to.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from langchain.docstore.document import Document
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

from ..memory.vector_store import VectorStoreFactory
from ..memory.mem0_memory import Mem0Memory
from ..document_pipeline import DoclingLoader, ExportType

logger = logging.getLogger(__name__)

class DoclingVectorStoreConnector:
    """
    Connector class that bridges Docling document processing with the WCC 2.0 vector store system.
    """
    
    def __init__(
        self,
        vector_store=None,
        mem0=None,
        collection_name: str = "construction_vectors",
        store_type: str = None,
        export_type: ExportType = ExportType.DOC_CHUNKS,
    ):
        """
        Initialize the connector.
        
        Args:
            vector_store: Optional existing vector store instance to use
            mem0: Optional existing Mem0Memory instance to use
            collection_name: Name of the collection to use in the vector store
            store_type: Type of vector store to use if not provided
            export_type: How to export documents from Docling (chunks or markdown)
        """
        self.export_type = export_type
        self.vector_store = vector_store or VectorStoreFactory.create_vector_store(
            store_type=store_type,
            collection_name=collection_name
        )
        self.mem0 = mem0 or Mem0Memory(client_id="docling_processor")
        logger.info(f"DoclingVectorStoreConnector initialized with {self.export_type.value} export type")
    
    def process_document(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
        chunker=None,
        converter=None,
        convert_kwargs: Optional[Dict[str, Any]] = None,
        md_export_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Process a document with Docling and store it in the vector store.
        
        Args:
            file_path: Path to the document file
            metadata: Additional metadata for the document
            chunker: Optional custom chunker
            converter: Optional custom document converter
            convert_kwargs: Additional arguments for document conversion
            md_export_kwargs: Additional arguments for Markdown export
            
        Returns:
            List of processed LangChain Document objects
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        # Initialize the Docling loader
        loader = DoclingLoader(
            file_path=str(file_path),
            export_type=self.export_type,
            chunker=chunker,
            converter=converter,
            convert_kwargs=convert_kwargs,
            md_export_kwargs=md_export_kwargs,
        )
        
        # Process the document
        documents = loader.load()
        
        # Enhance metadata
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
        
        # Store documents in vector store
        self.vector_store.add_documents(documents)
        
        # Store in Mem0 memory - consolidate content from chunks for mem0
        combined_content = ""
        doc_metadata = {}
        
        # Get content and metadata from first chunk as base
        if documents:
            combined_content = documents[0].page_content
            doc_metadata = documents[0].metadata.copy()
            
            # If we have multiple chunks, add context about the chunking
            if len(documents) > 1:
                # Add some content from each chunk (limited to keep memory entry reasonable)
                for i, doc in enumerate(documents[1:], start=1):
                    if i <= 3:  # Only add previews for first few chunks
                        combined_content += f"\n\nChunk {i+1} preview: {doc.page_content[:150]}..."
                    else:
                        break
                
                # Add info about total chunks
                doc_metadata["total_chunks"] = len(documents)
        
        # Add document to mem0
        self.mem0.add_memory(
            text=f"Document: {file_path.name}\n\nContent preview: {combined_content[:1000]}...",
            category="documents",
            metadata={
                "file_name": file_path.name,
                "docling_processed": True,
                "chunk_count": len(documents),
                **doc_metadata
            }
        )
        
        logger.info(f"Processed and stored document: {file_path.name} "
                  f"(created {len(documents)} document chunks)")
        
        return documents
    
    def search_documents(
        self,
        query: str,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for documents in the vector store.
        
        Args:
            query: Search query
            k: Maximum number of results
            metadata_filter: Filter by metadata fields
            
        Returns:
            List of document search results
        """
        # Currently metadata filters are not directly supported in all vector stores
        # This is a simplified implementation
        return self.vector_store.similarity_search(query, k=k)
    
    def search_documents_with_score(
        self,
        query: str,
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        Search for documents in the vector store and return relevance scores.
        
        Args:
            query: Search query
            k: Maximum number of results
            
        Returns:
            List of (document, score) tuples
        """
        return self.vector_store.similarity_search_with_score(query, k=k) 