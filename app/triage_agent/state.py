from typing import Optional, TypedDict, List
from pydantic import BaseModel, Field

class IntakeSchema(BaseModel):
    """Governance check for user input relevance."""
    is_related: bool = Field(description="True if the input is about medical symptoms, hospitals, wait times, or AHS. False otherwise.")
    reasoning: str = Field(description="Brief explanation of why the input was accepted or rejected.")
    symptoms: Optional[str] = Field(None, description="The medical issue or symptoms.")
    address: Optional[str] = Field(None, description="The street address if provided.")
    city: str = Field("Calgary", description="The city. Default to 'Calgary' if ambiguous.")
    province: str = Field("Alberta", description="The province.")
    postal_code: Optional[str] = Field(None, description="The postal code.")

class TriageState(TypedDict):
    raw_user_input: str # The original input from the user, e.g., "I have a fever and a cough, and I live in Calgary."
    user_location: Optional[dict] # The user's location, which we will use to fetch the relevant hospital data
    symptoms: Optional[str] # The symptoms or medical issue described by the user
    is_relevent: Optional[bool] # A flag set by the InputGovernor to indicate if the input is relevant to our task
    
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