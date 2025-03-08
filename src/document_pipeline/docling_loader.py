"""
DoclingLoader for integration with LangChain.

This module provides a custom loader to replace the existing document pipeline
with Docling functionality.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any, Iterable

from langchain_core.documents import Document
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker


class ExportType(Enum):
    """Export type options for the DoclingLoader."""
    
    MARKDOWN = "markdown"
    DOC_CHUNKS = "doc_chunks"


class DoclingLoader:
    """
    A document loader that uses Docling to process various document formats.
    
    This loader converts documents to either Markdown or chunked representation,
    and returns LangChain Document objects.
    """
    
    def __init__(
        self,
        file_path: Union[str, List[str]],
        export_type: ExportType = ExportType.DOC_CHUNKS,
        chunker=None,
        converter=None,
        convert_kwargs: Optional[Dict[str, Any]] = None,
        md_export_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the DoclingLoader.
        
        Args:
            file_path: The path(s) to the document file(s) to load.
            export_type: How to export the documents (default: DOC_CHUNKS).
            chunker: Custom chunker to use for DOC_CHUNKS mode (default: HybridChunker).
            converter: Custom Docling converter to use (default: new DocumentConverter).
            convert_kwargs: Additional arguments for document conversion.
            md_export_kwargs: Additional arguments for Markdown export.
        """
        self.file_paths = [file_path] if isinstance(file_path, str) else file_path
        self.export_type = export_type
        self.converter = converter or DocumentConverter()
        self.convert_kwargs = convert_kwargs or {}
        self.md_export_kwargs = md_export_kwargs or {}
        
        # Set up chunker for DOC_CHUNKS mode
        if export_type == ExportType.DOC_CHUNKS:
            self.chunker = chunker or HybridChunker()
    
    def load(self) -> List[Document]:
        """
        Load documents and convert them to LangChain Document objects.
        
        Returns:
            A list of LangChain Document objects.
        """
        docs = []
        
        for source in self.file_paths:
            # Convert the document using Docling
            result = self.converter.convert(source, **self.convert_kwargs)
            doc = result.document
            
            if self.export_type == ExportType.MARKDOWN:
                # Convert to Markdown and create a single Document
                markdown_content = doc.export_to_markdown(**self.md_export_kwargs)
                docs.append(
                    Document(
                        page_content=markdown_content,
                        metadata={
                            "source": source,
                            "format": "markdown",
                        }
                    )
                )
            else:  # ExportType.DOC_CHUNKS
                # Create chunks using the chunker
                chunks = self.chunker.chunk(doc)
                
                # Convert each chunk to a Document
                for chunk in chunks:
                    # Extract metadata from the chunk
                    metadata = {
                        "source": source,
                        "format": "chunk",
                    }
                    
                    # Add any available metadata from the chunk
                    if hasattr(chunk, "metadata") and chunk.metadata:
                        # Include headings if available
                        if hasattr(chunk.metadata, "headings") and chunk.metadata.headings:
                            metadata["headings"] = chunk.metadata.headings
                        
                        # Include provenance info if available
                        if hasattr(chunk.metadata, "dl_meta") and chunk.metadata.dl_meta:
                            metadata["dl_meta"] = chunk.metadata.dl_meta
                    
                    # Create the Document
                    docs.append(
                        Document(
                            page_content=chunk.text,
                            metadata=metadata
                        )
                    )
        
        return docs

    def lazy_load(self) -> Iterable[Document]:
        """
        Lazily load documents for memory-efficient processing.
        
        Yields:
            LangChain Document objects one at a time.
        """
        for source in self.file_paths:
            # Convert the document using Docling
            result = self.converter.convert(source, **self.convert_kwargs)
            doc = result.document
            
            if self.export_type == ExportType.MARKDOWN:
                # Convert to Markdown and create a single Document
                markdown_content = doc.export_to_markdown(**self.md_export_kwargs)
                yield Document(
                    page_content=markdown_content,
                    metadata={
                        "source": source,
                        "format": "markdown",
                    }
                )
            else:  # ExportType.DOC_CHUNKS
                # Create chunks using the chunker
                chunks = self.chunker.chunk(doc)
                
                # Yield each chunk as a Document
                for chunk in chunks:
                    # Extract metadata from the chunk
                    metadata = {
                        "source": source,
                        "format": "chunk",
                    }
                    
                    # Add any available metadata from the chunk
                    if hasattr(chunk, "metadata") and chunk.metadata:
                        # Include headings if available
                        if hasattr(chunk.metadata, "headings") and chunk.metadata.headings:
                            metadata["headings"] = chunk.metadata.headings
                        
                        # Include provenance info if available
                        if hasattr(chunk.metadata, "dl_meta") and chunk.metadata.dl_meta:
                            metadata["dl_meta"] = chunk.metadata.dl_meta
                    
                    # Yield the Document
                    yield Document(
                        page_content=chunk.text,
                        metadata=metadata
                    ) 