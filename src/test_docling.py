"""
Simple test script to verify Docling integration is working.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the system path
sys.path.append(str(Path(__file__).parent.parent))

from src.document_pipeline import DoclingLoader, ExportType

def test_docling():
    """
    Test the Docling integration by processing a document.
    """
    # Get a sample document - change this to a real document on your system
    # Try to find a PDF file in the current directory or its parents
    sample_file = None
    current_dir = Path.cwd()
    
    # Look for PDF files
    for path in current_dir.glob('**/*.pdf'):
        if path.is_file():
            sample_file = str(path)
            break
    
    if not sample_file:
        print("No PDF file found. Please provide a path to a document file.")
        file_path = input("Enter path to a document file: ")
        if not file_path or not os.path.exists(file_path):
            print("Invalid file path.")
            return
        sample_file = file_path
    
    print(f"Testing with file: {sample_file}")
    
    try:
        # Initialize the loader
        loader = DoclingLoader(
            file_path=sample_file,
            export_type=ExportType.MARKDOWN  # Use MARKDOWN for simpler testing
        )
        
        # Load the document
        print("Loading document...")
        documents = loader.load()
        
        # Print document details
        print(f"Successfully processed {len(documents)} documents")
        for i, doc in enumerate(documents):
            print(f"\nDocument {i+1} details:")
            print(f"Content preview: {doc.page_content[:150]}...")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        
        print("\nDocling integration test successful!")
        return True
        
    except Exception as e:
        print(f"Error testing Docling integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_docling() 