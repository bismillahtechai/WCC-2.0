#!/usr/bin/env python3
"""
Script to initialize pgvector extension in a PostgreSQL database.
Can be run directly after setting up a database on Render.
"""

import os
import sys
import time
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def initialize_pgvector(connection_string=None, max_retries=5, retry_delay=5):
    """Initialize pgvector extension in the database with retry logic."""
    
    # Get connection string from environment or parameter
    if not connection_string:
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            logger.error("No DATABASE_URL provided. Please set the DATABASE_URL environment variable or provide a connection string.")
            sys.exit(1)
    
    logger.info(f"Attempting to initialize pgvector extension (max {max_retries} attempts)")
    
    for attempt in range(max_retries):
        try:
            # Connect to the database
            logger.info(f"Connecting to database (attempt {attempt + 1}/{max_retries})")
            conn = psycopg2.connect(connection_string)
            conn.autocommit = True
            
            # Create a cursor
            with conn.cursor() as cur:
                # Check if pgvector extension exists
                logger.info("Checking for pgvector extension")
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if cur.fetchone():
                    logger.info("pgvector extension already exists")
                else:
                    # Create pgvector extension
                    logger.info("Creating pgvector extension")
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    logger.info("pgvector extension created successfully")
            
            # Close the connection
            conn.close()
            logger.info("Database connection closed")
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All attempts to initialize pgvector failed")
                return False

if __name__ == "__main__":
    # Get connection string from command line if provided
    connection_string = sys.argv[1] if len(sys.argv) > 1 else None
    
    if initialize_pgvector(connection_string):
        logger.info("pgvector initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("pgvector initialization failed")
        sys.exit(1) 