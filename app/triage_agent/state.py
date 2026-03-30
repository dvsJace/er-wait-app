from typing import Optional, TypedDict, List
from triage_agent.utils.fetch import HospitalData
from pydantic import BaseModel, Field

class IntakeSchema(BaseModel):
    address: str = Field(default="", description="The street address.")
    city: str = Field(description="The city. Default to 'Calgary' if ambiguous.")
    province: str = Field(default="Alberta", description="The province.")
    postal_code: str = Field(default="", description="The postal code.")
    symptoms: str = Field(description="The medical issue or symptoms.")

class TriageState(TypedDict):
    raw_user_input: str # The original input from the user, e.g., "I have a fever and a cough, and I live in Calgary."
    user_location: Optional[dict] # The user's location, which we will use to fetch the relevant hospital data
    symptoms: Optional[str] # The symptoms or medical issue described by the user
    
    # The data we fetch
    hospital_data: List[dict] # Wait times, addresses, etc.
    
    # The final output
    recommendations: str

class Location:
    """Simple class to represent a location with city and province."""
    address: str
    city: str
    province: str
    postal_code: str
    def __init__(self, city: str, province: str, address: str = "", postal_code: str = ""):
        self.city = city
        self.province = province
        self.postal_code = postal_code
        self.address = address