import os
import logging
import time
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, JSON, Text, Float, select, delete
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from langchain.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Define SQLAlchemy Base
Base = declarative_base()

class PostgresVectorStore:
    """
    PostgreSQL vector store with pgvector extension for the construction management system.
    Provides methods to store and retrieve information using vector similarity search.
    """
    
    def __init__(self, collection_name: str = "construction_vectors"):
        """
        Initialize the PostgreSQL vector store.
        
        Args:
            collection_name (str, optional): Collection name for the vector store
        """
        self.collection_name = collection_name
        
        # Check for DATABASE_URL first (Render provides this)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Use the DATABASE_URL directly
            logger.info("Using DATABASE_URL for connection")
            # Ensure sslmode is set properly for Render
            if "sslmode" not in database_url:
                if "?" in database_url:
                    database_url += "&sslmode=require"
                else:
                    database_url += "?sslmode=require"
            self.connection_string = database_url
        else:
            # Get PostgreSQL connection information
            self.host = os.getenv("POSTGRES_HOST", "localhost")
            self.port = os.getenv("POSTGRES_PORT", "5432")
            self.user = os.getenv("POSTGRES_USER", "postgres")
            self.password = os.getenv("POSTGRES_PASSWORD", "postgres")
            self.database = os.getenv("POSTGRES_DB", "construction_management")
            
            # URL encode password to handle special characters
            encoded_password = urllib.parse.quote_plus(self.password)
            
            # Build connection string with SSL mode for Render
            self.connection_string = f"postgresql+psycopg2://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}?sslmode=require"
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize SQLAlchemy engine with connection pooling settings
        self.engine = create_engine(
            self.connection_string,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize PGVector with retries
        self._initialize_pgvector_with_retries()
        
        logger.info(f"PostgreSQL vector store initialized with collection: {collection_name}")
    
    def _initialize_pgvector_with_retries(self, max_retries=5, retry_delay=5):
        """
        Initialize pgvector extension with retry logic for better resilience.
        """
        for attempt in range(max_retries):
            try:
                self._initialize_pgvector()
                return
            except Exception as e:
                logger.error(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("All attempts to initialize pgvector failed")
                    raise
    
    def _initialize_pgvector(self):
        """
        Initialize pgvector extension and create necessary tables.
        """
        try:
            # Create database connection
            with self.engine.connect() as conn:
                # Check if pgvector extension exists
                result = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if not result.scalar():
                    # Create pgvector extension
                    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    conn.commit()
                    logger.info("Created pgvector extension")
            
            # Initialize PGVector from LangChain
            self.vectorstore = PGVector(
                collection_name=self.collection_name,
                connection_string=self.connection_string,
                embedding_function=self.embeddings
            )
            
            logger.info(f"PGVector initialized with collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing pgvector: {str(e)}")
            raise
    
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
        ids = self.vectorstore.add_texts(split_texts, split_metadatas)
        
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
        ids = self.vectorstore.add_documents(split_docs)
        
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
        return self.vectorstore.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search for similar documents with similarity scores.
        
        Args:
            query (str): Query string to search for
            k (int, optional): Number of results to return
            
        Returns:
            List[Tuple[Document, float]]: List of document-score pairs
        """
        return self.vectorstore.similarity_search_with_score(query, k=k)
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents from the vector store by IDs.
        
        Args:
            ids (List[str]): List of document IDs to delete
        """
        for doc_id in ids:
            self.vectorstore.delete(doc_id)
    
    def clear(self) -> None:
        """
        Clear all documents from the vector store.
        """
        try:
            # Get the table name used by PGVector
            table_name = f"{self.collection_name}_embeddings"
            
            # Execute delete query
            with self.engine.connect() as conn:
                conn.execute(f"DELETE FROM {table_name}")
                conn.commit()
                
            logger.info(f"Cleared all documents from collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise


class VectorStoreFactory:
    """
    Factory for creating vector stores.
    """
    
    @staticmethod
    def create_vector_store(store_type: str = None, collection_name: str = "construction_vectors") -> Any:
        """
        Create a vector store based on the specified type.
        
        Args:
            store_type (str, optional): Type of vector store (postgres, chroma, pinecone)
            collection_name (str, optional): Collection name for the vector store
            
        Returns:
            Any: Vector store instance
        """
        # If no store_type specified, get from environment variable
        if store_type is None:
            store_type = os.getenv("VECTOR_DB_TYPE", "postgres").lower()
        
        logger.info(f"Creating vector store of type: {store_type}")
        
        if store_type == "postgres":
            return PostgresVectorStore(collection_name=collection_name)
        elif store_type == "chroma":
            from .vector_store import VectorStore
            return VectorStore(collection_name=collection_name)
        elif store_type == "pinecone":
            # This would need to be implemented
            raise NotImplementedError("Pinecone vector store not implemented yet")
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}") 