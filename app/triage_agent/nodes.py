import logging

from app.triage_agent.model import get_llm
from app.triage_agent.state import TriageState, IntakeSchema

from build.lib.triage_agent.utils.fetch import fetch_ahs_wait_data

# Configure structured logging
_name = "triage_agent.nodes"
logger = logging.getLogger(_name) 
logger.setLevel(logging.INFO)

def parse_user_input_node(state: TriageState):
    logger.info("--- NODE: Parsing User Intake ---")
    raw_text = state.get("raw_user_input")
    
    # Initialize the LLM and bind your schema
    structured_llm = get_llm().with_structured_output(IntakeSchema)
    
    # Extract the data
    extracted_data = structured_llm.invoke(raw_text)
    
    logger.info(f"Parsed City: {extracted_data.city}")
    logger.info(f"Parsed Symptoms: {extracted_data.symptoms}")
    
    # Update the state. We convert the Pydantic model to a dict for safe state passing
    return {
        "user_location": extracted_data.model_dump(exclude={'symptoms'}), 
        "symptoms": extracted_data.symptoms
    }

def fetch_wait_times(state: TriageState):
    logger.info("--- NODE: Fetching AHS Data ---")
    
    # Safely get the city out of the state dict, defaulting to Calgary just in case
    location_data = state.get("user_location", {})
    target_city = location_data.get("city", "Calgary")
    
    # Call your Playwright function here
    scraped_data = fetch_ahs_wait_data(target_city)
    logger.info(f"Fetched {len(scraped_data)} hospital entries for city: {target_city}")

    return {"hospital_data": scraped_data}


def categorize_hospitals(state: TriageState):
    llm = get_llm()
    
    prompt = f"""
    User Location: {state['user_location']}
    Symptoms: {state['symptoms']}
    Hospital Data: {state['hospital_data']}
    
    Rank these hospitals. Consider:
    1. Total Time = (Drive time from user) + (Wait time).
    2. Appropriateness: If it's a child, prefer Stollery. 
    """
    
    response = llm.invoke(prompt)
    return {"recommendations": response.content}


