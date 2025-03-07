#!/usr/bin/env python
"""
Script to initialize PostgreSQL database with pgvector extension.
This script should be run once before starting the application.
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_postgres():
    """
    Initialize PostgreSQL database with pgvector extension.
    """
    # Get PostgreSQL connection information
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    database = os.getenv("POSTGRES_DB", "construction_management")
    
    # Connect to PostgreSQL
    try:
        # First connect to default 'postgres' database to create our database if it doesn't exist
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database}'")
        if not cursor.fetchone():
            # Create database
            cursor.execute(f"CREATE DATABASE {database}")
            logger.info(f"Created database: {database}")
        else:
            logger.info(f"Database already exists: {database}")
        
        # Close connection to postgres database
        cursor.close()
        conn.close()
        
        # Connect to our database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if pgvector extension exists
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        if not cursor.fetchone():
            # Create pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("Created pgvector extension")
        else:
            logger.info("pgvector extension already exists")
        
        # Close connection
        cursor.close()
        conn.close()
        
        logger.info("PostgreSQL initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing PostgreSQL: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Initializing PostgreSQL database...")
    success = init_postgres()
    if success:
        logger.info("PostgreSQL initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("PostgreSQL initialization failed")
        sys.exit(1) 