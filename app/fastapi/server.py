from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

load_dotenv()  # Load environment variables from .env file

# Import your compiled LangGraph agent
from app.ahs_scraper.scheduler import start_scheduler
from app.sqlite_db import init_db
from app.triage_agent.graph import graph as triage_agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:     %(name)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize the API
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the Docker container starts
    init_db()
    from app.ahs_scraper.scheduler import scrape_job
    await scrape_job() # Initial scrape on startup
    scheduler = start_scheduler()
    yield
    # Code here runs when the container shuts down (optional)
    scheduler.shutdown()

app = FastAPI(title="AHS Triage Agent API", lifespan=lifespan)

# --- CORS Configuration ---
# This is REQUIRED if your frontend is running on a different port (e.g., localhost:3000 for React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change "*" to your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    hospitals_checked: Optional[list] = None
    extracted_location: Optional[dict] = None


# --- API Routes ---
@app.get("/health")
def health_check():
    """Simple endpoint to verify the server is running."""
    return {"status": "healthy", "agent": "ready"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_triage_agent(request: ChatRequest):
    """
    The main endpoint the frontend chat box will hit.
    """
    try:
        logger.info(f"Received message: {request.message}")
        
        # 1. Set the initial state exactly how LangGraph expects it
        initial_state = {
            "raw_user_input": request.message
        }
        
        # 2. Invoke the agent. This blocks until the entire graph finishes running.
        final_state = await triage_agent.ainvoke(initial_state)
        logger.info(f"Final state after agent execution: {final_state}")
        # 3. Format the response for your frontend
        return ChatResponse(
            response=final_state.get("recommendations", "I couldn't process that request."),
            hospitals_checked=final_state.get("hospital_data", []),
            extracted_location=final_state.get("user_location", {})
        )
        
    except Exception as e:
        logger.critical(f"Error executing agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing triage request.")