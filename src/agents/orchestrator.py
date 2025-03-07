from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_openai import OpenAI
import logging
import os
import time
from typing import List, Dict, Any

# Import specialized agents
from .financial_agent import FinancialAgent
from .project_agent import ProjectAgent
from .document_agent import DocumentAgent
from .client_agent import ClientAgent
from .resource_agent import ResourceAgent
from .compliance_agent import ComplianceAgent
from .analytics_agent import AnalyticsAgent

# Import memory components
from ..memory.mem0_memory import Mem0Memory, CategoryManager
from ..memory.postgres_vector_store import VectorStoreFactory

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Orchestrator Agent that coordinates specialized agents for construction management.
    It analyzes user requests and delegates to appropriate specialized agents.
    """
    
    def __init__(self):
        """
        Initialize the orchestrator agent with specialized agents and memory.
        """
        logger.info("Initializing Orchestrator Agent")
        
        # Initialize Mem0 memory
        self.mem0 = Mem0Memory(client_id="orchestrator")
        
        # Initialize category manager to set up categories
        self.category_manager = CategoryManager(self.mem0)
        
        # Initialize vector store
        self.vector_store = VectorStoreFactory.create_vector_store()
        
        # Initialize the memory for conversation history
        self.memory = self.mem0.get_langchain_memory(memory_key="chat_history")
        
        # Initialize specialized agents
        self.financial_agent = FinancialAgent()
        self.project_agent = ProjectAgent()
        self.document_agent = DocumentAgent()
        self.client_agent = ClientAgent()
        self.resource_agent = ResourceAgent()
        self.compliance_agent = ComplianceAgent()
        self.analytics_agent = AnalyticsAgent()
        
        # Create tools from specialized agents
        self.tools = self._create_tools()
        
        # Initialize the LLM
        self.llm = OpenAI(
            temperature=0,
            model_name="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Initialize the agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=os.getenv("DEBUG", "False").lower() == "true",
        )
        
        logger.info("Orchestrator Agent initialized successfully")
    
    def _create_tools(self) -> List[Tool]:
        """
        Create tools from specialized agents for use by the orchestrator.
        
        Returns:
            List[Tool]: List of tools for the orchestrator agent
        """
        # Tools for specialized agents
        agent_tools = [
            Tool(
                name="Financial Management",
                func=self.financial_agent.run,
                description="Handle financial tasks, invoicing, expense tracking, and budget management"
            ),
            Tool(
                name="Project Management",
                func=self.project_agent.run,
                description="Manage construction projects, tasks, timelines, and resources"
            ),
            Tool(
                name="Document Processing",
                func=self.document_agent.run,
                description="Analyze construction documents, plans, permits, and contracts"
            ),
            Tool(
                name="Client Relations",
                func=self.client_agent.run,
                description="Handle client communications, proposals, and client tracking"
            ),
            Tool(
                name="Resource Management",
                func=self.resource_agent.run,
                description="Manage materials, equipment, and labor scheduling"
            ),
            Tool(
                name="Compliance Management",
                func=self.compliance_agent.run,
                description="Monitor permits, codes, regulations, and safety compliance"
            ),
            Tool(
                name="Analytics and Insights",
                func=self.analytics_agent.run,
                description="Provide performance insights, forecasting, and financial analysis"
            ),
        ]
        
        # Tools for memory search
        memory_tools = [
            Tool(
                name="Search Memory",
                func=self.search_memory,
                description="Search for information in the system's memory"
            ),
            Tool(
                name="Search Documents",
                func=self.search_documents,
                description="Search for information in stored documents"
            )
        ]
        
        return agent_tools + memory_tools
    
    def search_memory(self, query: str) -> str:
        """
        Search for information in Mem0 memory.
        
        Args:
            query (str): Search query
            
        Returns:
            str: Search results in a formatted string
        """
        try:
            # Search all categories
            results = self.mem0.search_memories(query=query, limit=5)
            
            if not results:
                return "No relevant memories found."
            
            # Format results
            response = "Memory search results:\n\n"
            
            for i, result in enumerate(results, 1):
                response += f"{i}. Category: {result['category']}\n"
                response += f"   Content: {result['text']}\n"
                if result['metadata']:
                    response += f"   Metadata: {result['metadata']}\n"
                response += "\n"
            
            return response
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}")
            return f"Error searching memory: {str(e)}"
    
    def search_documents(self, query: str) -> str:
        """
        Search for information in document vector store.
        
        Args:
            query (str): Search query
            
        Returns:
            str: Search results in a formatted string
        """
        try:
            # Search vector store
            results = self.vector_store.similarity_search_with_score(query=query, k=5)
            
            if not results:
                return "No relevant documents found."
            
            # Format results
            response = "Document search results:\n\n"
            
            for i, (doc, score) in enumerate(results, 1):
                response += f"{i}. Relevance: {score:.2f}\n"
                response += f"   Content: {doc.page_content[:200]}...\n"
                if doc.metadata:
                    response += f"   Metadata: {doc.metadata}\n"
                response += "\n"
            
            return response
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return f"Error searching documents: {str(e)}"
    
    def run(self, user_input: str) -> str:
        """
        Process a user query and delegate to appropriate specialized agents.
        
        Args:
            user_input (str): The user's input query
            
        Returns:
            str: The response from the agent system
        """
        logger.info(f"Processing query with orchestrator: {user_input}")
        
        try:
            # Store the user input in Mem0
            self.mem0.add_memory(
                text=user_input,
                category="conversations",
                metadata={"role": "user", "timestamp": int(time.time())}
            )
            
            # Run the agent
            response = self.agent.run(user_input)
            
            # Store the response in Mem0
            self.mem0.add_memory(
                text=response,
                category="conversations",
                metadata={"role": "assistant", "timestamp": int(time.time())}
            )
            
            logger.info(f"Received response from orchestrator")
            return response
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            return f"I encountered an error processing your request: {str(e)}" 