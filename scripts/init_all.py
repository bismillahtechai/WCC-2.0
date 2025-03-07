#!/usr/bin/env python
"""
Script to run all initialization scripts for the construction management system.
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run_script(script_path):
    """
    Run a Python script and return the result.
    
    Args:
        script_path (str): Path to the script
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Running script: {script_path}")
        result = subprocess.run([sys.executable, script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running script {script_path}: {str(e)}")
        return False

def main():
    """
    Run all initialization scripts.
    """
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define scripts to run
    scripts = [
        os.path.join(script_dir, "init_postgres.py"),
        os.path.join(script_dir, "init_mem0.py"),
    ]
    
    # Run each script
    success = True
    for script in scripts:
        if not run_script(script):
            success = False
            logger.error(f"Failed to run script: {script}")
    
    return success

if __name__ == "__main__":
    logger.info("Running all initialization scripts...")
    success = main()
    if success:
        logger.info("All initialization scripts completed successfully")
        sys.exit(0)
    else:
        logger.error("One or more initialization scripts failed")
        sys.exit(1) 