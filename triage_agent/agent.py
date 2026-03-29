from triage_agent.state import TriageState
from langchain_google_genai import ChatGoogleGenerativeAI

def fetch_wait_times(state: TriageState):
    # In a real app, you'd scrape https://www.albertahealthservices.ca/waittimes/waittimes.aspx
    hospitals = [
        {"name": "Royal Alexandra", "wait": "3h 58m", "address": "10240 Kingsway Ave"},
        {"name": "Grey Nuns", "wait": "7h 15m", "address": "1100 Youville Dr W"},
        {"name": "Sturgeon Community", "wait": "6h 34m", "address": "201 Boudreau Rd"}
    ]
    return {"hospital_data": hospitals}

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


