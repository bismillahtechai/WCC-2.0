"""
Example of using Docling for document processing.

This script demonstrates how to use the Docling integration to process 
different document types and integrate with a vector store for retrieval.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.document_pipeline import DoclingLoader, ExportType
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def process_documents_with_docling(file_paths, output_dir=None):
    """Process documents with Docling and store in a vector database."""
    
    # Initialize the document loader with chunking mode
    loader = DoclingLoader(
        file_path=file_paths,
        export_type=ExportType.DOC_CHUNKS,
    )
    
    # Load and process the documents
    print(f"Processing {len(file_paths)} documents...")
    documents = loader.load()
    print(f"Generated {len(documents)} chunks from the documents.")
    
    # Initialize embeddings model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Create a vector store with the processed documents
    if output_dir:
        persist_directory = output_dir
    else:
        persist_directory = "chroma_db"
        
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"Documents stored in vector database at {persist_directory}")
    return vectorstore

def search_documents(vectorstore, query, k=3):
    """Search for documents based on a query."""
    
    # Search the vector store
    results = vectorstore.similarity_search(query, k=k)
    
    print(f"\nSearch results for query: '{query}'")
    print("-" * 60)
    
    for i, doc in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Content: {doc.page_content[:150]}...")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        
        # Print headings if available
        if 'headings' in doc.metadata:
            print(f"Headings: {doc.metadata['headings']}")
            
        print("-" * 60)
    
    return results

def main():
    """Main function to demonstrate Docling usage."""
    
    # Example documents
    # Replace these with actual files on your system
    sample_files = [
        # Add your document paths here, e.g.:
        # "C:/path/to/document1.pdf",
        # "C:/path/to/document2.docx",
    ]
    
    # Check if files are provided as command-line arguments
    if len(sys.argv) > 1:
        sample_files = sys.argv[1:]
    
    # If no files are specified, print help and exit
    if not sample_files:
        print("Please provide document paths as arguments:")
        print("python docling_example.py path/to/doc1.pdf path/to/doc2.docx")
        return
    
    # Process documents
    vectorstore = process_documents_with_docling(sample_files)
    
    # Example searches
    search_documents(vectorstore, "What is the main topic of this document?")
    
    # Allow user to enter custom queries
    while True:
        query = input("\nEnter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        search_documents(vectorstore, query)

if __name__ == "__main__":
    main() 