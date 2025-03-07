from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import agent orchestrator
from agents.orchestrator import OrchestratorAgent

app = FastAPI(
    title="Construction Management AI",
    description="Multi-agent system for construction business management",
    version="1.0.0",
)

# Initialize the orchestrator agent
orchestrator = OrchestratorAgent()

class Query(BaseModel):
    user_input: str


@app.post("/query")
async def process_query(query: Query):
    """
    Process a user query and return a response from the agent system.
    """
    try:
        logger.info(f"Received query: {query.user_input}")
        response = orchestrator.run(query.user_input)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy"}


@app.get("/")
async def root():
    """
    Root endpoint with basic information about the API.
    """
    return {
        "message": "Construction Management AI API",
        "documentation": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 