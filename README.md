# Multi-Agent Construction Management System

A sophisticated multi-agent system for construction business management that orchestrates specialized agents, each handling distinct functions while accessing shared data and seamlessly integrating with ClickUp.

## System Architecture

### 1. Multi-Agent Framework

- **Orchestrator Agent**: Central coordinator receiving commands, analyzing requests, delegating to specialized agents, and presenting unified responses.
- **Specialized Agents**:
  - **Financial Agent**: Handles invoicing, expense tracking, budget management
  - **Project Management Agent**: Manages tasks, timelines, resources, critical paths
  - **Document Processing Agent**: Analyzes plans, permits, contracts
  - **Client Relations Agent**: Handles communications, proposals, client tracking
  - **Resource Agent**: Manages materials, equipment, labor scheduling
  - **Compliance Agent**: Monitors permits, codes, regulations
  - **Analytics Agent**: Provides performance insights, forecasting, financial analysis

### 2. Shared Infrastructure

- **Persistent Memory**: 
  - **Mem0**: Intelligent memory layer for personalized AI interactions with custom categories
  - **PostgreSQL with pgvector**: Vector database for semantic search of documents and data
- **Data Pipeline**: Ingests and processes documents from multiple sources
- **Vector Storage**: Stores embedded representations of documents for semantic search

### 3. Integration Components

- **ClickUp Integration**: Bidirectional data flow for task, project, and resource management
- **Document Processing**: OCR capabilities and image analysis for construction documents

## Setup & Installation

### Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- ClickUp account with API access
- Mem0 API key (optional, for managed service)

### Installation Steps

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your API keys (see `.env.example`)
6. Initialize PostgreSQL database: `python scripts/init_postgres.py`
7. Run the application: `uvicorn src.main:app --reload`

## Memory System

The system uses two complementary memory systems:

### Mem0 Memory

Mem0 provides an intelligent memory layer with custom categories for construction-specific data:

- **Projects**: Information about construction projects
- **Clients**: Client information and preferences
- **Tasks**: Construction tasks and action items
- **Documents**: Content from construction documents
- **Conversations**: History of conversations
- **Compliance**: Permits, codes, and regulations
- **Resources**: Materials, equipment, and labor
- **Financial**: Budgets, expenses, and invoices

### PostgreSQL Vector Store

PostgreSQL with pgvector extension provides vector storage for semantic search:

- Stores document embeddings for semantic similarity search
- Enables natural language queries over construction documents
- Scales efficiently for large document collections

## Project Structure

```
construction-agent-system/
├── config/                 # Configuration files
├── data/                   # Data storage
│   └── vectorstore/        # Vector store data
├── docs/                   # Documentation
├── scripts/                # Utility scripts
│   └── init_postgres.py    # PostgreSQL initialization script
├── src/                    # Source code
│   ├── agents/             # Agent implementations
│   ├── integrations/       # External integrations (ClickUp, etc.)
│   ├── memory/             # Vector storage and memory components
│   └── utils/              # Utility functions
├── .env.example            # Example environment variables
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## Usage

The system provides a REST API for interaction:

```
POST /query
{
  "user_input": "Create a new project called 'Smith Residence' with a budget of $250,000"
}
```

The orchestrator agent will process the request, delegate to appropriate specialized agents, and return a unified response.

## Docker Deployment

You can also run the system using Docker:

```
docker-compose up -d
```

This will start the API server and PostgreSQL database with pgvector extension. 

## Render Deployment

This project is configured for deployment on Render using both development and production environments. The `render.yaml` blueprint file defines both environments with appropriate resources.

### Prerequisites for Render Deployment

1. A Render account
2. OpenAI API key
3. ClickUp API key (if using ClickUp integration)
4. Mem0 API key (if using Mem0 memory service)

### Automatic Deployment with Blueprint

1. Fork or push this repository to GitHub
2. In Render dashboard, click "New Blueprint"
3. Select your repository and click "Apply"
4. Render will automatically create the specified services and databases
5. After databases are created, run the pgvector initialization script:
   ```
   python scripts/init_pgvector.py
   ```

### Manual Deployment Steps

If you prefer manual setup:

1. **Create PostgreSQL Database**
   - In Render dashboard, go to "New" > "PostgreSQL"
   - Configure your database (name, region, etc.)
   - Choose PostgreSQL 15 or higher
   - After creation, note the connection details

2. **Initialize pgvector Extension**
   - Connect to the database using the provided PSQL command
   - Run: `CREATE EXTENSION IF NOT EXISTS vector;`
   - Alternatively, use the script: `python scripts/init_pgvector.py DATABASE_URL`

3. **Deploy Web Service**
   - In Render dashboard, go to "New" > "Web Service"
   - Connect your repository
   - Select "Docker" for environment
   - Set the following environment variables:
     - `DATABASE_URL`: Your PostgreSQL connection string
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `CLICKUP_API_KEY`: Your ClickUp API key
     - `MEM0_API_KEY`: Your Mem0 API key
     - `MEM0_CATEGORIES`: projects,clients,tasks,documents,conversations,compliance,resources,financial

### Development vs. Production

The blueprint configures two environments:

- **Development (wcc-dev)**
  - Free tier resources
  - Debug logging
  - Single instance
  - Tied to 'develop' branch

- **Production (wcc-prod)**
  - Standard tier resources
  - Multiple instances for redundancy
  - Normal logging level
  - Tied to 'main' branch

### Checking Deployment Status

1. Monitor build logs in the Render dashboard
2. Once deployed, visit the web service URL
3. Check the `/health` endpoint for service status

### Troubleshooting

If your service fails to start:

1. Check logs in the Render dashboard
2. Ensure pgvector extension is enabled
3. Verify all required environment variables are set
4. Check if the database is accessible from the web service 