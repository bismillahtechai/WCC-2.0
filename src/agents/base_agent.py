from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..memory.mem0_memory import Mem0Memory

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base agent class that all specialized agents will inherit from.
    Provides common functionality for agent creation and execution.
    """
    
    def __init__(
        self, 
        name: str, 
        description: str,
        memory_store: Optional[ConversationBufferMemory] = None
    ):
        """
        Initialize the base agent with a name, description, and memory store.
        
        Args:
            name (str): The name of the agent
            description (str): Description of the agent's specialization
            memory_store (Optional[ConversationBufferMemory]): Memory store for agent
        """
        self.name = name
        self.description = description
        
        # Initialize Mem0 memory
        self.mem0 = Mem0Memory(client_id=f"agent_{name.lower().replace(' ', '_')}")
        
        # Initialize memory if not provided
        if memory_store is None:
            self.memory = self.mem0.get_langchain_memory(memory_key="history")
        else:
            self.memory = memory_store
            
        # Initialize tools
        self.tools = self._get_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
        
        logger.info(f"{name} Agent initialized")
    
    @abstractmethod
    def _get_tools(self) -> List[Tool]:
        """
        Get the tools for this specialized agent.
        Must be implemented by subclasses.
        
        Returns:
            List[Tool]: List of tools for the agent
        """
        pass
    
    def _create_agent(self) -> AgentExecutor:
        """
        Create the agent executor with tools and memory.
        
        Returns:
            AgentExecutor: The agent executor
        """
        # Initialize LLM
        llm = OpenAI(
            temperature=0.1,
            model_name="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["input", "history", "agent_scratchpad"],
            template=f"""
            You are the {self.name} agent specializing in {self.description}.
            You are an expert in your domain and provide detailed, accurate information.
            
            User History: {{history}}
            New User Input: {{input}}
            {{agent_scratchpad}}
            
            Provide your response in a clear, professional manner.
            """
        )
        
        # Create LLM chain
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        
        # Create agent
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            allowed_tools=[tool.name for tool in self.tools],
            verbose=os.getenv("DEBUG", "False").lower() == "true"
        )
        
        # Create agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=os.getenv("DEBUG", "False").lower() == "true",
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def run(self, user_input: str) -> str:
        """
        Run the agent with the user input.
        
        Args:
            user_input (str): The user's input query
            
        Returns:
            str: The response from the agent
        """
        logger.info(f"Running {self.name} agent with input: {user_input}")
        
        try:
            # Add input to Mem0 memory
            self.mem0.add_memory(
                text=user_input,
                category="conversations",
                metadata={"agent": self.name, "role": "user"}
            )
            
            response = self.agent_executor.run(user_input)
            
            # Add response to Mem0 memory
            self.mem0.add_memory(
                text=response,
                category="conversations",
                metadata={"agent": self.name, "role": "assistant"}
            )
            
            logger.info(f"Response from {self.name} agent: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in {self.name} agent: {str(e)}")
            return f"Error in {self.name} agent: {str(e)}"
    
    def search_memory(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the agent's memory.
        
        Args:
            query (str): Search query
            category (str, optional): Category to search in
            limit (int, optional): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of memory items
        """
        return self.mem0.search_memories(query, category, limit) 