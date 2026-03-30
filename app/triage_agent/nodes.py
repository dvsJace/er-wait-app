import logging

from triage_agent.state import IntakeSchema, TriageState
from langchain_google_genai import ChatGoogleGenerativeAI

from build.lib.triage_agent.utils.fetch import fetch_wait_times_from_dropdown

# Configure structured logging
_name = "triage_agent.nodes"
logger = logging.getLogger(_name) 
logger.setLevel(logging.INFO)

def parse_user_input_node(state: TriageState):
    print("--- NODE: Parsing User Intake ---")
    raw_text = state.get("raw_user_input")
    
    # Initialize the LLM and bind your schema
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(IntakeSchema)
    
    # Extract the data
    extracted_data = structured_llm.invoke(raw_text)
    
    print(f"Parsed City: {extracted_data.city}")
    print(f"Parsed Symptoms: {extracted_data.symptoms}")
    
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
    scraped_data = fetch_wait_times_from_dropdown(target_city)
    
    # Mocking the response for the example
    scraped_data = [{"name": "South Health Campus", "wait": "3h 15m"}] 
    
    return {"hospital_data": scraped_data}


def categorize_hospitals(state: TriageState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    
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


