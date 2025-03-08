# Docling Migration Guide for WCC 2.0

This guide provides instructions for migrating from the legacy document processing pipeline to the new Docling-based system in WCC 2.0. This migration improves document processing capabilities, OCR quality, and integration with vector databases.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Install Dependencies](#step-1-install-dependencies)
4. [Step 2: Update Import Statements](#step-2-update-import-statements)
5. [Step 3: Replace Document Processing Code](#step-3-replace-document-processing-code)
6. [Step 4: Adapt Search Functionality](#step-4-adapt-search-functionality)
7. [Step 5: Handle Document Retrieval](#step-5-handle-document-retrieval)
8. [Step 6: Mem0 Integration](#step-6-mem0-integration)
9. [Testing the Migration](#testing-the-migration)
10. [Troubleshooting](#troubleshooting)

## Overview

The migration replaces the old `DocumentProcessor` class with the new Docling-based system. The key changes include:

- Using `DoclingLoader` for document processing
- Using `DoclingVectorStoreConnector` for integration with vector stores
- Supporting chunked document storage for better retrieval
- Maintaining compatibility with Mem0 for document history and tracking

## Prerequisites

- Python 3.8+
- Working WCC 2.0 installation
- Appropriate database access (PostgreSQL with pgvector extension)

## Step 1: Install Dependencies

Add docling to your requirements.txt file:

```python
docling>=0.1.0
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

## Step 2: Update Import Statements

Replace imports from the old document processor with the new Docling-based system:

**Old Code:**
```python
from document_pipeline import DocumentProcessor
from document_pipeline.handlers import PDFHandler
```

**New Code:**
```python
from document_pipeline import DoclingLoader, ExportType, DoclingVectorStoreConnector
```

## Step 3: Replace Document Processing Code

### Old Code

```python
# Initialize the document processor
document_processor = DocumentProcessor(vector_store=vector_store)

# Register handlers
document_processor.register_handler("application/pdf", PDFHandler)
# ... register other handlers

# Process a document
processed_doc = document_processor.process_document(
    file_path="path/to/document.pdf", 
    metadata={"key": "value"}
)

# Access document content and metadata
document_text = processed_doc.content
document_metadata = processed_doc.metadata
```

### New Code

```python
# Initialize the docling connector
docling_connector = DoclingVectorStoreConnector(
    vector_store=vector_store,
    mem0=mem0,  # Include mem0 instance if available
    export_type=ExportType.DOC_CHUNKS  # or ExportType.MARKDOWN
)

# Process a document - no need to register handlers
documents = docling_connector.process_document(
    file_path="path/to/document.pdf",
    metadata={"key": "value"}
)

# Access document content and metadata (now we have multiple chunks)
for doc in documents:
    document_text = doc.page_content
    document_metadata = doc.metadata
```

## Step 4: Adapt Search Functionality

### Old Code

```python
search_results = document_processor.search_documents(
    query="search query",
    limit=5,
    metadata_filter={"key": "value"}
)
```

### New Code

```python
search_results = docling_connector.search_documents(
    query="search query",
    k=5,
    metadata_filter={"key": "value"}
)

# Format results as needed
for doc in search_results:
    content = doc.page_content
    metadata = doc.metadata
```

## Step 5: Handle Document Retrieval

Document retrieval by ID may need to be updated:

### Old Code

```python
documents = vector_store.get_documents_by_id([document_id])
document = documents[0]
```

### New Code

```python
# If vector store has a get_documents_by_id method
if hasattr(vector_store, 'get_documents_by_id'):
    documents = vector_store.get_documents_by_id([document_id])
    document = documents[0]
else:
    # Try to search by metadata filter
    results = docling_connector.search_documents(
        query="",  # Empty query to match based on metadata only
        k=1,
        metadata_filter={"source_id": document_id}  # Depends on how IDs are stored
    )
    document = results[0]
```

## Step 6: Mem0 Integration

The docling connector integrates with Mem0 memory to maintain backward compatibility:

### Initializing with Mem0

```python
from memory.mem0_memory import Mem0Memory

# Create a Mem0 instance
mem0 = Mem0Memory(client_id="my_client")

# Pass it to the docling connector
docling_connector = DoclingVectorStoreConnector(
    vector_store=vector_store,
    mem0=mem0,
    export_type=ExportType.DOC_CHUNKS
)
```

### Working with Document History

If you're using the `_list_recent_documents` functionality, note that the metadata structure is slightly different for docling-processed documents:

```python
# Get recent documents from Mem0
memories = mem0.search(
    query="",
    category="documents",
    limit=10,
    sort_by_time=True
)

# Process document information
for memory in memories:
    metadata = memory.get("metadata", {})
    
    # Check if it's a docling-processed document
    if metadata.get("docling_processed"):
        # Docling-specific information
        chunk_count = metadata.get("chunk_count", 1)
        source = metadata.get("source", "")
        # Process accordingly
    else:
        # Legacy document processing
        document_id = metadata.get("document_id", "")
        mime_type = metadata.get("mime_type", "")
        # Process accordingly
```

## Testing the Migration

We've included a test script to compare the old and new systems:

```bash
python scripts/test_docling_migration.py path/to/document.pdf
```

This script processes a document with both the old and new systems, allowing you to compare the results.

## Troubleshooting

### Document Not Found

If you're getting "Document not found" errors when trying to retrieve by ID, you may need to adapt your search strategy. The old system stored document IDs differently from Docling.

### OCR Issues

Docling has different OCR settings. If you're having issues with OCR:

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Create custom pipeline options
pipeline_options = PdfPipelineOptions(
    run_ocr=True,  # Enable OCR
    ocr_lang="eng",  # OCR language
)

# Configure the converter
converter = DocumentConverter(
    pdf_pipeline_options=pipeline_options
)

# Use the custom converter with the connector
documents = docling_connector.process_document(
    file_path="path/to/document.pdf",
    converter=converter
)
```

### Chunking Strategy

If the default chunking strategy isn't suitable for your documents, you can customize it:

```python
from docling.chunking import HybridChunker

chunker = HybridChunker(
    chunk_size=512,
    chunk_overlap=50
)

documents = docling_connector.process_document(
    file_path="path/to/document.pdf",
    chunker=chunker
)
```

For further assistance, refer to:
- [Docling official documentation](https://ds4sd.github.io/docling/)
- The example scripts in the `examples/` directory 