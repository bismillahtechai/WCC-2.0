# Document Pipeline with Docling

This module provides document processing capabilities using [Docling](https://github.com/DS4SD/docling), an advanced document processing library developed by IBM.

## Overview

Docling provides powerful document parsing and understanding capabilities for various document formats, including:

- PDF documents with layout and table understanding
- Word documents (DOCX)
- PowerPoint presentations (PPTX)
- Excel spreadsheets (XLSX)
- HTML documents
- Images
- And more

## Installation

Make sure you have installed the required dependencies:

```bash
pip install docling langchain langchain-core
```

## Using the DoclingLoader

The `DoclingLoader` class provides integration with the LangChain ecosystem. Here's how to use it:

```python
from document_pipeline import DoclingLoader, ExportType

# Initialize the loader with document paths
loader = DoclingLoader(
    file_path=["path/to/document.pdf", "path/to/another_document.docx"],
    export_type=ExportType.DOC_CHUNKS  # or ExportType.MARKDOWN
)

# Load and process the documents
documents = loader.load()

# Process documents
for doc in documents:
    print(f"Content: {doc.page_content[:100]}...")
    print(f"Source: {doc.metadata.get('source')}")
    print("---")
```

### Export Types

The DoclingLoader supports two export modes:

1. `ExportType.DOC_CHUNKS` (default): Processes each document and splits it into semantic chunks for retrieval
2. `ExportType.MARKDOWN`: Processes each document and returns it as a single Markdown document

### Using with Vector Stores

You can easily integrate with LangChain vector stores for document retrieval:

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Initialize the document loader
loader = DoclingLoader(file_path=["path/to/document.pdf"])
documents = loader.load()

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Create vector store
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="chroma_db"
)

# Search documents
results = vectorstore.similarity_search("What is the main topic?", k=3)
```

## Features Provided by Docling

Docling provides several advanced features:

- Rich document understanding including layout, tables, and structure
- Document hierarchy preservation
- Advanced text extraction
- OCR for images and scanned documents
- Multiple export formats
- AI model-based document analysis
- Seamless integration with AI frameworks

## Example Scripts

See the `examples/docling_example.py` script for a complete example of how to use the Docling integration for document processing and retrieval. 