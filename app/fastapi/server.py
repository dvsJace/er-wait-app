from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import your compiled LangGraph agent
from app.graph import triage_agent

# Initialize the API
app = FastAPI(title="AHS Triage Agent API")

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
def chat_with_triage_agent(request: ChatRequest):
    """
    The main endpoint your frontend chat box will hit.
    """
    try:
        print(f"Received message: {request.message}")
        
        # 1. Set the initial state exactly how LangGraph expects it
        initial_state = {
            "raw_user_input": request.message
        }
        
        # 2. Invoke the agent. This blocks until the entire graph finishes running.
        final_state = triage_agent.invoke(initial_state)
        
        # 3. Format the response for your frontend
        return ChatResponse(
            response=final_state.get("recommendations", "I couldn't process that request."),
            hospitals_checked=final_state.get("hospital_data", []),
            extracted_location=final_state.get("user_location", {})
        )
        
    except Exception as e:
        print(f"Error executing agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing triage request.")