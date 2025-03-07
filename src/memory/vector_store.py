import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for persistent memory in the construction management system.
    Provides methods to store and retrieve information using semantic search.
    """
    
    def __init__(self, collection_name: str = "construction_memory"):
        """
        Initialize the vector store with a collection name.
        
        Args:
            collection_name (str, optional): Collection name for the vector store
        """
        self.collection_name = collection_name
        self.persist_directory = os.path.join(os.path.dirname(__file__), "../../data/vectorstore")
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize vector store
        self._initialize_vector_store()
        
        logger.info(f"Vector store initialized with collection: {collection_name}")
    
    def _initialize_vector_store(self):
        """
        Initialize the vector store with Chroma.
        """
        try:
            # Try to load existing vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            logger.info(f"Loaded existing vector store from {self.persist_directory}")
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {str(e)}")
            logger.info("Creating new vector store")
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts (List[str]): List of text strings to add
            metadatas (Optional[List[Dict[str, Any]]], optional): Metadata for each text
            
        Returns:
            List[str]: List of IDs for the added texts
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # Split texts for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        split_texts = []
        split_metadatas = []
        
        for i, text in enumerate(texts):
            docs = text_splitter.create_documents([text], [metadatas[i]])
            for doc in docs:
                split_texts.append(doc.page_content)
                split_metadatas.append(doc.metadata)
        
        # Add to vector store
        ids = self.vector_store.add_texts(split_texts, split_metadatas)
        
        # Persist vector store to disk
        self.vector_store.persist()
        
        return ids
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Document]): List of Document objects to add
            
        Returns:
            List[str]: List of IDs for the added documents
        """
        # Split documents for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        split_docs = text_splitter.split_documents(documents)
        
        # Add to vector store
        ids = self.vector_store.add_documents(split_docs)
        
        # Persist vector store to disk
        self.vector_store.persist()
        
        return ids
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search for similar documents by query.
        
        Args:
            query (str): Query string to search for
            k (int, optional): Number of results to return
            
        Returns:
            List[Document]: List of similar documents
        """
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple[Document, float]]:
        """
        Search for similar documents with similarity scores.
        
        Args:
            query (str): Query string to search for
            k (int, optional): Number of results to return
            
        Returns:
            List[tuple[Document, float]]: List of document-score pairs
        """
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents from the vector store by IDs.
        
        Args:
            ids (List[str]): List of document IDs to delete
        """
        self.vector_store.delete(ids)
        self.vector_store.persist()
    
    def clear(self) -> None:
        """
        Clear all documents from the vector store.
        """
        try:
            self.vector_store.delete_collection()
            self._initialize_vector_store()
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise 