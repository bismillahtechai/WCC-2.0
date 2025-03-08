from langchain.agents import Tool
from typing import List, Dict, Any, Optional
import logging
import json
import os
from pathlib import Path

from .base_agent import BaseAgent
from ..document_pipeline import DoclingVectorStoreConnector, ExportType
from ..memory.vector_store import VectorStoreFactory
from ..utils.schema import DocumentRequest, DocumentSearchRequest

logger = logging.getLogger(__name__)

class DocumentAgent(BaseAgent):
    """
    Document Processing Agent responsible for ingesting, processing,
    and retrieving documents related to construction projects.
    """
    
    def __init__(self):
        """
        Initialize the Document Processing Agent with docling connector.
        """
        # Initialize base agent first to set up mem0
        super().__init__(
            name="Document Processing",
            description="document processing, OCR, information extraction, and document search for construction documents"
        )
        
        # Initialize vector store
        self.vector_store = VectorStoreFactory.create_vector_store()
        
        # Initialize docling connector instead of document processor
        self.docling_connector = DoclingVectorStoreConnector(
            vector_store=self.vector_store,
            mem0=self.mem0,  # Pass the agent's mem0 instance
            export_type=ExportType.DOC_CHUNKS
        )
        
    def _get_tools(self) -> List[Tool]:
        """
        Get the tools for the Document Processing Agent.
        
        Returns:
            List[Tool]: List of tools for the agent
        """
        tools = [
            Tool(
                name="Process Document",
                func=self._process_document,
                description="Process a document file to extract text and metadata"
            ),
            Tool(
                name="Search Documents",
                func=self._search_documents,
                description="Search for documents based on content"
            ),
            Tool(
                name="Get Document By ID",
                func=self._get_document_by_id,
                description="Retrieve a document by its ID"
            ),
            Tool(
                name="List Recent Documents",
                func=self._list_recent_documents,
                description="List recently processed documents"
            ),
            Tool(
                name="Extract Entities From Document",
                func=self._extract_entities,
                description="Extract named entities from a document (people, organizations, locations, dates, etc.)"
            )
        ]
        return tools
        
    def _process_document(self, document_request_json: str) -> str:
        """
        Process a document file using docling.
        
        Args:
            document_request_json (str): JSON string with document request parameters
            
        Returns:
            str: JSON response with processing results
        """
        try:
            # Parse the request
            request_dict = json.loads(document_request_json)
            document_request = DocumentRequest(**request_dict)
            
            # Check if the file exists
            file_path = Path(document_request.file_path)
            if not file_path.exists():
                return json.dumps({
                    "success": False,
                    "error": f"File not found: {document_request.file_path}"
                })
            
            # Process the document using docling connector
            documents = self.docling_connector.process_document(
                file_path=document_request.file_path,
                metadata=document_request.metadata
            )
            
            # Return success response
            return json.dumps({
                "success": True,
                "message": f"Document processed successfully: {file_path.name}",
                "document_count": len(documents),
                "first_chunk_preview": documents[0].page_content[:100] if documents else ""
            })
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Error processing document: {str(e)}"
            })
            
    def _search_documents(self, search_request_json: str) -> str:
        """
        Search for documents based on content.
        
        Args:
            search_request_json (str): JSON string with search parameters
            
        Returns:
            str: JSON response with search results
        """
        try:
            # Parse the request
            request_dict = json.loads(search_request_json)
            search_request = DocumentSearchRequest(**request_dict)
            
            # Search for documents using docling connector
            results = self.docling_connector.search_documents(
                query=search_request.query,
                k=search_request.limit,
                metadata_filter=search_request.metadata_filter
            )
            
            # Format the results
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
                
            # Return search results
            return json.dumps({
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results)
            })
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Error searching documents: {str(e)}"
            })
            
    def _get_document_by_id(self, document_id: str) -> str:
        """
        Retrieve a document by its ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            JSON string with document information
        """
        try:
            # Find document in vector store
            # Note: Implementation depends on the specific vector store being used
            # We're assuming there's a method or we can do a metadata search
            
            # Option 1: If vector store has a direct method to get by ID
            if hasattr(self.vector_store, 'get_documents_by_id'):
                documents = self.vector_store.get_documents_by_id([document_id])
                
                if not documents:
                    return json.dumps({
                        "success": False,
                        "error": f"Document not found with ID: {document_id}"
                    })
                    
                document = documents[0]
                
                # Return success response for direct method
                return json.dumps({
                    "success": True,
                    "document_id": document.get("id") or document_id,
                    "content": document.get("text", ""),
                    "metadata": document.get("metadata", {})
                })
            
            # Option 2: Fall back to metadata search if no direct method
            else:
                # Try to search by metadata filter
                results = self.docling_connector.search_documents(
                    query="",  # Empty query to match based on metadata only
                    k=1,
                    metadata_filter={"source_id": document_id}  # Depends on how IDs are stored
                )
                
                if not results:
                    return json.dumps({
                        "success": False,
                        "error": f"Document not found with ID: {document_id}"
                    })
                
                document = results[0]
                
                # Return success response for metadata search
                return json.dumps({
                    "success": True,
                    "document_id": document_id,
                    "content": document.page_content,
                    "metadata": document.metadata
                })
            
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Error retrieving document: {str(e)}"
            })
            
    def _list_recent_documents(self, limit: int = 10) -> str:
        """
        List recently processed documents.
        
        Args:
            limit: Maximum number of documents to list
            
        Returns:
            JSON string with list of recent documents
        """
        try:
            # Get recent memories from the document category
            memories = self.mem0.search(
                query="",
                category="documents",
                limit=limit,
                sort_by_time=True
            )
            
            documents = []
            for memory in memories:
                metadata = memory.get("metadata", {})
                
                # Extract document information (format is different between old and docling-processed docs)
                document_info = {
                    "file_name": metadata.get("file_name", ""),
                    "timestamp": memory.get("timestamp", 0),
                    "metadata": metadata
                }
                
                # Add docling-specific information if present
                if metadata.get("docling_processed"):
                    document_info["processing_type"] = "docling"
                    document_info["chunk_count"] = metadata.get("chunk_count", 1)
                    # Include source document ID if available
                    if "source" in metadata:
                        document_info["source"] = metadata["source"]
                else:
                    # Old document processing
                    document_info["processing_type"] = "legacy"
                    document_info["document_id"] = metadata.get("document_id", "")
                    document_info["mime_type"] = metadata.get("mime_type", "")
                
                documents.append(document_info)
                
            # Return success response
            return json.dumps({
                "success": True,
                "documents": documents
            })
            
        except Exception as e:
            logger.error(f"Error listing recent documents: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Error listing recent documents: {str(e)}"
            })
            
    def _extract_entities(self, document_id: str) -> str:
        """
        Extract named entities from a document.
        
        Args:
            document_id: ID of the document to extract entities from
            
        Returns:
            JSON string with extracted entities
        """
        try:
            # Get document content
            documents = self.vector_store.get_documents_by_id([document_id])
            
            if not documents:
                return json.dumps({
                    "success": False,
                    "error": f"Document not found with ID: {document_id}"
                })
                
            document = documents[0]
            text = document.get("text", "")
            
            if not text:
                return json.dumps({
                    "success": False,
                    "error": "Document has no text content"
                })
                
            # Check if spaCy is available
            try:
                import spacy
                from spacy import displacy
                
                # Load spaCy model - use a larger model if available
                try:
                    nlp = spacy.load("en_core_web_lg")
                except OSError:
                    try:
                        nlp = spacy.load("en_core_web_md")
                    except OSError:
                        nlp = spacy.load("en_core_web_sm")
                        
                # Process text with spaCy
                doc = nlp(text[:100000])  # Limit text to avoid memory issues
                
                # Extract named entities
                entities = {}
                for ent in doc.ents:
                    entity_type = ent.label_
                    if entity_type not in entities:
                        entities[entity_type] = []
                    if ent.text not in entities[entity_type]:
                        entities[entity_type].append(ent.text)
                        
                # Return success response
                return json.dumps({
                    "success": True,
                    "document_id": document_id,
                    "entities": entities
                })
                
            except ImportError:
                # Fallback to basic entity extraction if spaCy not available
                return json.dumps({
                    "success": False,
                    "error": "NLP dependencies not available. Install spaCy with: pip install spacy && python -m spacy download en_core_web_sm"
                })
                
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            }) 