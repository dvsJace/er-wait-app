from typing import TypedDict, List

class TriageState(TypedDict):
    # The user's input
    user_location: str
    symptoms: str
    
    # The data we fetch
    hospital_data: List[dict] # Wait times, addresses, etc.
    
    # The final output
    recommendations: str