import logging

from app.triage_agent.model import get_llm
from app.triage_agent.state import TriageState, IntakeSchema

from app.triage_agent.utils.fetch import fetch_ahs_wait_data

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
    logger.info("--- NODE: Categorizing Hospitals ---")
    
    symptoms = state.get("symptoms", "Unknown issue")
    hospital_data = state.get("hospital_data", [])
    
    # We want a bit of reasoning ability here, so a slightly higher temperature is good
    llm = get_llm(temperature=0.2)
    
    # We use a system prompt to guide the LLM on how to interpret the data
    prompt = f"""
    You are an empathetic, efficient medical triage assistant for Alberta Health Services.
    
    The user has reported the following medical issue/symptoms: "{symptoms}"
    
    Here is the live wait time data for hospitals in their area:
    {hospital_data}
    
    TASK:
    1. Acknowledge their symptoms empathetically but briefly.
    2. Recommend the best facility for them to visit based on the shortest wait time.
    3. CRITICAL: If their symptoms sound minor (e.g., sprain, minor cut, cough), explicitly check if an "Urgent Care" or "Community Health Centre" is in the data list and recommend that over an Emergency Room.
    4. Always include a standard medical disclaimer to call 911 if it is a life-threatening emergency.
    
    Format your response cleanly using Markdown (bolding, bullet points) so it is easy to read on a mobile device.
    """
    
    # Call Gemini with the constructed prompt
    response = llm.invoke(prompt)
    
    # Save the AI's response to the final state variable
    return {"recommendations": response.content}


