#!/usr/bin/env python
"""
Script to initialize Mem0 categories for construction management.
This script should be run once before starting the application.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Mem0 components
from src.memory.mem0_memory import Mem0Memory, CategoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_mem0():
    """
    Initialize Mem0 categories for construction management.
    """
    try:
        # Initialize Mem0 memory
        mem0 = Mem0Memory(client_id="construction_management")
        
        # Initialize category manager
        category_manager = CategoryManager(mem0)
        
        # Initialize construction categories
        category_manager.initialize_construction_categories()
        
        logger.info("Mem0 categories initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing Mem0 categories: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Initializing Mem0 categories...")
    success = init_mem0()
    if success:
        logger.info("Mem0 initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("Mem0 initialization failed")
        sys.exit(1) 