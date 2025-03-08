# Migration Guide: Transitioning to Docling

This guide will help you migrate from the old `DocumentProcessor` system to the new Docling-based document processing pipeline.

## Why Migrate to Docling?

Docling offers several advantages over the previous document processing system:

1. **Advanced Document Understanding**: Docling provides better layout analysis, table extraction, and hierarchical structure understanding.
2. **More Document Formats**: Support for a wider range of document formats out of the box.
3. **AI-Powered Processing**: Docling leverages specialized AI models for better document comprehension.
4. **Better OCR**: Enhanced OCR capabilities for images and scanned documents.
5. **Rich Metadata**: More detailed document metadata and provenance information.
6. **Modern Architecture**: Built on a modern, maintainable codebase with active development.

## Step-by-Step Migration

### Step 1: Update Dependencies

First, ensure you have installed Docling and its dependencies:

```bash
pip install docling langchain langchain-core
```

### Step 2: Replace Imports

In your existing code, replace imports from the old document processor with the new Docling-based system:

**Old Code:**
```python
from document_pipeline import DocumentProcessor
from document_pipeline.handlers import PDFHandler
```

**New Code:**
```python
from document_pipeline import DoclingLoader, ExportType
```

### Step 3: Replace Document Processor Initialization

**Old Code:**
```python
from your_vector_store import VectorStore

vector_store = VectorStore()
document_processor = DocumentProcessor(vector_store=vector_store)
```

**New Code:**
```python
from document_pipeline import DoclingLoader, ExportType

loader = DoclingLoader(
    file_path=[],  # Will be populated later with specific files
    export_type=ExportType.DOC_CHUNKS
)
```

### Step 4: Replace Document Processing Logic

**Old Code:**
```python
# Process a document
processed_doc = document_processor.process_document("path/to/document.pdf")

# Extract text and metadata
document_text = processed_doc.content
document_metadata = processed_doc.metadata
```

**New Code:**
```python
# Process a document
loader = DoclingLoader(file_path="path/to/document.pdf")
documents = loader.load()

# The documents are already in LangChain Document format with text and metadata
for doc in documents:
    document_text = doc.page_content
    document_metadata = doc.metadata
```

### Step 5: Replace Search Functionality

**Old Code:**
```python
search_results = document_processor.search_documents(
    query="What is the main topic?",
    limit=5
)
```

**New Code:**
```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# First load documents
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
search_results = vectorstore.similarity_search(
    query="What is the main topic?",
    k=5
)
```

## Working with Document Chunks vs. Full Documents

With Docling, you have two options for document representation:

### Option 1: Document Chunks (Recommended for RAG applications)

```python
loader = DoclingLoader(
    file_path=["path/to/document.pdf"],
    export_type=ExportType.DOC_CHUNKS
)
```

This mode splits documents into semantic chunks, which is ideal for:
- Retrieval-Augmented Generation (RAG)
- Question-answering systems
- Semantic search applications
- Systems that need focused context

### Option 2: Full Markdown Documents

```python
loader = DoclingLoader(
    file_path=["path/to/document.pdf"],
    export_type=ExportType.MARKDOWN
)
```

This mode keeps each document as a single entity, which is ideal for:
- Document classification
- When you want to preserve the entire document context
- For further custom processing

## Customizing Docling

### Using Custom Chunking

```python
from docling.chunking import HybridChunker

chunker = HybridChunker(
    chunk_size=512,
    chunk_overlap=50
)

loader = DoclingLoader(
    file_path=["path/to/document.pdf"],
    chunker=chunker
)
```

### Using Custom Document Converter Options

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Create custom pipeline options
pipeline_options = PdfPipelineOptions(
    run_ocr=True,  # Enable OCR
    ocr_lang="eng",  # OCR language
    extract_tables=True,  # Extract tables
)

# Configure the converter
converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF, InputFormat.DOCX],
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)

# Use the custom converter with the loader
loader = DoclingLoader(
    file_path=["path/to/document.pdf"],
    converter=converter
)
```

## Need Help?

If you encounter any issues during migration, please refer to:
- Docling official documentation: https://ds4sd.github.io/docling/
- The example scripts in the `examples/` directory
- Create an issue on the project repository for assistance 