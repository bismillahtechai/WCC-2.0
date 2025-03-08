#!/usr/bin/env python
"""
Test script for the migration from DocumentProcessor to Docling.

This script demonstrates the migration from the old document processing pipeline
to the new Docling-based system. It processes a test document using both systems
and compares the results.
"""

import os
import sys
import logging
from pathlib import Path
import time
import argparse

# Add the src directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.document_pipeline import DoclingVectorStoreConnector, ExportType
from src.document_pipeline.document_processor import DocumentProcessor
from src.memory.vector_store import VectorStoreFactory
from src.memory.mem0_memory import Mem0Memory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_migration(file_path: str, use_old: bool = False, use_new: bool = True, test_mem0: bool = True):
    """
    Test the migration by processing a document with the old and/or new system.
    
    Args:
        file_path: Path to the document to process
        use_old: Whether to use the old document processor
        use_new: Whether to use the new docling connector
        test_mem0: Whether to test Mem0 integration
    """
    # Create vector store
    vector_store = VectorStoreFactory.create_vector_store(
        collection_name="test_migration"
    )
    
    # Create Mem0 instance for testing
    mem0 = Mem0Memory(client_id="test_migration")
    
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info(f"Testing with file: {file_path}")
    
    # Metadata for the document
    metadata = {
        "test": True,
        "migration_test": True,
        "timestamp": time.time()
    }
    
    # Process with old system if requested
    if use_old:
        try:
            logger.info("Processing with old DocumentProcessor...")
            start_time = time.time()
            
            # Initialize and register handlers
            document_processor = DocumentProcessor(vector_store=vector_store)
            
            # Set mem0 if testing mem0 integration
            if test_mem0:
                document_processor.mem0 = mem0
            
            # Try to import and register handlers
            try:
                from src.document_pipeline.handlers import PDFHandler, WordHandler, ExcelHandler
                
                # Register handlers
                document_processor.register_handler("application/pdf", PDFHandler)
                document_processor.register_handler("application/vnd.openxmlformats-officedocument.wordprocessingml.document", WordHandler)
                document_processor.register_handler("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ExcelHandler)
                
            except ImportError as e:
                logger.warning(f"Could not import some handlers: {e}")
            
            # Process the document
            processed_doc = document_processor.process_document(
                file_path=file_path,
                metadata=metadata
            )
            
            old_time = time.time() - start_time
            
            logger.info(f"Old system processed document in {old_time:.2f} seconds")
            logger.info(f"Document ID: {processed_doc.metadata.document_id}")
            logger.info(f"Content length: {len(processed_doc.content)} characters")
            logger.info(f"Content preview: {processed_doc.content[:150]}...")
        
        except Exception as e:
            logger.error(f"Error processing with old system: {e}")
    
    # Process with new system if requested
    if use_new:
        try:
            logger.info("Processing with new DoclingVectorStoreConnector...")
            start_time = time.time()
            
            # Initialize docling connector
            docling_connector = DoclingVectorStoreConnector(
                vector_store=vector_store,
                mem0=mem0 if test_mem0 else None,
                export_type=ExportType.DOC_CHUNKS
            )
            
            # Process the document
            documents = docling_connector.process_document(
                file_path=file_path,
                metadata=metadata
            )
            
            new_time = time.time() - start_time
            
            logger.info(f"New system processed document in {new_time:.2f} seconds")
            logger.info(f"Number of chunks: {len(documents)}")
            if documents:
                logger.info(f"First chunk content preview: {documents[0].page_content[:150]}...")
                logger.info(f"First chunk metadata: {documents[0].metadata}")
            
            # Test search functionality
            if documents:
                # Extract a few words from the first document for a search query
                words = documents[0].page_content.split()
                if len(words) >= 5:
                    query = " ".join(words[2:5])  # Use a few words from the middle
                    logger.info(f"Testing search with query: '{query}'")
                    
                    # Search for the document
                    results = docling_connector.search_documents(
                        query=query,
                        k=3
                    )
                    
                    logger.info(f"Search returned {len(results)} results")
                    if results:
                        logger.info(f"First result content preview: {results[0].page_content[:150]}...")
        
        except Exception as e:
            logger.error(f"Error processing with new system: {e}")
    
    # Test Mem0 integration if requested
    if test_mem0:
        try:
            logger.info("Testing Mem0 integration...")
            
            # Search for documents in Mem0
            memories = mem0.search(
                query="",
                category="documents",
                limit=10,
                sort_by_time=True
            )
            
            logger.info(f"Found {len(memories)} documents in Mem0")
            
            # Check documents in Mem0
            for i, memory in enumerate(memories):
                metadata = memory.get("metadata", {})
                logger.info(f"Memory {i+1}:")
                
                # Log different information based on document type
                if metadata.get("docling_processed"):
                    logger.info(f"  - Docling-processed document: {metadata.get('file_name', 'Unknown')}")
                    logger.info(f"  - Chunk count: {metadata.get('chunk_count', 0)}")
                else:
                    logger.info(f"  - Legacy document: {metadata.get('file_name', 'Unknown')}")
                    logger.info(f"  - Document ID: {metadata.get('document_id', 'Unknown')}")
                
                logger.info(f"  - Text preview: {memory.get('text', '')[:100]}...")
        
        except Exception as e:
            logger.error(f"Error testing Mem0 integration: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the migration from DocumentProcessor to Docling")
    parser.add_argument("file_path", help="Path to the document to process")
    parser.add_argument("--old", action="store_true", help="Use the old document processor")
    parser.add_argument("--new", action="store_true", help="Use the new docling connector")
    parser.add_argument("--no-mem0", action="store_true", help="Skip Mem0 integration testing")
    
    args = parser.parse_args()
    
    if not args.old and not args.new:
        # Default to using both systems
        args.old = True
        args.new = True
        
    test_migration(args.file_path, args.old, args.new, not args.no_mem0) 