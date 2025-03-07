import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
import time
import mem0ai
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Mem0Memory:
    """
    Mem0 memory system for persistent memory in the construction management system.
    Provides methods to store and retrieve information using Mem0's semantic search.
    """
    
    def __init__(self, client_id: str = "construction_management"):
        """
        Initialize the Mem0 memory system.
        
        Args:
            client_id (str, optional): Client ID for the Mem0 system
        """
        self.client_id = client_id
        self.api_key = os.getenv("MEM0_API_KEY")
        
        if not self.api_key:
            logger.error("Mem0 API key not found in environment variables")
            raise ValueError("Mem0 API key not found. Please set MEM0_API_KEY environment variable.")
        
        # Initialize Mem0 client
        mem0ai.api_key = self.api_key
        
        # Get pre-defined categories from environment variables
        categories_str = os.getenv("MEM0_CATEGORIES", "")
        self.categories = categories_str.split(",") if categories_str else []
        
        logger.info(f"Mem0 memory initialized with client ID: {client_id}")
        logger.info(f"Available categories: {self.categories}")
    
    def add_memory(self, text: str, category: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Add a memory to Mem0.
        
        Args:
            text (str): Text content to store
            category (str, optional): Category for the memory
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            str: Memory ID
        """
        if category and category not in self.categories:
            logger.warning(f"Category '{category}' not in predefined categories: {self.categories}")
        
        if metadata is None:
            metadata = {}
        
        # Add timestamp
        metadata["timestamp"] = int(time.time())
        
        try:
            # Create memory in Mem0
            memory = mem0ai.Memory.create(
                text=text,
                category=category,
                metadata=metadata,
                client_id=self.client_id
            )
            
            logger.info(f"Added memory with ID: {memory.id} in category: {category}")
            return memory.id
        except Exception as e:
            logger.error(f"Error adding memory to Mem0: {str(e)}")
            raise
    
    def bulk_add_memories(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple memories to Mem0 in bulk.
        
        Args:
            items (List[Dict[str, Any]]): List of memory items with text, category, and metadata
            
        Returns:
            List[str]: List of memory IDs
        """
        memory_ids = []
        
        for item in items:
            text = item.get("text", "")
            category = item.get("category")
            metadata = item.get("metadata", {})
            
            memory_id = self.add_memory(text, category, metadata)
            memory_ids.append(memory_id)
        
        return memory_ids
    
    def search_memories(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for memories in Mem0.
        
        Args:
            query (str): Search query
            category (str, optional): Category to search in
            limit (int, optional): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of memory items
        """
        try:
            # Set up search parameters
            search_params = {
                "query": query,
                "limit": limit,
                "client_id": self.client_id
            }
            
            if category:
                search_params["category"] = category
            
            # Search memories in Mem0
            memories = mem0ai.Memory.search(**search_params)
            
            # Format results
            results = []
            for memory in memories:
                results.append({
                    "id": memory.id,
                    "text": memory.text,
                    "category": memory.category,
                    "metadata": memory.metadata,
                    "score": memory.score
                })
            
            logger.info(f"Found {len(results)} memories for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching memories in Mem0: {str(e)}")
            raise
    
    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id (str): Memory ID
            
        Returns:
            Dict[str, Any]: Memory data
        """
        try:
            memory = mem0ai.Memory.get(memory_id)
            
            return {
                "id": memory.id,
                "text": memory.text,
                "category": memory.category,
                "metadata": memory.metadata
            }
        except Exception as e:
            logger.error(f"Error getting memory from Mem0: {str(e)}")
            raise
    
    def update_memory(self, memory_id: str, text: str = None, category: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update a memory in Mem0.
        
        Args:
            memory_id (str): Memory ID
            text (str, optional): New text content
            category (str, optional): New category
            metadata (Dict[str, Any], optional): New metadata
            
        Returns:
            Dict[str, Any]: Updated memory data
        """
        try:
            # Get the memory
            memory = mem0ai.Memory.get(memory_id)
            
            # Update fields if provided
            if text is not None:
                memory.text = text
            
            if category is not None:
                if category not in self.categories:
                    logger.warning(f"Category '{category}' not in predefined categories: {self.categories}")
                memory.category = category
            
            if metadata is not None:
                memory.metadata = metadata
            
            # Save the changes
            memory.save()
            
            logger.info(f"Updated memory with ID: {memory_id}")
            
            return {
                "id": memory.id,
                "text": memory.text,
                "category": memory.category,
                "metadata": memory.metadata
            }
        except Exception as e:
            logger.error(f"Error updating memory in Mem0: {str(e)}")
            raise
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from Mem0.
        
        Args:
            memory_id (str): Memory ID
            
        Returns:
            bool: True if successful
        """
        try:
            memory = mem0ai.Memory.get(memory_id)
            memory.delete()
            
            logger.info(f"Deleted memory with ID: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory from Mem0: {str(e)}")
            raise
    
    def get_memories_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get memories by category.
        
        Args:
            category (str): Category to retrieve
            limit (int, optional): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of memory items
        """
        try:
            # Search with empty query but with category filter
            memories = mem0ai.Memory.search(
                query="",
                category=category,
                limit=limit,
                client_id=self.client_id
            )
            
            # Format results
            results = []
            for memory in memories:
                results.append({
                    "id": memory.id,
                    "text": memory.text,
                    "category": memory.category,
                    "metadata": memory.metadata
                })
            
            logger.info(f"Found {len(results)} memories in category: {category}")
            return results
        except Exception as e:
            logger.error(f"Error getting memories by category from Mem0: {str(e)}")
            raise
    
    def create_category(self, category: str, description: str = "") -> bool:
        """
        Create a new category in Mem0.
        
        Args:
            category (str): Category name
            description (str, optional): Category description
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if category exists
            if category in self.categories:
                logger.info(f"Category '{category}' already exists")
                return True
            
            # Create category in Mem0
            # Note: Mem0 doesn't have explicit category creation, so we'll just
            # add the category to our local list and create a memory with this category
            self.categories.append(category)
            
            # Add a metadata memory for this category
            self.add_memory(
                text=f"Category description: {description}",
                category=category,
                metadata={"is_category_metadata": True, "description": description}
            )
            
            logger.info(f"Created category: {category}")
            return True
        except Exception as e:
            logger.error(f"Error creating category in Mem0: {str(e)}")
            raise
    
    def get_langchain_memory(self, memory_key: str = "chat_history") -> ConversationBufferMemory:
        """
        Get a LangChain memory adapter for Mem0.
        
        Args:
            memory_key (str, optional): Memory key for LangChain
            
        Returns:
            ConversationBufferMemory: LangChain memory object
        """
        # Create a custom LangChain memory adapter
        memory = ConversationBufferMemory(memory_key=memory_key, return_messages=True)
        
        # Monkey patch the memory.save_context method to also save to Mem0
        original_save_context = memory.save_context
        
        def save_context_with_mem0(inputs, outputs):
            # Call the original method
            original_save_context(inputs, outputs)
            
            # Save to Mem0
            input_text = inputs.get("input", "")
            output_text = outputs.get("output", "")
            
            if input_text:
                self.add_memory(
                    text=input_text,
                    category="conversations",
                    metadata={"role": "user", "timestamp": int(time.time())}
                )
            
            if output_text:
                self.add_memory(
                    text=output_text,
                    category="conversations",
                    metadata={"role": "assistant", "timestamp": int(time.time())}
                )
        
        # Replace the method
        memory.save_context = save_context_with_mem0
        
        return memory


class CategoryManager:
    """
    Manager for Mem0 categories for construction management.
    Provides predefined categories for the construction domain.
    """
    
    def __init__(self, mem0_memory: Mem0Memory):
        """
        Initialize the category manager.
        
        Args:
            mem0_memory (Mem0Memory): Mem0 memory instance
        """
        self.mem0 = mem0_memory
        self.initialize_construction_categories()
    
    def initialize_construction_categories(self):
        """
        Initialize predefined categories for construction management.
        """
        # Define construction categories with descriptions
        construction_categories = [
            {
                "name": "projects",
                "description": "Information about construction projects, including timelines, status, and general details."
            },
            {
                "name": "clients",
                "description": "Client information, including contact details, preferences, and communication history."
            },
            {
                "name": "tasks",
                "description": "Construction tasks, to-dos, and action items for different projects."
            },
            {
                "name": "documents",
                "description": "Content and metadata from construction documents, plans, permits, and contracts."
            },
            {
                "name": "conversations",
                "description": "History of conversations with clients, team members, and other stakeholders."
            },
            {
                "name": "compliance",
                "description": "Information about permits, codes, regulations, and compliance requirements."
            },
            {
                "name": "resources",
                "description": "Data about materials, equipment, and labor resources."
            },
            {
                "name": "financial",
                "description": "Financial information, including budgets, expenses, invoices, and cost estimates."
            }
        ]
        
        # Create categories in Mem0
        for category in construction_categories:
            self.mem0.create_category(category["name"], category["description"])
            logger.info(f"Initialized category: {category['name']}")


class ConstructionMemory(BaseModel):
    """
    Standardized structure for construction memories.
    """
    text: str
    category: str
    project_id: Optional[str] = None
    client_id: Optional[str] = None
    document_id: Optional[str] = None
    task_id: Optional[str] = None
    created_at: Optional[int] = None
    created_by: Optional[str] = None
    tags: Optional[List[str]] = []
    additional_metadata: Optional[Dict[str, Any]] = {} 